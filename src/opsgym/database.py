from __future__ import annotations

import json
import sqlite3
from typing import Any


SCHEMA = """
CREATE TABLE accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    legal_name TEXT NOT NULL,
    tier TEXT NOT NULL,
    address TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    plan TEXT NOT NULL DEFAULT 'growth',
    scheduled_plan TEXT,
    plan_effective_date TEXT,
    renewal_date TEXT,
    owner_email TEXT,
    risk_level TEXT NOT NULL DEFAULT 'low'
);
CREATE TABLE contracts (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    legal_name TEXT NOT NULL,
    address TEXT NOT NULL,
    refund_limit REAL NOT NULL,
    notice_days INTEGER NOT NULL,
    sla_hours INTEGER NOT NULL,
    signed_at TEXT NOT NULL
);
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    status TEXT NOT NULL DEFAULT 'open',
    queue TEXT NOT NULL DEFAULT 'triage',
    note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    direction TEXT NOT NULL,
    sent_at TEXT NOT NULL DEFAULT '2026-08-23T09:00:00Z'
);
CREATE TABLE invoices (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    kind TEXT NOT NULL,
    period TEXT NOT NULL
);
CREATE TABLE credits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id TEXT NOT NULL,
    amount REAL NOT NULL,
    reason TEXT NOT NULL
);
CREATE TABLE incidents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    affected_account_ids TEXT NOT NULL,
    approved_message TEXT NOT NULL,
    eta TEXT
);
CREATE TABLE usage_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    period TEXT NOT NULL
);
CREATE TABLE calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attendees TEXT NOT NULL,
    event_time TEXT NOT NULL,
    subject TEXT NOT NULL
);
CREATE TABLE escalations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id TEXT NOT NULL,
    reason TEXT NOT NULL
);
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step INTEGER NOT NULL,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    ok INTEGER NOT NULL,
    result TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def rows(db: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in db.execute(sql, params).fetchall()]


def row(db: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    found = db.execute(sql, params).fetchone()
    return dict(found) if found else None


def log_action(
    db: sqlite3.Connection,
    step: int,
    tool: str,
    args: dict[str, Any],
    ok: bool,
    result: Any,
) -> None:
    db.execute(
        "INSERT INTO audit_log(step, tool, args, ok, result) VALUES (?, ?, ?, ?, ?)",
        (step, tool, json.dumps(args, sort_keys=True), int(ok), json.dumps(result, sort_keys=True)),
    )
    db.commit()

