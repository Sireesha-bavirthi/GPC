"""
APO v2 — Core Configuration
All settings, API keys, and constants in one place.
Create a .env file in apo_v2/ with your keys:
    OPENAI_API_KEY=sk-...
    ANTHROPIC_API_KEY=sk-ant-...
"""

import os
from pathlib import Path

# ── Load .env if present ───────────────────────────────────────
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# ── API Keys ───────────────────────────────────────────────────
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")

# ── Target ─────────────────────────────────────────────────────
ROOT_URL           = "https://www.cpchem.com"
JURISDICTION       = "CCPA"          # "CCPA" or "GDPR"

# ── Output paths ───────────────────────────────────────────────
BASE_DIR           = Path(__file__).parent.parent
OUTPUT_DIR         = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

GRAPH_FILE             = OUTPUT_DIR / "interaction_graph.json"
TRAFFIC_BASELINE_FILE  = OUTPUT_DIR / "traffic_baseline.json"
TRAFFIC_COMPLIANCE_FILE= OUTPUT_DIR / "traffic_compliance.json"
SESSION_BASELINE_FILE  = OUTPUT_DIR / "session_state_baseline.json"
SESSION_COMPLIANCE_FILE= OUTPUT_DIR / "session_state_compliance.json"
COMPLIANCE_REPORT_FILE = OUTPUT_DIR / "compliance_report.json"
EVIDENCE_REPORT_FILE   = OUTPUT_DIR / "evidence_report.json"

RULES_SQL_FILE         = BASE_DIR / "rules.sql"

# ── Crawler (Tier 1) ────────────────────────────────────────────
MAX_PAGES          = 10             # max pages to crawl
SCROLL_STEPS       = 3             # scroll iterations per page
HEADLESS           = True          # False = watch browser live

# ── Interaction (Tier 2) ───────────────────────────────────────
MAX_JOURNEYS       = 20            # pages to visit per session
ACTION_DELAY_MS    = 800           # ms between actions
PAGE_LOAD_TIMEOUT  = 30_000        # ms
TEMPORAL_LEAK_MS   = 500           # tracker within 500ms = temporal leak

# ── GPC Signal ─────────────────────────────────────────────────
GPC_HEADER_KEY     = "Sec-GPC"
GPC_HEADER_VALUE   = "1"
GPC_JS_SCRIPT      = (
    "Object.defineProperty(navigator, 'globalPrivacyControl', "
    "{get: () => true, configurable: true});"
)

# ── Known Tracker Domains ──────────────────────────────────────
KNOWN_TRACKERS = [
    "google-analytics.com", "analytics.google.com",
    "googletagmanager.com", "segment.com",
    "mixpanel.com", "amplitude.com",
    "hotjar.com", "fullstory.com",
    "connect.facebook.net", "facebook.com",
    "doubleclick.net", "googlesyndication.com",
    "adservice.google.com", "advertising.com",
    "adsystem.amazon.com", "criteo.com",
    "taboola.com", "outbrain.com",
    "quantserve.com", "scorecardresearch.com",
    "bluekai.com", "krxd.net",
    "demdex.net", "rlcdn.com",
    "rubiconproject.com", "pubmatic.com",
    "openx.net", "bing.com", "bat.bing.com",
    "yandex.ru", "mc.yandex.ru",
    "linkedin.com", "px.ads.linkedin.com",
    "twitter.com", "analytics.twitter.com",
    "tiktok.com", "analytics.tiktok.com",
]

# ── PII Patterns ───────────────────────────────────────────────
PII_PATTERNS = {
    "email":        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "uid":          r"uid=[^&]+",
    "user_id":      r"user_id=[^&]+",
    "email_param":  r"email=[^&]+",
    "hashed_email": r"sha256=[a-f0-9]{64}",
    "ip_address":   r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    "phone":        r"phone=[^&]+",
    "name":         r"(first_name|last_name|fullname)=[^&]+",
}

# ── LLM Models ─────────────────────────────────────────────────
# Claude  : best for long document reading (privacy policy)
# GPT-4o  : best for structured JSON output (violation classification)
CLAUDE_MODEL   = "claude-3-5-haiku-20241022"
OPENAI_MODEL   = "gpt-4o"
LLM_MAX_TOKENS = 1500
