"""
APO v2 — Tier 1: Discovery Agent (Agentic, Claude-Powered)
============================================================
Claude acts as the brain using Anthropic's tool_use API.
It decides what to crawl next, scores each page for privacy risk,
and builds a prioritized interaction graph.

Tools available to Claude:
  1. navigate_and_extract  — loads a URL, returns clean structured page data
  2. mark_visited          — marks a URL as done in the graph
  3. add_to_queue          — adds a priority URL to the crawl queue
  4. save_graph            — saves the final graph to output/

Claude's job per page:
  - What links/buttons/forms are here?
  - Which paths are privacy-relevant? (checkout, contact, privacy policy)
  - What is the privacy risk score of this page?
  - What should the agent visit next?

Saves: output/interaction_graph.json
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from urllib.parse import urlparse
from playwright.async_api import async_playwright, Page

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import core.config as _cfg
from core.tools import navigate_to_page, scroll_page
from core.llm_router import call_llm


# ═══════════════════════════════════════════════════════════════
# Browser helper — extracts clean structured data from a page
# ═══════════════════════════════════════════════════════════════

def _same_domain(url: str) -> bool:
    try:
        return urlparse(url).netloc == urlparse(_cfg.ROOT_URL).netloc
    except Exception:
        return False


def _clean_url(url: str) -> str:
    return url.split("#")[0].rstrip("/")


async def _extract_page_data(page: Page, url: str) -> dict:
    """Extract compact structured data from rendered page (sent to Claude)."""
    await scroll_page(page, steps=_cfg.SCROLL_STEPS)

    links = await page.evaluate("""() =>
        Array.from(document.querySelectorAll('a[href]'))
            .map(a => ({href: a.href, text: (a.innerText||'').trim().slice(0,60)}))
            .filter(a => a.href.startsWith('http'))
            .slice(0, 40)
    """)

    buttons = await page.evaluate("""() =>
        Array.from(document.querySelectorAll('button,[role="button"],input[type="submit"]'))
            .map(b => ({
                text: (b.innerText||b.value||b.getAttribute('aria-label')||'').trim().slice(0,60),
                id: b.id || '',
                cls: (b.className||'').split(' ')[0]
            }))
            .filter(b => b.text.length > 0)
            .slice(0, 20)
    """)

    forms = await page.evaluate("""() =>
        Array.from(document.querySelectorAll('form'))
            .map(f => ({
                action: f.action || '',
                method: f.method || 'get',
                fields: Array.from(f.querySelectorAll('input,textarea'))
                    .map(i => i.name || i.type || '')
                    .filter(Boolean).slice(0, 8)
            }))
            .slice(0, 5)
    """)

    tracker_scripts = await page.evaluate("""(trackers) => {
        return Array.from(document.querySelectorAll('script[src]'))
            .map(s => s.src)
            .filter(src => trackers.some(t => src.includes(t)));
    }""", _cfg.KNOWN_TRACKERS)

    has_dns_text = await page.evaluate("""() => {
        const t = document.body.innerText.toLowerCase();
        return t.includes('do not sell') || t.includes('your privacy choices')
            || t.includes('opt-out') || t.includes('california privacy');
    }""")

    return {
        "url":             url,
        "title":           await page.title(),
        "links":           links,
        "buttons":         buttons,
        "forms":           forms,
        "tracker_scripts": tracker_scripts,
        "has_dns_text":    has_dns_text,
    }


# ═══════════════════════════════════════════════════════════════
# Tool definitions for Claude (Anthropic tool_use format)
# ═══════════════════════════════════════════════════════════════

CLAUDE_TOOLS = [
    {
        "name": "analyze_page",
        "description": (
            "Analyze a webpage's extracted data for privacy risk. "
            "Return a risk score, list of priority URLs to crawl next, "
            "and any privacy violations found on this page."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "privacy_risk_score": {
                    "type": "integer",
                    "description": "Risk score 1-10. 10=highest risk (forms sending to 3rd party, trackers present, no DNS link)"
                },
                "risk_reasons": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Short reasons for the score"
                },
                "priority_urls": {
                    "type": "array",
                    "description": "URLs that should be crawled next, in priority order",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url":      {"type": "string"},
                            "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                            "reason":   {"type": "string"}
                        },
                        "required": ["url", "priority", "reason"]
                    }
                },
                "page_purpose": {
                    "type": "string",
                    "description": "What this page does (e.g. homepage, contact form, privacy policy, checkout)"
                },
                "trackers_loaded": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tracker domains detected on this page"
                },
                "pii_risk_elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Elements likely to transmit PII (e.g. 'email form → pardot.com')"
                }
            },
            "required": ["privacy_risk_score", "priority_urls", "page_purpose"]
        }
    }
]


# ═══════════════════════════════════════════════════════════════
# Claude agent loop
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a privacy compliance analyst working as the Discovery Agent in an Autonomous Privacy Observability (APO) system.

Your job is to analyze webpages during a crawl and:
1. Score the page for privacy risk (1-10)
2. Identify which links should be crawled next and why
3. Detect forms/scripts/elements that may violate CCPA/GPC rules

High priority URLs: checkout, contact, login, signup, privacy-policy, cookie-settings, newsletter, subscribe
Medium priority: about, products, search, categories  
Low priority: blog posts, press releases, pagination, social media links, external domains

Always prioritize pages likely to:
- Send user data to third parties
- Have tracking scripts
- Collect PII via forms
- Lack 'Do Not Sell' opt-out links

Use the analyze_page tool to return your structured analysis."""


