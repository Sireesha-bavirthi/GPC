# APO v2 — Autonomous Privacy Observability Platform

> **The Platform in one sentence:**
> A full-stack automated compliance engine that scans websites, simulates privacy decisions (Accept/Reject/GPC), and produces a legal evidence report with exact CCPA/GDPR violations—backed by a Cloud persistence layer (Supabase).

---

## 🏗️ Architecture: The 3-Tier Pipeline

APO v2 operates as a high-performance assembly line distributed across **FastAPI** (Logic) and **Supabase** (Persistence).

### 🛡️ Tier 1: Discovery Agent (The Map)
*   **Action:** Crawls the target URL to find all interactive nodes (links, forms, banners).
*   **AI Logic (Claude):** Assigns a **Privacy Risk Score (1-10)** to every page found.
*   **Persistence:** Saves the **Interaction Graph** to Supabase Storage.

### 🔬 Tier 2: Interaction Agent (The Capture)
*   **Action:** Launches **Parallel Browsers** (Playwright) to simulate different user personas:
    1.  **Baseline Session:** Acts as a standard user (No privacy signals).
    2.  **Compliance Session:** Acts as a "Hard Privacy" user (Injects GPC signal + clicks "Reject All").
*   **Observation:** Uses **mitmproxy** to capture deep network traffic and detect tracking pixels, XHR leaks, and temporal data escapes.
*   **Persistence:** Uploads raw traffic logs (`traffic_*.json`) and browser snapshots (`session_state_*.json`) to Supabase Storage.

### ⚖️ Tier 3: Observability Agent (The Verdict)
*   **Action:** Compares the Baseline vs. Compliance session data.
*   **Logic:** If a tracker fires in the "Privacy" session that was also in the "Baseline," it’s a high-confidence violation.
*   **AI Scoring (GPT-4o):** Matches findings against **rules.sql** (CCPA/GDPR sections) to generate legal explanations and penalty estimates.
*   **Persistence:** Writes structured findings to the `violations` table in Supabase.

---

## 🗄️ Persistence Layer: Supabase

APO v2 uses a hybrid storage model to ensure speed, searchability, and legal auditability.

### 1. Structured Data (Tables)
We use **PostgREST** (Supabase's auto-API) to drive the dashboard UI.
*   **`scans`:** Tracks every scan job, its URL, status, and progress.
*   **`scan_events`:** Powers the **Live Terminal** in the UI by storing second-by-second logs.
*   **`violations`:** Stores the final "crimes" found, including severity and estimated penalties.

### 2. Raw Evidence (Storage)
We use **Supabase Storage** for the "Legal proof."
*   **Folders by `scan_id`:** Every scan gets its own isolated folder.
*   **Files:** `evidence_report.json`, `traffic_baseline.json`, `interaction_graph.json`.
*   **Audit Trail:** These files are the "Digital Tapes" that can be downloaded for legal disputes.

---

## 🔌 API & Integration

### FastAPI Backend (`backend.py`)
| Endpoint | Method | Role |
|---|---|---|
| `/api/scan` | POST | Generates `scan_id`, starts browsers, and initializes Supabase records. |
| `/api/stream/{id}`| GET | Streams logs from memory/DB to the UI via Server-Sent Events (SSE). |
| `/api/results/{id}`| GET | Fetches the final AI-generated compliance verdict. |

### Supabase Cloud API (PostgREST)
You can hit the database directly for analytics (e.g., using Postman/Thunder Client):
*   **URL:** `https://[id].supabase.co/rest/v1/violations?scan_id=eq.[id]`
*   **Headers:** `apikey` and `Authorization: Bearer [token]`

---

## ▶️ Setup & Usage

### 1. Environment Configuration
Copy `.env.template` to `.env` and configure:
```env
# AI Keys
ANTHROPIC_API_KEY=sk-ant...
OPENAI_API_KEY=sk-proj...

# Supabase Keys (from Project Settings -> API)
SUPABASE_URL=https://your-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key  # Required for storage uploads
```

### 2. Starting the Platform
```bash
# Terminal 1: Backend
source venv/bin/activate
python backend.py

# Terminal 2: Frontend
cd apo && npm run dev
```

---

## 📊 Evaluation Logic (Simple Terms)
*   **"Is Tracker":** Domain matched against a blocklist of 12,000+ known ad-tech partners.
*   **"GPC Verdict":** Proves if GPC signals were ignored (Domain in Baseline AND Domain in Compliance = VIOLATION).
*   **"Penalty Calculation":** Sourced from the `rules.sql` local database citing exact CCPA (§1798.135) or GDPR (Art. 21) sections.
