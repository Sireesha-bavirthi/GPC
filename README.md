# APO v2 — Autonomous Privacy Observability

> **What this is in one sentence:**
> An automated tool that visits any website like a real user, tests whether the site respects privacy choices (cookie consent, GPC opt-out), and produces a legal evidence report citing exact CCPA / GDPR violations and fines.

---

## 📁 Folder Structure

Everything lives inside `apo_v2/`. The **backend** (Python/FastAPI) and the **frontend** (React) are both here.

```
apo_v2/
│
├── backend.py              ← FastAPI server — the bridge between UI and pipeline
├── main.py                 ← CLI entry point (run without a UI)
├── proxy_addon.py          ← mitmproxy plugin to capture raw network traffic
├── rules.sql               ← All CCPA & GDPR rules stored as SQL (25 rules)
├── requirements.txt        ← Python packages needed
├── .env.template           ← Copy this to .env and add your API keys
│
├── agents/                 ← The 3-tier pipeline (runs the actual scan)
│   ├── tier1_discovery.py  ← Crawls the website, maps all pages
│   ├── tier2_interaction.py← Opens browser, runs 4 sessions, records traffic
│   └── tier3_observability.py ← Checks rules, generates violation report
│
├── core/                   ← Shared utilities used by all agents
│   ├── config.py           ← All settings in one place (URL, jurisdiction, etc.)
│   ├── llm_router.py       ← Calls Claude / GPT-4o with auto-fallback
│   ├── rules_db.py         ← Loads rules.sql into SQLite for fast lookup
│   └── tools.py            ← Browser tools (navigate, scroll, detect banners, etc.)
│
├── apo/                    ← React frontend (the web UI)
│   ├── src/
│   │   ├── pages/          ← Main scan page
│   │   ├── components/     ← UI blocks: ScanForm, TerminalLog, ViolationsTable, etc.
│   │   └── lib/api.ts      ← Calls backend API endpoints
│   ├── package.json
│   └── index.html
│
└── output/                 ← All scan results are saved here (auto-created)
    ├── interaction_graph.json      ← Map of all pages crawled
    ├── traffic_baseline.json       ← Network requests (no consent action)
    ├── traffic_compliance.json     ← Network requests (GPC signal ON)
    ├── session_state_baseline.json ← Cookies & storage from baseline
    ├── session_state_compliance.json
    ├── raw_traffic_proxy.jsonl     ← Deep traffic capture via mitmproxy
    └── evidence_report.json        ← ✅ Final violation report (what the UI shows)
```

---

## 🔄 How It Works — The Full Pipeline

When a user submits a scan from the UI (or CLI), this is what happens step by step:

```
User enters URL + settings in the React UI
           │
           ▼
    POST /api/scan  →  backend.py
           │
           ▼
    ┌──────────────────────────────────────────────┐
    │  TIER 1 — Discovery Agent                    │
    │  tier1_discovery.py                          │
    │                                              │
    │  • Opens a browser with Playwright           │
    │  • Visits the target URL                     │
    │  • Finds all links, forms, buttons           │
    │  • Uses Claude AI to score each page's       │
    │    privacy risk (1–10)                       │
    │  • Saves a map of every page found           │
    │  → Outputs: interaction_graph.json           │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  TIER 2 — Interaction Agent                  │
    │  tier2_interaction.py                        │
    │                                              │
    │  Runs 4 browser sessions (in order):         │
    │                                              │
    │  1. BASELINE      — visits with no action    │
    │  2. CONSENT ACCEPT — clicks "Accept All"     │
    │  3. CONSENT DECLINE — clicks "No Thanks"     │
    │  4. GPC COMPLIANCE — sends Sec-GPC: 1 header │
    │                                              │
    │  Each session records every network request: │
    │  • Which tracker companies were called?      │
    │  • Was PII (email, location) sent?           │
    │  • Did trackers still fire after "No Thanks"?│
    │  • Did trackers fire before the user could   │
    │    even see the consent banner?              │
    │                                              │
    │  → Outputs: traffic_*.json, session_*.json   │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────────────┐
    │  TIER 3 — Observability Agent                │
    │  tier3_observability.py                      │
    │                                              │
    │  Loads all 25 CCPA + GDPR rules from DB      │
    │  Runs each rule detector:                    │
    │                                              │
    │  CCPA checks:                                │
    │  ✓ GPC signal not honored?                   │
    │  ✓ "Do Not Sell" link missing?               │
    │  ✓ No cookie/consent banner?                 │
    │  ✓ PII in tracker requests?                  │
    │  ✓ Sensitive data (health, finance) exposed? │
    │  ✓ No privacy policy page?                   │
    │  ✓ Consent wall (service gated behind Accept)?│
    │  ✓ Trackers active right after opt-out?      │
    │                                              │
    │  GDPR checks:                                │
    │  ✓ Trackers loading before user sees banner? │
    │  ✓ Cross-site tracking identifiers present?  │
    │  ✓ Device fingerprinting detected?           │
    │  ✓ Decline option absent or hidden?          │
    │  ✓ Accept and Decline have same tracker load?│
    │  ✓ No transparency disclosure page?          │
    │  ✓ No erasure / "delete my data" mechanism? │
    │  ✓ Marketing trackers still firing after     │
    │    objection? (Art. 21 — absolute right)     │
    │  ✓ Automated profiling services detected?    │
    │  ✓ PII sent to US servers without SCCs?      │
    │                                              │
    │  Uses GPT-4o to write plain-English          │
    │  explanations and fix recommendations        │
    │  for each violation found.                   │
    │                                              │
    │  → Outputs: evidence_report.json             │
    └──────────────────────────────────────────────┘
                       │
                       ▼
    Results stream back to the React UI via SSE
    (GET /api/stream/{scan_id})
    Final report shown in the Violations table
```

