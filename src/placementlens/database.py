"""Small SQLite persistence layer used by the Streamlit interface."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "database" / "placementlens.db"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialise() -> None:
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS workspaces (id INTEGER PRIMARY KEY, name TEXT UNIQUE, created_at TEXT);
        CREATE TABLE IF NOT EXISTS source_files (id INTEGER PRIMARY KEY, name TEXT, path TEXT, file_type TEXT,
            imported_at TEXT, is_synthetic INTEGER DEFAULT 0, notes TEXT);
        CREATE TABLE IF NOT EXISTS dataset_versions (id INTEGER PRIMARY KEY, source_id INTEGER, label TEXT,
            created_at TEXT, record_count INTEGER, mapping_json TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS placement_records (id INTEGER PRIMARY KEY, version_id INTEGER, record_json TEXT);
        CREATE TABLE IF NOT EXISTS validation_issues (id INTEGER PRIMARY KEY, version_id INTEGER, severity TEXT,
            field TEXT, message TEXT, row_number INTEGER);
        CREATE TABLE IF NOT EXISTS source_claims (id INTEGER PRIMARY KEY, version_id INTEGER, field TEXT,
            source_note TEXT, reliability TEXT);
        CREATE TABLE IF NOT EXISTS aggregate_metrics (id INTEGER PRIMARY KEY, version_id INTEGER, metric TEXT,
            value TEXT, calculated_at TEXT);
        CREATE TABLE IF NOT EXISTS analysis_history (id INTEGER PRIMARY KEY, page TEXT, version_id INTEGER, viewed_at TEXT);
        CREATE TABLE IF NOT EXISTS report_history (id INTEGER PRIMARY KEY, version_id INTEGER, name TEXT,
            path TEXT, created_at TEXT, format TEXT);
        """)
        conn.execute("INSERT OR IGNORE INTO workspaces(name, created_at) VALUES (?, ?)",
                     ("College Analysis", now()))


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def save_dataset(df: pd.DataFrame, name: str, mapping: dict, issues: list[dict], *, synthetic: bool = False,
                 notes: str = "") -> int:
    """Store each import as a new immutable dataset version."""
    with connect() as conn:
        source = conn.execute("INSERT INTO source_files(name, path, file_type, imported_at, is_synthetic, notes) VALUES(?,?,?,?,?,?)",
            (name, "Synthetic demonstration data" if synthetic else f"data/imports/{name}", Path(name).suffix, now(), int(synthetic), notes))
        version = conn.execute("INSERT INTO dataset_versions(source_id,label,created_at,record_count,mapping_json,notes) VALUES(?,?,?,?,?,?)",
            (source.lastrowid, name, now(), len(df), json.dumps(mapping), notes))
        version_id = version.lastrowid
        rows = [(version_id, json.dumps(row, default=str)) for row in df.where(pd.notna(df), None).to_dict("records")]
        conn.executemany("INSERT INTO placement_records(version_id,record_json) VALUES(?,?)", rows)
        conn.executemany("INSERT INTO validation_issues(version_id,severity,field,message,row_number) VALUES(?,?,?,?,?)",
            [(version_id, x["severity"], x["field"], x["message"], x.get("row", 0)) for x in issues])
        return version_id


def versions() -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query("""SELECT v.id, v.label, v.created_at, v.record_count, v.notes,
            s.is_synthetic FROM dataset_versions v JOIN source_files s ON s.id=v.source_id ORDER BY v.id DESC""", conn)


def load_dataset(version_id: int | None = None) -> pd.DataFrame:
    if version_id is None:
        values = versions()
        if values.empty: return pd.DataFrame()
        version_id = int(values.iloc[0].id)
    with connect() as conn:
        rows = conn.execute("SELECT record_json FROM placement_records WHERE version_id=?", (version_id,)).fetchall()
    return pd.DataFrame([json.loads(r[0]) for r in rows])


def issues_for(version_id: int) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query("SELECT severity, field, message, row_number FROM validation_issues WHERE version_id=?", conn, params=(version_id,))


def log_report(version_id: int, name: str, path: str, fmt: str) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO report_history(version_id,name,path,created_at,format) VALUES(?,?,?,?,?)", (version_id,name,path,now(),fmt))


def report_history() -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query("SELECT name,created_at,format,path FROM report_history ORDER BY id DESC", conn)

def add_source_claim(version_id: int, field: str, source_note: str, reliability: str) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO source_claims(version_id,field,source_note,reliability) VALUES(?,?,?,?)",(version_id,field,source_note,reliability))

def source_claims(version_id: int) -> pd.DataFrame:
    with connect() as conn:
        return pd.read_sql_query("SELECT field,source_note,reliability FROM source_claims WHERE version_id=? ORDER BY id DESC",conn,params=(version_id,))
