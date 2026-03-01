"""
APO v2 — Tier 3: Observability Agent
======================================
Three-part observability pipeline:

  Part A: Rule Engine — loads rules.sql into SQLite, runs 5 detectors
  Part B: LLM Analysis — Claude reads privacy policy, GPT-4o classifies violations
  Part C: Report Builder — generates structured JSON evidence report

Saves:
  output/compliance_report.json
  output/evidence_report.json
"""

import json
import re
from datetime import datetime
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import core.config as _cfg
from core.config import (
    COMPLIANCE_REPORT_FILE, EVIDENCE_REPORT_FILE,
    RULES_SQL_FILE, OPENAI_API_KEY, ANTHROPIC_API_KEY,
    CLAUDE_MODEL, OPENAI_MODEL, LLM_MAX_TOKENS,
    KNOWN_TRACKERS
)
from core.rules_db import load_rules_db, fetch_rules


# ═══════════════════════════════════════════════════════════════
# PART A — Rule-based violation detectors
# ═══════════════════════════════════════════════════════════════

def _find_rule(rules: list, *keywords) -> dict | None:
    for r in rules:
        if any(k in r["rule_id"] for k in keywords):
            return r
    return None


def _check_gpc_not_honored(b_log: list, c_log: list, rules: list) -> list:
    """CCPA §1798.135(b)(1) — trackers fire despite GPC ON"""
    rule = _find_rule(rules, "135b", "1798.135b")
    if not rule:
        return []
    b_domains = {r["domain"] for r in b_log if r.get("is_tracker")}
    c_domains = {r["domain"] for r in c_log if r.get("is_tracker")}
    violated  = sorted(b_domains & c_domains)
    if not violated:
        return []
    b_count = len([r for r in b_log if r.get("is_tracker")])
    c_count = len([r for r in c_log if r.get("is_tracker")])
    return [{
        "rule_id": rule["rule_id"],
        "section": rule["section_citation"],
        "rule_title": rule["rule_title"],
        "violation_type": "GPC_NOT_HONORED",
        "severity": "HIGH",
        "evidence": {
            "domains_ignoring_gpc": violated,
            "baseline_tracker_requests": b_count,
            "compliance_tracker_requests": c_count,
            "reduction_percent": round((1 - c_count / max(b_count, 1)) * 100, 1),
        },
        "penalty_min_usd": rule["violation_penalty_min"],
        "penalty_max_usd": rule["violation_penalty_max"],
        "recommendation": (
            "Stop all third-party tracker beacons when Sec-GPC: 1 header is "
            "received. Process within 15 business days (§1798.185(a)(14))."
        ),
    }]


def _check_temporal_leaks(temporal_leaks: list, rules: list) -> list:
    """Temporal leak — tracker fires within 500ms of GPC signal"""
    rule = _find_rule(rules, "135b", "1798.135b")
    if not rule or not temporal_leaks:
        return []
    unique_domains = sorted({l["domain"] for l in temporal_leaks})
    return [{
        "rule_id": rule["rule_id"],
        "section": rule["section_citation"],
        "rule_title": rule["rule_title"],
        "violation_type": "TEMPORAL_LEAK",
        "severity": "HIGH",
        "evidence": {
            "leak_count": len(temporal_leaks),
            "leaked_domains": unique_domains,
            "sample_leaks": temporal_leaks[:3],
            "window_ms": 500,
        },
        "penalty_min_usd": rule["violation_penalty_min"],
        "penalty_max_usd": rule["violation_penalty_max"],
        "recommendation": (
            "Trackers fired within 500ms of the GPC signal — data was already "
            "transmitted before opt-out could be processed. Pre-block trackers "
            "before page load when GPC header is detected."
        ),
    }]


def _check_dns_link(dns_results: dict, rules: list) -> list:
    """CCPA §1798.135(a) — Do Not Sell link must be on every page"""
    rule = _find_rule(rules, "135a", "1798.135a")
    if not rule:
        return []
    missing = [url for url, r in dns_results.items() if not r.get("link_found")]
    if not missing:
        return []
    return [{
        "rule_id": rule["rule_id"],
        "section": rule["section_citation"],
        "rule_title": rule["rule_title"],
        "violation_type": "MISSING_DO_NOT_SELL_LINK",
        "severity": "HIGH",
        "evidence": {
            "pages_missing_link": missing[:10],
            "total_pages_checked": len(dns_results),
            "pages_compliant": len(dns_results) - len(missing),
        },
        "penalty_min_usd": rule["violation_penalty_min"],
        "penalty_max_usd": rule["violation_penalty_max"],
        "recommendation": (
            "Add a clear and conspicuous 'Do Not Sell or Share My Personal "
            "Information' link to all pages (CCPA §1798.135(a))."
        ),
    }]


