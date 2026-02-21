"""
APO v2 — Tier 2: Interaction Agent (Claude-Guided)
====================================================
Claude acts as the session strategist:
  - Decides WHICH pages to visit based on risk scores from Tier 1
  - Decides WHAT actions to take on each page (click, fill, scroll)
  - Flags real-time observations during the session

Runs both sessions in PARALLEL using asyncio.gather.
Tier 3 (Observability) receives traffic + Claude's session notes.

Saves:
  output/traffic_baseline.json
  output/traffic_compliance.json
  output/session_state_baseline.json
  output/session_state_compliance.json
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import (
    GPC_HEADER_KEY, GPC_HEADER_VALUE, GPC_JS_SCRIPT,
    ACTION_DELAY_MS, MAX_JOURNEYS, SCROLL_STEPS,
    TRAFFIC_BASELINE_FILE, TRAFFIC_COMPLIANCE_FILE,
    SESSION_BASELINE_FILE, SESSION_COMPLIANCE_FILE,
)
from core.tools import (
    navigate_to_page, scroll_page, make_traffic_listener,
    save_session_state, detect_cookie_banner,
    detect_do_not_sell_link, detect_temporal_leak
)
from core.llm_router import call_llm


# ═══════════════════════════════════════════════════════════════
# Claude tool — session action decision
# ═══════════════════════════════════════════════════════════════

SESSION_TOOLS = [
    {
        "name": "decide_session_actions",
        "description": "Decide which pages to prioritize and what actions to perform in this browser session",
        "input_schema": {
            "type": "object",
            "properties": {
                "pages_to_visit": {
                    "type": "array",
                    "description": "Ordered list of page URLs to visit in this session (most important first)",
                    "items": {"type": "string"}
                },
                "observations": {
                    "type": "array",
                    "description": "Privacy observations about the interaction graph",
                    "items": {"type": "string"}
                },
                "high_risk_pages": {
                    "type": "array",
                    "description": "Pages Claude considers critical for GPC compliance testing",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url":    {"type": "string"},
                            "reason": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["pages_to_visit", "observations"]
        }
    }
]

SESSION_SYSTEM = """You are the Session Strategist for an Autonomous Privacy Observability (APO) system.

Given an interaction graph of a website (nodes with risk scores), you must decide:
1. Which pages to visit during the compliance test session (up to MAX_JOURNEYS pages)
2. Which pages are most critical for detecting GPC non-compliance

Prioritize:
- Pages with HIGH privacy_risk_score (7-10)
- Pages with tracker_scripts present
- Pages with forms sending to third parties
- Privacy policy and cookie settings pages
- Pages missing Do Not Sell links