---

## 🔌 API Endpoints (backend.py)

| Endpoint | Method | What it does |
|---|---|---|
| `/api/scan` | POST | Start a new scan, returns `scan_id` |
| `/api/stream/{scan_id}` | GET | Live log stream (Server-Sent Events) |
| `/api/status/{scan_id}` | GET | Check progress % of each tier |
| `/api/results/{scan_id}` | GET | Get the final `evidence_report.json` |
| `/api/download/{filename}` | GET | Download any output file |
| `/health` | GET | Check if backend is alive |

---

## 🗄️ rules.sql — The Legal Database

Contains **25 official rules** from CCPA and GDPR, each with:
- Rule ID (e.g. `CCPA-1798.120`, `GDPR-Art7.3`)
- Official section citation
- Full rule text
- Minimum and maximum fine amounts (in USD / EUR)

These are loaded into SQLite at scan time and matched against what was observed in Tier 2.

---

## ▶️ How to Run

### Step 1 — Set up Python environment (first time only)
```bash
cd apo_v2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Step 2 — Add API keys (optional but recommended)
```bash
cp .env.template .env
# Edit .env and add:
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
```
> Without API keys, the tool still works — it skips AI analysis but runs all rule-based checks.

### Step 3 — Start the backend
```bash
# Terminal 1
cd apo_v2
source venv/bin/activate
python backend.py
# → Running on http://localhost:8000
```

### Step 4 — Start the frontend
```bash
# Terminal 2
cd apo_v2/apo
npm install   # first time only
npm run dev
# → Running on http://localhost:5173
```

### Step 5 — Open the app
Go to **http://localhost:5173** in your browser, enter a URL, choose CCPA or GDPR, and click **Scan**.

---

### CLI mode (no UI needed)
```bash
cd apo_v2
source venv/bin/activate
python main.py --url https://www.example.com
python main.py --url https://www.example.com --skip-discovery  # reuse last crawl
```

---

## 📊 What the Evidence Report Contains

`output/evidence_report.json` is structured like this:

```json
{
  "report_metadata": { "target", "jurisdiction", "generated_at" },
  "session_summary": {
    "baseline":          { "pages_visited": 5, "tracker_count": 40 },
    "consent_accepted":  { "pages_visited": 5, "tracker_count": 43 },
    "consent_declined":  { "pages_visited": 5, "tracker_count": 38 },
    "compliance_gpc_on": { "pages_visited": 5, "tracker_count": 35 }
  },
  "gpc_verdict": { "verdict": "NON-COMPLIANT", "domains_ignoring_gpc": ["..."] },
  "violation_summary": {
    "total": 6,
    "severity_breakdown": { "HIGH": 4, "MEDIUM": 2, "LOW": 0 },
    "max_potential_penalty_usd": 150000
  },
  "violations": [
    {
      "rule_id": "CCPA-1798.135b",
      "section": "§1798.135(b)(1)",
      "violation_type": "GPC_NOT_HONORED",
      "severity": "HIGH",
      "evidence": { "tracker_domains": ["doubleclick.net", "..."] },
      "penalty_min_usd": 2500,
      "penalty_max_usd": 7500,
      "recommendation": "When Sec-GPC: 1 is received, stop all third-party tracker calls.",
      "llm_explanation": "Plain English explanation for non-lawyers...",
      "llm_technical_fix": "Exact code change engineers need to make..."
    }
  ]
}
```

---

## 🧠 AI Integration

| Where | Model | What it does |
|---|---|---|
| Tier 1 | Claude | Scores each crawled page for privacy risk (1–10), picks priority pages to visit next |
| Tier 2 | Claude | Plans which pages to focus the scan on; writes per-page compliance observations |
| Tier 3 | Claude | Reads the privacy policy and checks for required disclosures |
| Tier 3 | GPT-4o | Writes plain-English explanations and technical fix instructions for each violation |

If no API keys are provided, all AI steps are skipped and only the rule-based detectors run.

---

## ⚙️ Key Settings (core/config.py)

| Setting | Default | Description |
|---|---|---|
| `ROOT_URL` | set by UI | The website to scan |
| `JURISDICTION` | `CCPA` | Which law to check against (`CCPA` or `GDPR`) |
| `MAX_PAGES` | `10` | How many pages to crawl (UI slider × 5) |
| `HEADLESS` | `True` | Set `False` to watch the browser as it scans |
| `SCROLL_STEPS` | `3` | How many times to scroll per page (triggers lazy trackers) |
| `TEMPORAL_LEAK_MS` | `500` | Trackers firing within this many ms of page load = violation |