def _check_cookie_banner(banner_results: dict, rules: list) -> list:
    """ePrivacy / CCPA §1798.130 — consent notice required"""
    rule_id = "GDPR-ePD-Art5.3" if _cfg.JURISDICTION == "GDPR" else "CCPA-1798.130a5A"
    rule = _find_rule(rules, rule_id)
    if not rule:
        return []
    no_banner = [url for url, r in banner_results.items() if not r.get("banner_detected")]
    if not no_banner:
        return []
    return [{
        "rule_id":      rule["rule_id"],
        "section":      rule["section_citation"],
        "rule_title":   rule["rule_title"],
        "violation_type": "NO_CONSENT_BANNER",
        "severity":     "MEDIUM",
        "evidence": {
            "pages_without_banner": no_banner[:10],
            "total_pages_checked":  len(banner_results),
        },
        "penalty_min_usd": rule.get("violation_penalty_min"),
        "penalty_max_usd": rule.get("violation_penalty_max"),
        "recommendation": (
            "Display a privacy/cookie consent banner on all pages before "
            "loading non-essential tracking scripts."
        ),
    }]


def _check_pii_in_requests(c_log: list, rules: list) -> list:
    """CCPA §1798.100 — PII must not leak through tracking URLs"""
    rule = _find_rule(rules, "1798.100")
    if not rule:
        return []
    pii_hits = [
        {"url": r["url"][:150], "pii_types": r["pii_detected"]}
        for r in c_log if r.get("pii_detected")
    ]
    if not pii_hits:
        return []
    return [{
        "rule_id":    rule["rule_id"],
        "section":    rule["section_citation"],
        "rule_title": rule["rule_title"],
        "violation_type": "PII_IN_TRACKING_REQUESTS",
        "severity":   "HIGH",
        "evidence": {
            "total_pii_hits": len(pii_hits),
            "sample_hits":    pii_hits[:5],
        },
        "penalty_min_usd": rule["violation_penalty_min"],
        "penalty_max_usd": rule["violation_penalty_max"],
        "recommendation": (
            "Remove or anonymize PII from outbound tracker URLs. "
            "Never pass email, phone, or hashed IDs in beacon request parameters."
        ),
    }]


# ═══════════════════════════════════════════════════════════════
# PART B — LLM Analysis
# ═══════════════════════════════════════════════════════════════

