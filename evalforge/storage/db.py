import json
import os
import sqlite3
from pathlib import Path
from threading import local
from typing import Any

_thread_local = local()

DEFAULT_DB_PATH = Path.home() / "evalforge_data" / "evalforge.db"


def get_db_path() -> Path:
    env_path = os.environ.get("EVALFORGE_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    if not hasattr(_thread_local, "conn") or _thread_local.conn is None:
        db_path = get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _thread_local.conn = sqlite3.connect(str(db_path))
        _thread_local.conn.row_factory = sqlite3.Row
        _thread_local.conn.execute("PRAGMA journal_mode=WAL")
    conn: sqlite3.Connection = _thread_local.conn  # type: ignore[assignment]
    return conn


def close_connection() -> None:
    if hasattr(_thread_local, "conn") and _thread_local.conn is not None:
        _thread_local.conn.close()
        _thread_local.conn = None


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_connection_dict() -> sqlite3.Connection:
    conn = get_connection()
    conn.row_factory = dict_factory  # type: ignore[assignment]
    return conn


def serialize(value: Any) -> str:
    return json.dumps(value, default=str)


def deserialize(value: str | None) -> Any:
    if value is None:
        return {}
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    tasks TEXT DEFAULT '[]',
    grading_type TEXT DEFAULT 'deterministic',
    judge_config TEXT,
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_definitions (
    id TEXT PRIMARY KEY,
    evaluation_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    instructions TEXT NOT NULL,
    success_criteria TEXT DEFAULT '[]',
    expected_output TEXT,
    max_steps INTEGER DEFAULT 50,
    max_tokens INTEGER DEFAULT 10000,
    timeout_seconds INTEGER DEFAULT 300,
    required_tools TEXT DEFAULT '[]',
    tags TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    evaluation_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    agent_config TEXT DEFAULT '{}',
    started_at TEXT,
    completed_at TEXT,
    seed INTEGER,
    env_snapshot TEXT DEFAULT '{}',
    metrics TEXT DEFAULT '{}',
    trace_id TEXT,
    diagnostics TEXT DEFAULT '[]',
    error_message TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS steps (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    step_type TEXT NOT NULL,
    content TEXT DEFAULT '',
    tool_name TEXT,
    tool_input TEXT,
    tool_output TEXT,
    token_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0.0,
    latency_ms REAL DEFAULT 0.0,
    state_snapshot TEXT,
    error_message TEXT,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS traces (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS diagnostics (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    category TEXT DEFAULT 'general',
    title TEXT DEFAULT '',
    description TEXT DEFAULT '',
    step_index INTEGER,
    recommendation TEXT DEFAULT '',
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_evaluation_id ON runs(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
CREATE INDEX IF NOT EXISTS idx_steps_run_id ON steps(run_id);
CREATE INDEX IF NOT EXISTS idx_diagnostics_run_id ON diagnostics(run_id);
CREATE INDEX IF NOT EXISTS idx_task_definitions_evaluation_id ON task_definitions(evaluation_id);
"""


def init_db() -> None:
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def reset_db() -> None:
    conn = get_connection()
    tables = ["diagnostics", "traces", "steps", "runs", "task_definitions", "evaluations"]
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    init_db()
