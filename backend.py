"""
APO v2 — FastAPI Backend
=========================
Exposes the APO v2 scan pipeline to the React frontend.

Endpoints:
  POST /api/scan            — start a new scan, returns {"scan_id": "..."}
  GET  /api/stream/{id}    — SSE stream of real-time agent log events
  GET  /api/results/{id}   — final evidence_report.json when complete
  GET  /api/download/{file} — serve output files for download
  GET  /api/status/{id}    — current agent phases + progress % (polling fallback)

CORS: http://localhost:5173 (Vite dev server)
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

# ── Supabase integration (non-blocking, optional) ─────────────────────────────
try:
    from core.supabase_store import (
        create_scan, update_scan_status,
        push_event as _sb_push_event, save_violations, upload_file, save_scan_result
    )
    SUPABASE_ENABLED = True
except Exception as _sb_err:
    SUPABASE_ENABLED = False
    print(f"[WARNING] Supabase not available: {_sb_err}")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
OUTPUT_DIR  = BASE_DIR / "output"
PROXY_ADDON = BASE_DIR / "proxy_addon.py"

OUTPUT_DIR.mkdir(exist_ok=True)

# ── In-memory scan registry ───────────────────────────────────────────────────
# scan_id → {"status": ..., "events": [...], "result": {...}}
SCANS: dict[str, dict] = {}

app = FastAPI(title="APO v2 Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ─────────────────────────────────────────────────────────────
class ScanRequest(BaseModel):
    url: str
    framework: str = "CCPA"
    crawl_depth: int = 3
    use_llm: bool = True
    claude_key: str = ""
    openai_key: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────
def _emit(scan_id: str, agent: str, level: str, msg: str):
    """Push a log event into the scan registry AND Supabase."""
    event = {
        "timestamp": time.strftime("%H:%M:%S"),
        "agent": agent,
        "level": level,
        "msg": msg,
    }
    SCANS[scan_id]["events"].append(event)
    if SUPABASE_ENABLED:
        try:
            _sb_push_event(scan_id, agent, level, msg)
        except Exception:
            pass


def _set_phase(scan_id: str, phase: str, progress: int):
    SCANS[scan_id]["phase"] = phase
    SCANS[scan_id]["progress"][phase] = progress
    if SUPABASE_ENABLED:
        try:
            update_scan_status(
                scan_id, SCANS[scan_id]["status"],
                phase=phase, progress=SCANS[scan_id]["progress"]
            )
        except Exception:
            pass


# ── Background scan runner ─────────────────────────────────────────────────────
def _run_scan(scan_id: str, req: ScanRequest):
    """
    Runs the full 3-tier APO pipeline inside a background thread.
    Streams live updates into SCANS[scan_id]["events"].
    """
    import importlib, sys as _sys

    scan = SCANS[scan_id]
    scan["status"] = "running"

    # Override env with user-supplied keys if provided
    if req.claude_key:
        os.environ["ANTHROPIC_API_KEY"] = req.claude_key
    if req.openai_key:
        os.environ["OPENAI_API_KEY"] = req.openai_key

    apo_path = str(BASE_DIR)
    if apo_path not in _sys.path:
        _sys.path.insert(0, apo_path)

    try:
        # ── Apply UI config to core.config ──────────────────────────────
        import core.config as cfg

        # Map UI framework string → valid jurisdiction key (default CCPA)
        FRAMEWORK_MAP = {
            "CCPA": "CCPA", "GDPR": "GDPR", "LGPD": "LGPD",
            "PIPEDA": "PIPEDA", "POPIA": "POPIA",
        }
        jurisdiction = FRAMEWORK_MAP.get(req.framework.upper(), "CCPA")

        cfg.ROOT_URL     = req.url
        cfg.JURISDICTION = jurisdiction
        cfg.MAX_PAGES    = req.crawl_depth * 5   # crawl_depth slider → max pages
        # Also update API keys on cfg so Tier 3 sees them
        if req.claude_key:
            cfg.ANTHROPIC_API_KEY = req.claude_key
        if req.openai_key:
            cfg.OPENAI_API_KEY    = req.openai_key

        _emit(scan_id, "discovery", "INFO",
              f"Config applied — URL: {cfg.ROOT_URL}  Jurisdiction: {cfg.JURISDICTION}  Max pages: {cfg.MAX_PAGES}")


        from agents.tier1_discovery import run_discovery_agent
        _emit(scan_id, "discovery", "INFO", "Playwright launching browser...")
        _set_phase(scan_id, "discovery", 20)

        import asyncio as _aio
        graph = _aio.run(run_discovery_agent())
        pages = len(graph.get("interaction_graph", {}).get("nodes", [])) if isinstance(graph, dict) else 0
        _emit(scan_id, "discovery", "SUCCESS", f"Discovery complete — {pages} pages mapped")
        _set_phase(scan_id, "discovery", 100)

        # ── TIER 2: Interaction ─────────────────────────────────────────────
        _emit(scan_id, "interaction", "INFO", "Launching parallel GPC sessions (baseline + compliance)")
        _set_phase(scan_id, "interaction", 10)

        # Start mitmproxy as subprocess for proxy capture
        proxy_port = 18080
        proxy_proc = None
        try:
            proxy_proc = subprocess.Popen(
                [
                    _sys.executable, "-m", "mitmproxy",
                    "--listen-port", str(proxy_port),
                    "--mode", "regular",
                    "-s", str(PROXY_ADDON),
                    "--quiet",
                ],
                cwd=str(BASE_DIR),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _emit(scan_id, "interaction", "INFO", f"mitmproxy started on port {proxy_port}")
            time.sleep(2)   # give proxy time to bind
        except Exception as px_err:
            _emit(scan_id, "interaction", "WARNING", f"mitmproxy unavailable: {px_err} — continuing without proxy")
            proxy_proc = None

        try:
            from agents.tier2_interaction import run_interaction_agent
            _emit(scan_id, "interaction", "INFO", "Claude planning session actions...")
            _set_phase(scan_id, "interaction", 35)
            session_results = _aio.run(run_interaction_agent(graph))
            _emit(scan_id, "interaction", "SUCCESS", "Both sessions complete — traffic captured")
            _set_phase(scan_id, "interaction", 100)
        finally:
            if proxy_proc:
                proxy_proc.terminate()
                _emit(scan_id, "interaction", "INFO", "mitmproxy proxy stopped")

        # ── TIER 3: Observability ───────────────────────────────────────────
        _emit(scan_id, "observability", "INFO", f"Loading {cfg.JURISDICTION} rules from rules.sql")
        _set_phase(scan_id, "observability", 15)

        from agents.tier3_observability import run_observability_agent

        # Enrich with proxy traffic if captured
        proxy_traffic_file = OUTPUT_DIR / "raw_traffic_proxy.jsonl"
        proxy_records = []
        if proxy_traffic_file.exists():
            with open(proxy_traffic_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        proxy_records.append(json.loads(line))
            _emit(scan_id, "observability", "INFO",
                  f"Loaded {len(proxy_records)} proxy-captured records (richer evidence)")
            # Inject into session_results for Tier3 analysis
            session_results["proxy_traffic"] = proxy_records

        _set_phase(scan_id, "observability", 40)
        _emit(scan_id, "observability", "INFO", "Running rule detectors...")

        # Get privacy policy text from interaction results if available
        policy_text = session_results.get("privacy_policy_text", "")

        report = run_observability_agent(session_results, policy_text)
        violations = report.get("violations", [])

        _emit(scan_id, "observability", "SUCCESS",
              f"Evidence report done — {len(violations)} violations | "
              f"max fine ${report.get('violation_summary',{}).get('max_potential_penalty_usd',0):,}")
        _set_phase(scan_id, "observability", 100)

        scan["result"] = report
        scan["status"] = "complete"

        # ── Push everything to Supabase ──────────────────────────────
        if SUPABASE_ENABLED:
            try:
                save_violations(scan_id, violations)
                upload_file(scan_id, "evidence_report.json", report)
                baseline_log = session_results.get("baseline", {}).get("traffic_log", [])
                compliance_log = session_results.get("compliance", {}).get("traffic_log", [])
                upload_file(scan_id, "traffic_baseline.json", baseline_log)
                upload_file(scan_id, "traffic_compliance.json", compliance_log)
                save_scan_result(scan_id, report)
            except Exception as sb_err:
                print(f"[Supabase] post-scan upload error: {sb_err}")

    except Exception as exc:
        _emit(scan_id, "observability", "ERROR", f"Pipeline error: {exc}")
        scan["status"] = "error"
        scan["error"] = str(exc)
        import traceback
        traceback.print_exc()


# ── API routes ─────────────────────────────────────────────────────────────────
@app.post("/api/scan")
def start_scan(req: ScanRequest, background_tasks: BackgroundTasks):
    scan_id = str(uuid.uuid4())[:8]
    SCANS[scan_id] = {
        "status": "pending",
        "events": [],
        "result": None,
        "error": None,
        "phase": "idle",
        "progress": {"discovery": 0, "interaction": 0, "observability": 0},
        "request": req.model_dump(),
    }
    # Persist to Supabase
    if SUPABASE_ENABLED:
        try:
            create_scan(scan_id, req.url, req.framework)
        except Exception as e:
            print(f"[Supabase] create_scan failed: {e}")
    background_tasks.add_task(_run_scan, scan_id, req)
    return {"scan_id": scan_id}


@app.get("/api/status/{scan_id}")
def get_status(scan_id: str):
    if scan_id not in SCANS:
        raise HTTPException(404, "Scan not found")
    scan = SCANS[scan_id]
    return {
        "scan_id": scan_id,
        "status": scan["status"],
        "phase": scan["phase"],
        "progress": scan["progress"],
        "event_count": len(scan["events"]),
        "error": scan.get("error"),
    }


@app.get("/api/stream/{scan_id}")
async def stream_events(scan_id: str):
    """Server-Sent Events — streams log lines as they arrive."""
    if scan_id not in SCANS:
        raise HTTPException(404, "Scan not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        sent = 0
        scan = SCANS[scan_id]
        while True:
            events = scan["events"]
            while sent < len(events):
                ev = events[sent]
                sent += 1
                yield f"data: {json.dumps(ev)}\n\n"
            if scan["status"] in ("complete", "error"):
                # Flush remaining
                while sent < len(scan["events"]):
                    ev = scan["events"][sent]
                    sent += 1
                    yield f"data: {json.dumps(ev)}\n\n"
                # Send terminal event
                yield f"data: {json.dumps({'agent':'system','level':'DONE','msg':scan['status'],'timestamp':''})}\n\n"
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/results/{scan_id}")
def get_results(scan_id: str):
    if scan_id not in SCANS:
        raise HTTPException(404, "Scan not found")
    scan = SCANS[scan_id]
    if scan["status"] != "complete":
        raise HTTPException(425, "Scan not complete yet")
    return scan["result"]


@app.get("/api/download/{filename}")
def download_file(filename: str):
    # Security: only allow known output files
    allowed = {
        "evidence_report.json",
        "traffic_baseline.json",
        "traffic_compliance.json",
        "interaction_graph.json",
        "session_state_baseline.json",
        "session_state_compliance.json",
        "raw_traffic_proxy.jsonl",
    }
    if filename not in allowed:
        raise HTTPException(403, "Not allowed")
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(path, filename=filename)


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0"}


if __name__ == "__main__":
    print("Starting APO v2 Backend on http://localhost:8000")
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