def _check_privacy_policy_with_claude(policy_text: str) -> dict:
    """
    Claude 3.5 Sonnet reads the privacy policy text and checks
    whether CCPA/GDPR-required disclosures are present.
    Falls back gracefully if no API key.
    """
    if not ANTHROPIC_API_KEY:
        return {"skipped": True, "reason": "No ANTHROPIC_API_KEY set"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = f"""You are a privacy compliance expert. Read the following privacy policy and answer each question with YES or NO, then a one-sentence explanation.

PRIVACY POLICY TEXT:
{policy_text[:6000]}

QUESTIONS:
1. Does the policy mention the right to opt-out of sale or sharing of personal information? (CCPA §1798.120)
2. Does the policy describe how consumers can submit a deletion request? (CCPA §1798.105)
3. Does the policy mention Global Privacy Control (GPC) or automatic opt-out signals?
4. Does the policy list the categories of personal information collected? (CCPA §1798.100)
5. Does the policy mention the right not to be discriminated against for exercising privacy rights? (CCPA §1798.125)

Respond ONLY in this JSON format:
{{
  "opt_out_right": {{"present": true/false, "quote": "..."}},
  "deletion_right": {{"present": true/false, "quote": "..."}},
  "gpc_mentioned": {{"present": true/false, "quote": "..."}},
  "categories_listed": {{"present": true/false, "quote": "..."}},
  "non_discrimination": {{"present": true/false, "quote": "..."}}
}}"""

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=LLM_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        # Parse JSON from response
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return {"skipped": False, "analysis": json.loads(json_match.group())}
        return {"skipped": False, "raw": raw}

    except Exception as e:
        return {"skipped": True, "reason": str(e)}


def _classify_violations_with_gpt4o(violations: list) -> list:
    """
    GPT-4o adds a plain-English explanation and actionable fix
    to each violation. Falls back if no API key.
    """
    if not OPENAI_API_KEY or not violations:
        return violations

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        violations_summary = json.dumps([
            {"type": v["violation_type"], "section": v["section"],
             "evidence_summary": str(v["evidence"])[:200]}
            for v in violations
        ], indent=2)

        prompt = f"""You are a CCPA compliance attorney. For each violation below, provide:
1. A plain-English explanation (2 sentences, no legal jargon)
2. A specific technical fix the engineering team should implement

Violations:
{violations_summary}

Respond as a JSON array matching the input order:
[{{"plain_english": "...", "technical_fix": "..."}}]"""

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a CCPA compliance expert. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=LLM_MAX_TOKENS,
        )
        raw = response.choices[0].message.content
        parsed = json.loads(raw)
        # GPT might return {"violations": [...]} or just [...]
        if isinstance(parsed, dict):
            parsed = list(parsed.values())[0]

        for i, v in enumerate(violations):
            if i < len(parsed):
                if isinstance(parsed[i], dict):
                    v["llm_explanation"]  = parsed[i].get("plain_english", "")
                    v["llm_technical_fix"]= parsed[i].get("technical_fix", "")
                else:
                    v["llm_explanation"]  = str(parsed[i])
                    v["llm_technical_fix"]= ""
        return violations

    except Exception as e:
        print(f"  [LLM] GPT-4o classification skipped: {e}")
        return violations


# ═══════════════════════════════════════════════════════════════
# PART C — Report Builder
# ═══════════════════════════════════════════════════════════════

def _build_report(session_results: dict, violations: list,
                  privacy_policy_analysis: dict) -> dict:
    baseline   = session_results["baseline"]
    compliance = session_results["compliance"]

    b_trackers = [r for r in baseline["traffic_log"]   if r.get("is_tracker")]
    c_trackers = [r for r in compliance["traffic_log"] if r.get("is_tracker")]
    violated_domains = sorted(
        {r["domain"] for r in b_trackers} & {r["domain"] for r in c_trackers}
    )

    severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for v in violations:
        s = v.get("severity", "LOW")
        severity_counts[s] = severity_counts.get(s, 0) + 1

    total_penalty = sum(v.get("penalty_max_usd") or 0 for v in violations)

    report = {
        "report_metadata": {
            "tool":          "APO v2 — Autonomous Privacy Observability",
            "version":       "2.0",
            "target":        _cfg.ROOT_URL,
            "jurisdiction":  _cfg.JURISDICTION,
            "generated_at":  datetime.utcnow().isoformat() + "Z",
            "elapsed_seconds": session_results.get("elapsed_seconds"),
        },
        "session_summary": {
            "baseline": {
                "pages_visited":    baseline["pages_visited"],
                "total_requests":   len(baseline["traffic_log"]),
                "tracker_requests": len(b_trackers),
                "unique_tracker_domains": sorted({r["domain"] for r in b_trackers}),
            },
            "compliance_gpc_on": {
                "pages_visited":    compliance["pages_visited"],
                "total_requests":   len(compliance["traffic_log"]),
                "tracker_requests": len(c_trackers),
                "unique_tracker_domains": sorted({r["domain"] for r in c_trackers}),
                "temporal_leaks":   len(compliance.get("temporal_leaks", [])),
            },
        },
        "gpc_verdict": {
            "verdict":                   "NON-COMPLIANT" if violated_domains else "COMPLIANT",
            "domains_ignoring_gpc":      violated_domains,
            "temporal_leak_count":       len(compliance.get("temporal_leaks", [])),
        },
        "privacy_policy_analysis": privacy_policy_analysis,
        "violation_summary": {
            "total":                     len(violations),
            "severity_breakdown":        severity_counts,
            "max_potential_penalty_usd": total_penalty,
        },
        "violations": violations,
    }

    EVIDENCE_REPORT_FILE.write_text(json.dumps(report, indent=2))
    return report