def _call_claude(page_data: dict, visited_count: int, queue_size: int) -> dict:
    """
    Send one page's extracted data to LLM (Claude → GPT-4o fallback).
    Returns structured result: risk score, priority URLs, etc.
    """
    user_message = f"""Analyze this webpage for privacy risk and crawl prioritization.

Page data:
{json.dumps(page_data, indent=2)}

Context:
- Pages visited so far: {visited_count}
- Current queue size: {queue_size}
- Root site: {_cfg.ROOT_URL}

Use the analyze_page tool to return your structured analysis."""

    result = call_llm(
        prompt=user_message,
        tools=CLAUDE_TOOLS,
        system=SYSTEM_PROMPT,
        max_tokens=1024
    )

    if result["tool_result"]:
        return result["tool_result"]

    # Rule-based fallback
    score = len(page_data.get("tracker_scripts", [])) * 2
    score += len(page_data.get("forms", [])) * 2
    score += 0 if page_data.get("has_dns_text") else 3
    score = min(score, 10)
    return {
        "privacy_risk_score": score,
        "priority_urls": [
            {"url": l["href"], "priority": "medium", "reason": "rule-based"}
            for l in page_data.get("links", [])[:5]
        ],
        "page_purpose": "unknown",
        "risk_reasons": ["rule-based scoring (no LLM available)"],
    }


# ═══════════════════════════════════════════════════════════════
# Main discovery loop
# ═══════════════════════════════════════════════════════════════

