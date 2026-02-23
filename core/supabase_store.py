"""
APO v2 — Supabase Storage Helper
==================================
Central module for all Supabase interactions:
  • DB  — scans table, violations table, events table
  • Storage — traffic JSON, session JSON, evidence report

Required Supabase tables (run schema.sql once in Supabase SQL editor):
  CREATE TABLE scans (
      scan_id TEXT PRIMARY KEY,
      status TEXT,
      phase TEXT,
      url TEXT,
      framework TEXT,
      progress JSONB DEFAULT '{}',
      created_at TIMESTAMPTZ DEFAULT NOW(),
      updated_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE TABLE scan_events (
      id BIGSERIAL PRIMARY KEY,
      scan_id TEXT REFERENCES scans(scan_id),
      timestamp TEXT,
      agent TEXT,
      level TEXT,
      msg TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );

  CREATE TABLE violations (
      id BIGSERIAL PRIMARY KEY,
      scan_id TEXT REFERENCES scans(scan_id),
      rule_id TEXT,
      section TEXT,
      violation_type TEXT,
      severity TEXT,
      penalty_min_usd INT,
      penalty_max_usd INT,
      evidence JSONB,
      recommendation TEXT,
      llm_explanation TEXT,
      llm_technical_fix TEXT,
      created_at TIMESTAMPTZ DEFAULT NOW()
  );

Storage bucket: create a bucket called 'apo-reports' in Supabase dashboard.
"""

import json
import time
from core.supabase_client import supabase


# ─────────────────────────────────────────────────────────────────
# SCANS TABLE
# ─────────────────────────────────────────────────────────────────

def create_scan(scan_id: str, url: str, framework: str):
    """Insert a new scan record when a scan starts."""
    try:
        supabase.table("scans").insert({
            "scan_id":   scan_id,
            "status":    "pending",
            "phase":     "idle",
            "url":       url,
            "framework": framework,
            "progress":  {"discovery": 0, "interaction": 0, "observability": 0},
        }).execute()
        print(f"  [Supabase] Scan {scan_id} created in DB")
    except Exception as e:
        print(f"  [Supabase] create_scan error: {e}")


def update_scan_status(scan_id: str, status: str, phase: str = None,
                        progress: dict = None):
    """Update scan status, phase, and progress."""
    try:
        data = {"status": status, "updated_at": "now()"}
        if phase:
            data["phase"] = phase
        if progress:
            data["progress"] = progress
        supabase.table("scans").update(data).eq("scan_id", scan_id).execute()
    except Exception as e:
        print(f"  [Supabase] update_scan_status error: {e}")


def save_scan_result(scan_id: str, report: dict):
    """Save final summary stats when scan completes."""
    try:
        vs = report.get("violation_summary", {})
        supabase.table("scans").update({
            "status": "complete",
            "phase": "done",
            "progress": {"discovery": 100, "interaction": 100, "observability": 100},
            "updated_at": "now()",
        }).eq("scan_id", scan_id).execute()
        print(f"  [Supabase] Scan {scan_id} marked complete")
    except Exception as e:
        print(f"  [Supabase] save_scan_result error: {e}")


# ─────────────────────────────────────────────────────────────────
# SCAN EVENTS TABLE  (live log streaming)
# ─────────────────────────────────────────────────────────────────

def push_event(scan_id: str, agent: str, level: str, msg: str):
    """Push a live log event to Supabase (used alongside SSE)."""
    try:
        supabase.table("scan_events").insert({
            "scan_id":   scan_id,
            "timestamp": time.strftime("%H:%M:%S"),
            "agent":     agent,
            "level":     level,
            "msg":       msg,
        }).execute()
    except Exception as e:
        print(f"  [Supabase] push_event error: {e}")


# ─────────────────────────────────────────────────────────────────
# VIOLATIONS TABLE
# ─────────────────────────────────────────────────────────────────

def save_violations(scan_id: str, violations: list):
    """Insert each violation as a separate row for easy querying."""
    if not violations:
        return
    try:
        rows = []
        for v in violations:
            rows.append({
                "scan_id":          scan_id,
                "rule_id":          v.get("rule_id", ""),
                "section":          v.get("section", ""),
                "violation_type":   v.get("violation_type", ""),
                "severity":         v.get("severity", "LOW"),
                "penalty_min_usd":  v.get("penalty_min_usd") or 0,
                "penalty_max_usd":  v.get("penalty_max_usd") or 0,
                "evidence":         v.get("evidence", {}),
                "recommendation":   v.get("recommendation", ""),
                "llm_explanation":  v.get("llm_explanation", ""),
                "llm_technical_fix":v.get("llm_technical_fix", ""),
            })
        supabase.table("violations").insert(rows).execute()
        print(f"  [Supabase] {len(rows)} violations saved to DB")
    except Exception as e:
        print(f"  [Supabase] save_violations error: {e}")


# ─────────────────────────────────────────────────────────────────
# STORAGE — upload output files
# ─────────────────────────────────────────────────────────────────

BUCKET = "apo-reports"


def upload_file(scan_id: str, filename: str, data: dict | list | str):
    """
    Upload any JSON output file to Supabase Storage.
    Path inside bucket: {scan_id}/{filename}
    """
    try:
        if isinstance(data, (dict, list)):
            content = json.dumps(data, indent=2).encode("utf-8")
        else:
            content = data.encode("utf-8") if isinstance(data, str) else data

        path = f"{scan_id}/{filename}"
        # upsert=True overwrites if file already exists
        supabase.storage.from_(BUCKET).upload(
            path, content,
            file_options={"content-type": "application/json", "upsert": "true"}
        )
        print(f"  [Supabase Storage] Uploaded {filename} → {BUCKET}/{path}")
        return get_public_url(scan_id, filename)
    except Exception as e:
        print(f"  [Supabase Storage] upload error for {filename}: {e}")
        return None


def get_public_url(scan_id: str, filename: str) -> str:
    """Get the public download URL of an uploaded file."""
    try:
        path = f"{scan_id}/{filename}"
        res = supabase.storage.from_(BUCKET).get_public_url(path)
        return res
    except Exception:
        return ""
