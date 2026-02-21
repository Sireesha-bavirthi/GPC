# APO v2 — Autonomous Privacy Observability

**APO v2** is a fully automated privacy compliance scanner. It launches real browser sessions against any website, injects the **Global Privacy Control (GPC)** opt-out signal, captures all network traffic, and generates a structured evidence report of CCPA / GDPR violations — with exact fines, affected domains, and LLM-written remediation guidance.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [How the UI Connects to the Backend](#how-the-ui-connects-to-the-backend)
3. [Tier 1 — Discovery Agent](#tier-1--discovery-agent)
4. [Tier 2 — Interaction Agent ⭐](#tier-2--interaction-agent)
5. [Tier 3 — Observability Agent](#tier-3--observability-agent)
6. [mitmproxy Addon (Proxy Traffic Capture)](#mitmproxy-addon-proxy-traffic-capture)
7. [Core Modules](#core-modules)
8. [Configuration Reference](#configuration-reference)
9. [Output Files](#output-files)
10. [How to Run](#how-to-run)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      React Frontend (UI)                    │
│  User inputs: URL, Framework (CCPA/GDPR), Crawl Depth      │
└─────────────────────────────┬───────────────────────────────┘
                              │  POST /api/scan
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (backend.py)                │
│  • Sets cfg.ROOT_URL, cfg.JURISDICTION, cfg.MAX_PAGES       │
│  • Runs the 3-tier pipeline in a background thread          │
│  • Streams live logs via SSE  →  GET /api/stream/{id}       │
└──────┬──────────────────────┬──────────────────────┬────────┘
       │                      │                      │
       ▼                      ▼                      ▼
┌─────────────┐    ┌─────────────────────┐  ┌───────────────────┐
│  Tier 1     │    │  Tier 2             │  │  Tier 3           │
│  Discovery  │───▶│  Interaction Agent  │─▶│  Observability    │
│  Agent      │    │  (PARALLEL sessions)│  │  Agent            │
└─────────────┘    └─────────────────────┘  └───────────────────┘
     Crawl site         Baseline + GPC          Rules engine +
     Build graph        sessions run            LLM analysis +
     Risk-score         simultaneously          Evidence report
     each page          Capture traffic         (JSON output)
```

The three tiers run sequentially. The output of each feeds the next.

---

## How the UI Connects to the Backend

### Frontend → Backend (POST /api/scan)

The React UI sends:
```json
{
  "url": "https://www.example.com",
  "framework": "CCPA",
  "crawl_depth": 3,
  "claude_key": "sk-ant-...",   // optional
  "openai_key": "sk-..."        // optional
}
```

### Backend sets config dynamically

In `backend.py → _run_scan()`:
```python
cfg.ROOT_URL     = req.url          # e.g. "https://www.example.com"
cfg.JURISDICTION = req.framework    # e.g. "CCPA" or "GDPR"
cfg.MAX_PAGES    = req.crawl_depth * 5  # crawl depth slider → max pages
```

> **Important:** All agents read config values from the live `core.config` module at the time they run, not at import time. This ensures every scan uses the URL and framework the user chose, not the defaults.

### Live log streaming (SSE)

The frontend connects to `GET /api/stream/{scan_id}` which is a **Server-Sent Events** stream. Every `_emit()` call in the pipeline pushes a structured log event:
```json
{ "timestamp": "14:03:05", "agent": "discovery", "level": "INFO", "msg": "..." }
```
The UI renders these in real time as the coloured log panel.

### Final results

When the scan completes, the frontend calls `GET /api/results/{scan_id}` to fetch the full `evidence_report.json`.

---

## Tier 1 — Discovery Agent

**File:** `agents/tier1_discovery.py`

### What it does

Crawls the target website, scores every page for privacy risk, and builds an **interaction graph** — a structured map of the site that Tier 2 and Tier 3 use to focus their sessions on the highest-risk pages.

### How it works — step by step

```
Start with ROOT_URL in a priority queue
         │
         ▼
┌─────────────────────────────────────────────┐
│  For each URL in queue (up to MAX_PAGES):   │
│                                             │
│  1. navigate_to_page(url)                   │
│     Playwright loads page, waits for        │
│     networkidle                             │
│                                             │
│  2. _extract_page_data(page, url)           │
│     Extracts:                               │
│       • All <a href> links (up to 40)       │
│       • All buttons/submit inputs           │
│       • All <form> actions + fields         │
│       • Tracker <script src> tags           │
│       • Do Not Sell text detection          │
│                                             │
│  3. _call_claude(page_data)                 │
│     Sends extracted data to Claude API      │
│     Claude returns via tool_use:            │
│       • privacy_risk_score (1–10)           │
│       • priority_urls  ← next pages to crawl│
│       • page_purpose                        │
│       • risk_reasons                        │
│       • pii_risk_elements                   │
│                                             │
│  4. Build graph node for this page          │
│  5. Add Claude's priority_urls to queue     │
└─────────────────────────────────────────────┘
         │
         ▼
  Sort nodes highest risk first
  Save to output/interaction_graph.json
  Return graph dict to Tier 2
```

### Key methods

| Method | Purpose |
|--------|---------|
| `run_discovery_agent()` | Main async entry point. Manages the crawl queue loop and Playwright browser. |
| `_extract_page_data(page, url)` | Uses Playwright's `page.evaluate()` to pull links, buttons, forms, tracker scripts, and DNS text from the live DOM. |
| `_call_claude(page_data, visited, queue_size)` | Sends page data to Claude using `call_llm()` with the `analyze_page` tool. Falls back to rule-based scoring if no API key. |
| `_same_domain(url)` | Filters out external links — only same-domain URLs are crawled. |
| `_clean_url(url)` | Strips URL fragments and trailing slashes to avoid duplicate crawls. |

### LLM Tool: `analyze_page`
Claude is given the structured page data and must call this tool:
```json
{
  "privacy_risk_score": 8,
  "page_purpose": "checkout",
  "priority_urls": [
    {"url": "...", "priority": "high", "reason": "form sends to third party"}
  ],
  "risk_reasons": ["Facebook Pixel fires on load", "no Do Not Sell link"],
  "pii_risk_elements": ["email form → pardot.com"]
}
```
Pages with `priority: "high"` are put at the front of the crawl queue.

---

## Tier 2 — Interaction Agent

**File:** `agents/tier2_interaction.py`

This is the most complex tier. It runs **two full browser sessions in parallel** — one without GPC (baseline) and one with GPC enabled (compliance) — and compares what trackers fire in each.

### How it works — step by step

```
Receive graph from Tier 1
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 1: Claude plans the session                      │
│                                                         │
│  _plan_session_with_claude(nodes, MAX_JOURNEYS)         │
│  Sends all graph nodes to Claude with risk scores       │
│  Claude selects the most important pages to visit       │
│  and returns ordered list + observations                │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 2: Two sessions run in PARALLEL                  │
│  (asyncio.gather)                                       │
│                                                         │
│  🌐 BASELINE session          🔒 COMPLIANCE session      │
│  gpc_on = False               gpc_on = True             │
│  No Sec-GPC header            Header: Sec-GPC: 1        │
│  No JS override               navigator.globalPrivacy   │
│                               Control = true            │
│                                                         │
│  For each page in ordered_urls:                         │
│   • navigate_to_page(url)                               │
│   • scroll_page()                                       │
│   • detect_cookie_banner()  ─── checks CSS selectors    │
│   • detect_do_not_sell_link() ─ checks link text        │
│   • Traffic listener records every request              │
│   • detect_temporal_leak()  ─── (compliance only)       │
│     Flags trackers firing <500ms after page load        │
│   • _observe_page_with_claude() ─ (compliance only)     │
│     Claude writes 1-sentence observation per page       │
└─────────────────────────────────────────────────────────┘
         │
         ▼
  Save traffic logs, session state, cookies
  Return {baseline: {...}, compliance: {...}} to Tier 3
```

### Parallel session setup

```python
baseline_result, compliance_result = await asyncio.gather(
    _run_session(browser1, ordered_urls, gpc_on=False, ...),
    _run_session(browser2, ordered_urls, gpc_on=True,  ...),
)
```
Both browsers launch simultaneously. This cuts scan time roughly in half.

### GPC Signal Injection (Compliance Session only)

Two methods are used together to ensure the browser signals opt-out:

1. **HTTP Header** — every request sends `Sec-GPC: 1`
   ```python
   context = await browser.new_context(
       extra_http_headers={"Sec-GPC": "1"}
   )
   ```

2. **JavaScript override** — the JS property is set before any page scripts run
   ```python
   await context.add_init_script(
       "Object.defineProperty(navigator, 'globalPrivacyControl', {get: () => true})"
   )
   ```

### Traffic Listener

`make_traffic_listener(session_label)` in `core/tools.py` attaches a callback to the Playwright `page.on("request", ...)` event. For every outgoing HTTP request it records:
- URL, domain, method, resource type
- Timestamp in milliseconds (crucial for temporal leak detection)
- Whether the domain is a **known tracker**
- Whether the URL contains **PII** (email, uid, phone, hashed email, IP)

### Temporal Leak Detection

```python
def detect_temporal_leak(traffic_log, page_load_ts_ms):
```
After each page loads, it checks: did any tracker fire within **500ms** of the page load timestamp? If yes, it's a **temporal leak** — the tracker already sent data before the opt-out could be processed.

### Key methods in Tier 2

| Method | Purpose |
|--------|---------|
| `run_interaction_agent(graph)` | Main entry point. Calls Claude to plan, then runs parallel sessions. |
| `_plan_session_with_claude(nodes, max_visits)` | Sends the interaction graph to Claude. Claude picks the most privacy-risky pages to visit. Uses `decide_session_actions` tool. |
| `_run_session(browser, ordered_urls, gpc_on, plan)` | Runs one complete browser session over all selected pages. Captures traffic, cookie banners, DNS links, temporal leaks. |
| `_observe_page_with_claude(url, banner, dns, trackers, gpc_on)` | Asks Claude to write a one-sentence compliance observation for each page visited in the compliance session. |

### LLM Tool: `decide_session_actions`
Claude receives all graph nodes with their risk scores and must call:
```json
{
  "pages_to_visit": ["https://example.com/", "https://example.com/privacy"],
  "observations": ["All pages have trackers", "No Do Not Sell link found"],
  "high_risk_pages": [
    {"url": "https://example.com/checkout", "reason": "form sends to pardot"}
  ]
}
```

### mitmproxy (optional, runs alongside Tier 2)

While Tier 2 sessions run, a **mitmproxy** process is started as a subprocess on port 18080. The `proxy_addon.py` intercepts every request/response and writes it to `output/raw_traffic_proxy.jsonl`. This captures the actual `Sec-GPC` header as sent over the wire, full POST bodies, and `Set-Cookie` response headers — richer evidence than Playwright alone provides.

---

## Tier 3 — Observability Agent

**File:** `agents/tier3_observability.py`

Takes the session results from Tier 2 and produces the final structured evidence report. Three sub-phases run in sequence:

### Part A — Rule-Based Detectors

Loads `rules.sql` into an in-memory SQLite database, fetches all rules for the selected jurisdiction (CCPA or GDPR), then runs 5 detectors:

| Detector | Rule | What it checks |
|----------|------|----------------|
| `_check_gpc_not_honored` | CCPA §1798.135(b)(1) | Tracker domains that fired in BOTH baseline AND compliance sessions — meaning they ignored the GPC signal |
| `_check_temporal_leaks` | CCPA §1798.135(b)(1) | Trackers that fired within 500ms of page load in the compliance session |
| `_check_dns_link` | CCPA §1798.135(a) | Pages missing a "Do Not Sell" link |
| `_check_cookie_banner` | CCPA §1798.130 / GDPR ePrivacy | Pages with no cookie consent banner |
| `_check_pii_in_requests` | CCPA §1798.100 | Requests where PII (email, uid, hashed IDs) appears in the URL |

### Part B — LLM Analysis

Two LLM calls run if API keys are available:

1. **Claude reads the privacy policy** (`_check_privacy_policy_with_claude`)
   - Checks for presence of: opt-out right, deletion right, GPC mention, categories disclosed, non-discrimination clause
   - Returns structured JSON with `present: true/false` + quoted evidence

2. **GPT-4o classifies violations** (`_classify_violations_with_gpt4o`)
   - For each detected violation, GPT-4o writes:
     - `plain_english` — a 2-sentence plain explanation for non-lawyers
     - `technical_fix` — exact engineering action to remediate

### Part C — Report Builder

`_build_report()` assembles all data into a single structured JSON:
```json
{
  "report_metadata": { "target", "jurisdiction", "generated_at", ... },
  "session_summary": { "baseline": {...}, "compliance_gpc_on": {...} },
  "gpc_verdict": { "verdict": "NON-COMPLIANT", "domains_ignoring_gpc": [...] },
  "privacy_policy_analysis": { "opt_out_right": {...}, ... },
  "violation_summary": { "total": 4, "severity_breakdown": {...}, "max_potential_penalty_usd": 30000 },
  "violations": [ { "rule_id", "section", "violation_type", "severity", "evidence", "penalty_min_usd", "penalty_max_usd", "recommendation", "llm_explanation", "llm_technical_fix" } ]
}
```
Saved to `output/evidence_report.json`.

---

## mitmproxy Addon (Proxy Traffic Capture)

**File:** `proxy_addon.py`

A mitmproxy addon class (`APOProxyAddon`) that runs as a subprocess during Tier 2. It hooks into two mitmproxy events:

| Hook | Method | What it captures |
|------|--------|-----------------|
| Outgoing request | `request(flow)` | URL, method, domain, `Sec-GPC` header value, POST body (for form submissions), is_tracker flag |
| Server response | `response(flow)` | Status code, `Set-Cookie` headers, content-type |

All records are appended to `output/raw_traffic_proxy.jsonl` (one JSON object per line). After both sessions complete, Tier 3 loads these records and can inject them into the session results for richer analysis.

---

## Core Modules

### `core/config.py`
Single source of truth for all settings. Key values:

| Variable | Default | Set by UI? |
|----------|---------|-----------|
| `ROOT_URL` | `https://www.cpchem.com` | ✅ Yes — from URL input |
| `JURISDICTION` | `CCPA` | ✅ Yes — from framework dropdown |
| `MAX_PAGES` | `10` | ✅ Yes — `crawl_depth × 5` |
| `ANTHROPIC_API_KEY` | from `.env` | ✅ Optional — from key fields |
| `OPENAI_API_KEY` | from `.env` | ✅ Optional — from key fields |
| `KNOWN_TRACKERS` | list of 30+ domains | ❌ Fixed |
| `TEMPORAL_LEAK_MS` | `500` | ❌ Fixed |
| `GPC_HEADER_KEY/VALUE` | `Sec-GPC: 1` | ❌ Fixed |

### `core/llm_router.py` — `call_llm()`

Universal LLM caller with automatic Claude → GPT-4o → rule-based fallback:
```
1. Try Claude (Anthropic API) with tool_use
2. If that fails → try GPT-4o (OpenAI API) with function calling
3. If no API keys → return empty, caller uses built-in fallback logic
```

### `core/rules_db.py` — `load_rules_db()` / `fetch_rules()`

Parses `rules.sql` into an in-memory SQLite DB on every scan. `fetch_rules(conn, "CCPA")` returns all rules for that jurisdiction as a list of dicts with `rule_id`, `section_citation`, `rule_title`, `violation_penalty_min`, `violation_penalty_max`.

### `core/tools.py` — Browser Tools

| Tool | Type | Purpose |
|------|------|---------|
| `navigate_to_page(page, url)` | async | Goto URL, wait for networkidle, return status |
| `scroll_page(page, steps)` | async | Scroll down in increments to trigger lazy-loaded content |
| `detect_cookie_banner(page)` | async | Check DOM for cookie consent elements via CSS selectors |
| `detect_do_not_sell_link(page)` | async | Scan all links and buttons for "do not sell" / "opt-out" text |
| `make_traffic_listener(label)` | sync | Returns a `(log_list, on_request_handler)` pair for Playwright's request event |
| `detect_temporal_leak(log, ts)` | sync | Finds tracker requests within 500ms of page load |
| `save_session_state(page, path)` | async | Saves cookies, localStorage, sessionStorage to JSON |
| `inject_gpc_signal(page)` | async | Injects GPC JS override (used as alternative to init_script) |
| `click_element(page, selector)` | async | Clicks a DOM element; auto-dismisses modals first |
| `fill_form_field(page, sel, val)` | async | Fills and optionally submits a form field |

---

## Configuration Reference

Create a `.env` file in `apo_v2/`:
```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

All other settings in `core/config.py`:
```python
MAX_PAGES        = 10      # max pages to crawl (UI: crawl_depth × 5)
SCROLL_STEPS     = 3       # scroll iterations per page
HEADLESS         = True    # set False to watch the browser live
MAX_JOURNEYS     = 20      # max pages per session in Tier 2
ACTION_DELAY_MS  = 800     # ms pause between interactions
PAGE_LOAD_TIMEOUT= 30_000  # ms to wait for page load
TEMPORAL_LEAK_MS = 500     # ms window for temporal leak detection
```

---

## Output Files

All files are written to `apo_v2/output/`:

| File | Written by | Contents |
|------|-----------|---------|
| `interaction_graph.json` | Tier 1 | All crawled pages with risk scores, links, trackers |
| `traffic_baseline.json` | Tier 2 | Every HTTP request from the baseline (no GPC) session |
| `traffic_compliance.json` | Tier 2 | Every HTTP request from the GPC-on session |
| `session_state_baseline.json` | Tier 2 | Cookies, localStorage, sessionStorage — baseline |
| `session_state_compliance.json` | Tier 2 | Cookies, localStorage, sessionStorage — compliance |
| `raw_traffic_proxy.jsonl` | mitmproxy | Full request+response records with headers (one JSON per line) |
| `evidence_report.json` | Tier 3 | Final structured evidence report with all violations |

---

## How to Run

### Kill existing ports
```bash
lsof -ti :8000 | xargs kill -9 2>/dev/null
lsof -ti :8080 | xargs kill -9 2>/dev/null
```

### Terminal 1 — Backend
```bash
cd /Users/bhargavigundabathina/Desktop/GPC/apo_v2
venv/bin/python backend.py
# Starts FastAPI on http://localhost:8000 with hot reload
```

### Terminal 2 — Frontend
```bash
cd /Users/bhargavigundabathina/Desktop/GPC/apo
npm run dev
# Starts React/Vite on http://localhost:8080
```

### CLI (no UI, no API server)
```bash
cd /Users/bhargavigundabathina/Desktop/GPC/apo_v2
venv/bin/python main.py --url https://www.example.com
venv/bin/python main.py --skip-discovery  # reuse last crawl
```

### Requirements
```bash
venv/bin/pip install -r requirements.txt
venv/bin/playwright install chromium
```

`requirements.txt` includes: `fastapi`, `uvicorn`, `playwright`, `anthropic`, `openai`, `mitmproxy`, `pydantic`
