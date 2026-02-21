"""
APO v2 — Rules DB
Loads rules.sql into in-memory SQLite and exposes query helpers.
"""

import sqlite3
import re
from pathlib import Path


def load_rules_db(sql_file: Path) -> sqlite3.Connection:
    """
    Parse rules.sql → execute CREATE TABLE + INSERT statements
    into an in-memory SQLite database.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    sql_text = Path(sql_file).read_text()
    # Strip SQL comments
    clean = re.sub(r'--[^\n]*', '', sql_text)
    # Execute only DDL/DML
    for stmt in clean.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        keyword = stmt.split()[0].upper() if stmt.split() else ""
        if keyword in ("CREATE", "INSERT", "ALTER", "DROP"):
            try:
                conn.execute(stmt)
            except sqlite3.Error:
                pass
    conn.commit()
    return conn


def fetch_rules(conn: sqlite3.Connection, regulation_id: str) -> list[dict]:
    """Return all rules for CCPA or GDPR."""
    cur = conn.execute(
        """SELECT rule_id, section_citation, rule_title,
                  rule_text, violation_penalty_min, violation_penalty_max
           FROM compliance_rules WHERE regulation_id = ?""",
        (regulation_id,)
    )
    return [dict(row) for row in cur.fetchall()]


def get_rule(conn: sqlite3.Connection, rule_id: str) -> dict | None:
    """Fetch a single rule by its ID."""
    cur = conn.execute(
        "SELECT * FROM compliance_rules WHERE rule_id = ?", (rule_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def list_all_rules(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.execute("SELECT rule_id, regulation_id, rule_title FROM compliance_rules")
    return [dict(row) for row in cur.fetchall()]