async def run_discovery_agent() -> dict:
    ROOT_URL  = _cfg.ROOT_URL
    MAX_PAGES = _cfg.MAX_PAGES
    HEADLESS  = _cfg.HEADLESS
    SCROLL_STEPS = _cfg.SCROLL_STEPS
    GRAPH_FILE   = _cfg.GRAPH_FILE
    CLAUDE_MODEL = _cfg.CLAUDE_MODEL
    print("\n" + "═"*60)
    print("  Tier 1 — Discovery Agent (Claude-Powered)")
    print(f"  Model  : {CLAUDE_MODEL}")
    print(f"  Target : {ROOT_URL}")
    print("═"*60)

    nodes    = []
    edges    = []
    visited  = set()
    # Priority queue: list of (priority_int, url)
    # Priority: high=1, medium=2, low=3
    queue    = [(1, ROOT_URL)]
    node_map = {}   # url → node_id
    node_idx = 1
    total_llm_calls = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True,
        )
        page = await context.new_page()

        while queue and len(visited) < MAX_PAGES:
            # Pop highest priority URL
            queue.sort(key=lambda x: x[0])
            _, url = queue.pop(0)
            url = _clean_url(url)

            if url in visited:
                continue
            visited.add(url)

            print(f"\n  [{len(visited):02d}/{MAX_PAGES}] {url[:70]}")

            # Navigate
            nav = await navigate_to_page(page, url)
            if nav["status"] != "ok":
                print(f"    ⚠ Skip: {nav.get('msg','')[:50]}")
                continue

            # Extract page data
            page_data = await _extract_page_data(page, url)

            # ── Claude analyzes the page ───────────────────────
            print(f"    → Claude analyzing...")
            claude_result = _call_claude(page_data, len(visited), len(queue))
            total_llm_calls += 1

            risk_score  = claude_result.get("privacy_risk_score", 5)
            purpose     = claude_result.get("page_purpose", "unknown")
            risk_reasons= claude_result.get("risk_reasons", [])
            pii_risk    = claude_result.get("pii_risk_elements", [])
            trackers    = claude_result.get("trackers_loaded", page_data["tracker_scripts"])

            print(f"    ✓ Risk: {risk_score}/10 | Purpose: {purpose}")
            if risk_reasons:
                print(f"      Reasons: {', '.join(risk_reasons[:2])}")

            # ── Build node ────────────────────────────────────
            node_id = f"state_{node_idx:03d}"
            node_idx += 1
            node_map[url] = node_id

            nodes.append({
                "id":                node_id,
                "type":              "URL",
                "value":             url,
                "description":       page_data["title"],
                "page_purpose":      purpose,
                "privacy_risk_score":risk_score,
                "risk_reasons":      risk_reasons,
                "pii_risk_elements": pii_risk,
                "tracker_scripts":   trackers,
                "has_dns_text":      page_data["has_dns_text"],
                "buttons":           page_data["buttons"],
                "forms":             page_data["forms"],
                "scraped_at":        datetime.utcnow().isoformat(),
            })

            # ── Claude's priority URLs → add to queue ─────────
            priority_map = {"high": 1, "medium": 2, "low": 3}
            for item in claude_result.get("priority_urls", []):
                href = _clean_url(item.get("url", ""))
                pri  = priority_map.get(item.get("priority", "low"), 3)
                reason = item.get("reason", "")

                if not href or href in visited:
                    continue
                if not _same_domain(href):
                    continue  # only crawl same domain

                queue.append((pri, href))

                # Add edge
                edges.append({
                    "from":     node_id,
                    "to":       href,
                    "type":     "navigate",
                    "priority": item.get("priority", "low"),
                    "reason":   reason[:80],
                })

        await browser.close()

    # Sort nodes: highest risk first
    nodes.sort(key=lambda n: -n["privacy_risk_score"])

    graph = {
        "interaction_graph": {
            "audit_id":       f"apo_v2_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "root_url":       ROOT_URL,
            "model_used":     CLAUDE_MODEL,
            "total_llm_calls":total_llm_calls,
            "nodes":          nodes,
            "edges":          edges,
        }
    }

    GRAPH_FILE.write_text(json.dumps(graph, indent=2))

    print(f"\n  Discovery complete:")
    print(f"    Pages crawled  : {len(nodes)}")
    print(f"    Edges mapped   : {len(edges)}")
    print(f"    Claude calls   : {total_llm_calls}")
    print(f"    Graph saved    : {GRAPH_FILE}")
    print(f"    Top risk pages :")
    for n in nodes[:3]:
        print(f"      [{n['privacy_risk_score']}/10] {n['value'][:60]}")

    return graph


if __name__ == "__main__":
    asyncio.run(run_discovery_agent())
