-- ============================================================
-- APO v2 — Supabase Database Schema
-- Run this ONCE in your Supabase project's SQL Editor:
-- Dashboard → SQL Editor → New Query → paste this → Run
-- ============================================================


-- 1. SCANS TABLE
-- Tracks every scan run by any user
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scans (
    scan_id     TEXT        PRIMARY KEY,
    status      TEXT        NOT NULL DEFAULT 'pending',
    phase       TEXT        NOT NULL DEFAULT 'idle',
    url         TEXT        NOT NULL,
    framework   TEXT        NOT NULL DEFAULT 'CCPA',
    progress    JSONB       NOT NULL DEFAULT '{"discovery": 0, "interaction": 0, "observability": 0}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update updated_at on any row change
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER scans_updated_at
BEFORE UPDATE ON scans
FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- 2. SCAN EVENTS TABLE
-- Stores live log lines streamed during a scan
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS scan_events (
    id          BIGSERIAL   PRIMARY KEY,
    scan_id     TEXT        NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    timestamp   TEXT,
    agent       TEXT,           -- 'discovery' | 'interaction' | 'observability'
    level       TEXT,           -- 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR'
    msg         TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookup of events for a specific scan
CREATE INDEX IF NOT EXISTS idx_scan_events_scan_id ON scan_events(scan_id);


-- 3. VIOLATIONS TABLE
-- One row per detected compliance violation
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS violations (
    id                  BIGSERIAL   PRIMARY KEY,
    scan_id             TEXT        NOT NULL REFERENCES scans(scan_id) ON DELETE CASCADE,
    rule_id             TEXT,           -- e.g. 'CCPA-1798.135b'
    section             TEXT,           -- e.g. '§1798.135(b)(1)'
    violation_type      TEXT,           -- e.g. 'GPC_NOT_HONORED'
    severity            TEXT,           -- 'HIGH' | 'MEDIUM' | 'LOW'
    penalty_min_usd     INT,
    penalty_max_usd     INT,
    evidence            JSONB,          -- full evidence dict
    recommendation      TEXT,
    llm_explanation     TEXT,           -- plain-English explanation
    llm_technical_fix   TEXT,           -- engineering fix
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for fast lookup per scan
CREATE INDEX IF NOT EXISTS idx_violations_scan_id ON violations(scan_id);
-- Index for filtering by severity
CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity);


-- ============================================================
-- Storage bucket: create manually in Supabase Dashboard
-- Storage → New Bucket → Name: apo-reports → Public: ON
-- ============================================================

-- Files uploaded per scan:
--   {scan_id}/evidence_report.json
--   {scan_id}/traffic_baseline.json
--   {scan_id}/traffic_compliance.json

-- ============================================================
-- Optional: Row Level Security (enable once you add auth)
-- ============================================================

-- ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE violations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scan_events ENABLE ROW LEVEL SECURITY;

-- (Add policies per user_id once Supabase Auth is integrated)
