"""
APO v2 — Main Entry Point
===========================
Usage:
    python main.py
    python main.py --url https://www.cpchem.com --jurisdiction CCPA
    python main.py --skip-discovery   # reuse existing interaction_graph.json

Pipeline:
    Tier 1: Discovery Agent   → crawls site, builds interaction graph
    Tier 2: Interaction Agent → parallel baseline + compliance sessions
    Tier 3: Observability     → rules engine + LLM + evidence report
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from core.config import (
    ROOT_URL, JURISDICTION, GRAPH_FILE, EVIDENCE_REPORT_FILE,
    OUTPUT_DIR, OPENAI_API_KEY, ANTHROPIC_API_KEY
)
from agents.tier1_discovery    import run_discovery_agent
from agents.tier2_interaction  import run_interaction_agent
from agents.tier3_observability import run_observability_agent


def print_banner():

    print(f"  Target      : {ROOT_URL}")
    print(f"  Jurisdiction: {JURISDICTION}")
    print(f"  Output dir  : {OUTPUT_DIR}")
    llm_status = []
    if ANTHROPIC_API_KEY: llm_status.append("Claude ✓")
    if OPENAI_API_KEY:    llm_status.append("GPT-4o ✓")
    print(f"  LLM         : {', '.join(llm_status) if llm_status else 'None (rule-based only)'}")
    print()


async def main(skip_discovery: bool = False):
    print_banner()

    # ── Tier 1: Discovery ─────────────────────────────────────
    if skip_discovery and GRAPH_FILE.exists():
        print("[Tier 1] Skipping — loading existing graph:", GRAPH_FILE)
        with open(GRAPH_FILE) as f:
            graph = json.load(f)
        node_count = len(graph["interaction_graph"]["nodes"])
        print(f"[Tier 1] Loaded {node_count} nodes from cache")
    else:
        print("[Tier 1] Starting Discovery Agent...")
        graph = await run_discovery_agent()

    # ── Tier 2: Interaction ───────────────────────────────────
    print("\n[Tier 2] Starting Interaction Agent (parallel sessions)...")
    session_results = await run_interaction_agent(graph)

    # ── Fetch privacy policy text for LLM ────────────────────
    policy_text = ""
    policy_node = next(
        (n for n in graph["interaction_graph"]["nodes"]
         if "privacy" in n["value"].lower()),
        None
    )
    if policy_node:
        # Simple text extraction from session logs is enough
        # (Full content was scrolled during session)
        policy_text = f"Privacy policy page found at: {policy_node['value']}"
        print(f"\n[Tier 3] Privacy policy page: {policy_node['value']}")

    # ── Tier 3: Observability ─────────────────────────────────
    print("\n[Tier 3] Starting Observability Agent...")
    report = run_observability_agent(session_results, policy_text)

    # ── Final Summary ─────────────────────────────────────────
    verdict = report["gpc_verdict"]["verdict"]
    total_v = report["violation_summary"]["total"]
    penalty = report["violation_summary"]["max_potential_penalty_usd"]

    print(f"""

  FINAL RESULT                                                
  Verdict   : {verdict:<48}║
  Violations: {str(total_v):<48}║
  Max Fine  : ${str(f'${penalty:,.0f}'):<47}║


  Output files:
    {GRAPH_FILE}
    {EVIDENCE_REPORT_FILE}
""")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APO v2 — Privacy Compliance Scanner")
    parser.add_argument("--skip-discovery", action="store_true",
                        help="Reuse existing interaction_graph.json")
    args = parser.parse_args()

    asyncio.run(main(skip_discovery=args.skip_discovery))