def _print_summary(report: dict):
    verdict = report["gpc_verdict"]["verdict"]
    icon    = "🚨" if verdict == "NON-COMPLIANT" else "✅"
    vs      = report["violation_summary"]
    gpc     = report["gpc_verdict"]

    print("\n" + "═"*65)
    print("  APO v2 — EVIDENCE REPORT")
    print("═"*65)
    print(f"  Target      : {report['report_metadata']['target']}")
    print(f"  Jurisdiction: {report['report_metadata']['jurisdiction']}")
    print(f"  Generated   : {report['report_metadata']['generated_at']}")
    print(f"  Time taken  : {report['report_metadata']['elapsed_seconds']}s (parallel sessions)")
    print(f"\n  GPC Verdict : {verdict} {icon}")
    if gpc["domains_ignoring_gpc"]:
        for d in gpc["domains_ignoring_gpc"]:
            print(f"    ✗ {d}")
    print(f"  Temporal leaks detected: {gpc['temporal_leak_count']}")
    print(f"\n  Violations  : {vs['total']}")
    print(f"  HIGH        : {vs['severity_breakdown']['HIGH']}")
    print(f"  MEDIUM      : {vs['severity_breakdown']['MEDIUM']}")
    print(f"  Max Penalty : ${vs['max_potential_penalty_usd']:,.2f}")

    print(f"\n  {'─'*60}")
    for i, v in enumerate(report["violations"], 1):
        icon2 = "🔴" if v["severity"] == "HIGH" else "🟡"
        print(f"\n  [{i}] {icon2} {v['violation_type']}")
        print(f"       Rule : {v['rule_id']} — {v['section']}")
        if v.get("llm_explanation"):
            print(f"       Plain: {v['llm_explanation'][:100]}")
    print("\n" + "═"*65)


# ═══════════════════════════════════════════════════════════════
# Main entry
# ═══════════════════════════════════════════════════════════════

def run_observability_agent(session_results: dict,
                             privacy_policy_text: str = "") -> dict:
    """
    Full observability pipeline:
    A) Rule engine → violations
    B) LLM analysis → enrich violations + policy check
    C) Build + save report
    """
    # Read live config so backend URL/jurisdiction overrides are picked up
    JURISDICTION = _cfg.JURISDICTION
    ROOT_URL     = _cfg.ROOT_URL
    print("\n" + "═"*60)
    print("  Tier 3 — Observability Agent")
    print("═"*60)

    # Load rules
    conn  = load_rules_db(RULES_SQL_FILE)
    rules = fetch_rules(conn, JURISDICTION)
    print(f"  Loaded {len(rules)} {JURISDICTION} rules from rules.sql")

    b_log  = session_results["baseline"]["traffic_log"]
    c_log  = session_results["compliance"]["traffic_log"]
    dns_r  = session_results["compliance"]["dns_link_results"]
    ban_r  = session_results["compliance"]["banner_results"]
    t_leaks= session_results["compliance"].get("temporal_leaks", [])

    # Part A — rule-based detectors
    print("\n  [A] Running rule-based detectors...")
    violations = []
    violations += _check_gpc_not_honored(b_log, c_log, rules)
    violations += _check_temporal_leaks(t_leaks, rules)
    violations += _check_dns_link(dns_r, rules)
    violations += _check_cookie_banner(ban_r, rules)
    violations += _check_pii_in_requests(c_log, rules)
    print(f"      Found {len(violations)} violations")

    # Part B — LLM
    print("\n  [B] LLM analysis...")
    policy_analysis = {}
    if privacy_policy_text:
        print("      Claude: reading privacy policy...")
        policy_analysis = _check_privacy_policy_with_claude(privacy_policy_text)
        skipped = policy_analysis.get("skipped", False)
        print(f"      Claude: {'skipped — ' + policy_analysis.get('reason','') if skipped else 'done ✓'}")

    if violations:
        print("      GPT-4o: classifying violations...")
        violations = _classify_violations_with_gpt4o(violations)
        print("      GPT-4o: done ✓" if OPENAI_API_KEY else "      GPT-4o: skipped (no key)")

    # Part C — build report
    print("\n  [C] Building evidence report...")
    report = _build_report(session_results, violations, policy_analysis)
    _print_summary(report)

    print(f"\n  Evidence report → {EVIDENCE_REPORT_FILE}")
    return report