Always include the homepage and privacy policy page.
Use the decide_session_actions tool to return your decision."""


def _plan_session_with_claude(nodes: list, max_visits: int) -> dict:
    """
    LLM reviews the interaction graph and decides
    which pages to focus on in the session (Claude → GPT-4o fallback).
    """
    node_summaries = [
        {
            "url":         n["value"],
            "purpose":     n.get("page_purpose", "unknown"),
            "risk_score":  n.get("privacy_risk_score", 5),
            "has_trackers":bool(n.get("tracker_scripts")),
            "has_dns_link":n.get("has_dns_text", False),
            "has_forms":   bool(n.get("forms")),
        }
        for n in nodes[:50]
    ]

    result = call_llm(
        prompt=(
            f"Here is the interaction graph ({len(nodes)} pages).\n"
            f"Select up to {max_visits} pages to visit for GPC compliance testing.\n\n"
            f"Graph:\n{json.dumps(node_summaries, indent=2)}"
        ),
        tools=SESSION_TOOLS,
        system=SESSION_SYSTEM,
        max_tokens=1024
    )

    if result["tool_result"]:
        return result["tool_result"]

    # Fallback: sort by risk score
    sorted_nodes = sorted(nodes, key=lambda n: -n.get("privacy_risk_score", 0))
    return {
        "pages_to_visit": [n["value"] for n in sorted_nodes[:max_visits]],
        "observations":   ["Fallback: sorted by risk score (no LLM available)"],
        "high_risk_pages":[]
    }


# ═══════════════════════════════════════════════════════════════
# Per-page Claude observation (lightweight, Claude Haiku ideal)
# ═══════════════════════════════════════════════════════════════

def _observe_page_with_claude(url: str, banner: dict,
                               dns: dict, trackers_fired: list,
                               gpc_on: bool) -> str:
    """
    Quick single-sentence observation from LLM after visiting a page.
    Uses call_llm router (Claude → GPT-4o fallback).
    """
    prompt = (
        f"Page: {url}\n"
        f"GPC active: {gpc_on}\n"
        f"Cookie banner detected: {banner.get('banner_detected')}\n"
        f"Do Not Sell link found: {dns.get('link_found')}\n"
        f"Trackers fired: {trackers_fired[:5]}\n\n"
        "In one sentence, state the key privacy compliance observation for this page."
    )
    try:
        result = call_llm(prompt=prompt, max_tokens=100)
        return result.get("text", "").strip()
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════
# Single session runner
# ═══════════════════════════════════════════════════════════════

async def _run_session(browser: Browser, ordered_urls: list,
                       gpc_on: bool, claude_plan: dict) -> dict:
    """
    Runs one complete session over Claude's prioritized URL list.
    """
    label   = "compliance" if gpc_on else "baseline"
    icon    = "🔒" if gpc_on else "🌐"
    headers = {GPC_HEADER_KEY: GPC_HEADER_VALUE} if gpc_on else {}

    print(f"\n  {icon} {label.upper()} session starting ({len(ordered_urls)} pages planned)")

    context = await browser.new_context(
        ignore_https_errors=True,
        extra_http_headers=headers,
        viewport={"width": 1280, "height": 800},
    )
    if gpc_on:
        await context.add_init_script(GPC_JS_SCRIPT)

    page = await context.new_page()

    traffic_log, on_request = make_traffic_listener(label)
    page.on("request", on_request)

    banner_results   = {}
    dns_link_results = {}
    temporal_leaks   = []
    page_observations= {}
    pages_visited    = 0

    traffic_file = TRAFFIC_COMPLIANCE_FILE if gpc_on else TRAFFIC_BASELINE_FILE
    session_file = SESSION_COMPLIANCE_FILE if gpc_on else SESSION_BASELINE_FILE

    for url in ordered_urls:
        if not url.startswith("http"):
            continue

        print(f"    [{label}] ▶ {url[:65]}")

        pre_count    = len(traffic_log)
        page_load_ts = int(time.time() * 1000)

        nav = await navigate_to_page(page, url)
        if nav["status"] != "ok":
            print(f"      ⚠ {nav.get('msg','error')[:50]}")
            continue

        await scroll_page(page, steps=SCROLL_STEPS)

        # Per-page checks
        banner = await detect_cookie_banner(page)
        dns    = await detect_do_not_sell_link(page)
        banner_results[url]   = banner
        dns_link_results[url] = dns

        # Temporal leak (compliance only)
        if gpc_on:
            new_reqs = traffic_log[pre_count:]
            leaks = detect_temporal_leak(new_reqs, page_load_ts)
            if leaks:
                temporal_leaks.extend([{**l, "page": url} for l in leaks])
                print(f"      ⚠ Temporal leak: {len(leaks)} tracker(s) in <500ms")

        # Trackers that fired on this page
        trackers_on_page = [
            r["domain"] for r in traffic_log[pre_count:]
            if r.get("is_tracker")
        ]

        # Claude quick observation (compliance session only to save cost)
        if gpc_on and trackers_on_page:
            obs = _observe_page_with_claude(
                url, banner, dns, trackers_on_page, gpc_on
            )
            if obs:
                page_observations[url] = obs
                print(f"      Claude: {obs[:80]}")

        pages_visited += 1

    await save_session_state(page, session_file)
    traffic_file.write_text(json.dumps(traffic_log, indent=2))
    await context.close()

    tracker_hits = [r for r in traffic_log if r.get("is_tracker")]
    print(f"\n  {icon} {label.upper()} done — "
          f"{pages_visited} pages, {len(traffic_log)} requests, "
          f"{len(tracker_hits)} tracker hits, "
          f"{len(temporal_leaks)} temporal leaks")

    return {
        "label":             label,
        "gpc_on":            gpc_on,
        "traffic_log":       traffic_log,
        "banner_results":    banner_results,
        "dns_link_results":  dns_link_results,
        "temporal_leaks":    temporal_leaks,
        "page_observations": page_observations,
        "pages_visited":     pages_visited,
        "claude_session_plan": claude_plan,
    }


# ═══════════════════════════════════════════════════════════════
# Main — Claude plans then BOTH sessions run in parallel
# ═══════════════════════════════════════════════════════════════

async def run_interaction_agent(graph: dict) -> dict:
    print("\n" + "═"*60)
    print("  Tier 2 — Interaction Agent (Claude-Guided, Parallel)")
    print("═"*60)

    nodes = graph["interaction_graph"]["nodes"]
    print(f"  Graph: {len(nodes)} nodes")

    # ── Claude plans the session ───────────────────────────────
    print("\n  Claude planning session strategy...")
    plan = _plan_session_with_claude(nodes, MAX_JOURNEYS)
    ordered_urls = plan.get("pages_to_visit", [n["value"] for n in nodes[:MAX_JOURNEYS]])

    print(f"  Claude selected {len(ordered_urls)} pages to visit")
    if plan.get("observations"):
        for obs in plan["observations"][:3]:
            print(f"    • {obs}")
    if plan.get("high_risk_pages"):
        print(f"  High-risk pages flagged by Claude:")
        for p in plan["high_risk_pages"][:3]:
            print(f"    🔴 {p.get('url','')[:55]} — {p.get('reason','')[:40]}")

    start_time = time.time()

    # ── Launch parallel sessions ───────────────────────────────
    async with async_playwright() as pw:
        browser1 = await pw.chromium.launch(headless=True)
        browser2 = await pw.chromium.launch(headless=True)

        baseline_result, compliance_result = await asyncio.gather(
            _run_session(browser1, ordered_urls, gpc_on=False, claude_plan=plan),
            _run_session(browser2, ordered_urls, gpc_on=True,  claude_plan=plan),
        )

        await browser1.close()
        await browser2.close()

    elapsed = time.time() - start_time
    print(f"\n  Both sessions completed in {elapsed:.1f}s (parallel)")

    return {
        "baseline":        baseline_result,
        "compliance":      compliance_result,
        "elapsed_seconds": round(elapsed, 1),
        "claude_plan":     plan,
    }


if __name__ == "__main__":
    graph_path = os.path.join(
        os.path.dirname(__file__), "..", "output", "interaction_graph.json"
    )
    with open(graph_path) as f:
        graph = json.load(f)
    asyncio.run(run_interaction_agent(graph))
