"""Action queue: SQLite-backed assign/resolve state for exceptions."""
from __future__ import annotations

import json
import sqlite3
from typing import Any


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS action_queue (
            exception_id TEXT PRIMARY KEY,
            assigned_to TEXT NOT NULL,
            action_type TEXT NOT NULL,
            status TEXT DEFAULT 'assigned',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP NULL
        )
    """)
    conn.commit()


def assign_exception(conn: sqlite3.Connection, exception_id: str, assigned_to: str, action_type: str) -> None:
    # True UPSERT: update only assignment fields, preserve notes/created_at/resolved_at
    conn.execute(
        "INSERT INTO action_queue (exception_id, assigned_to, action_type, status) "
        "VALUES (?, ?, ?, 'assigned') "
        "ON CONFLICT(exception_id) DO UPDATE SET "
        "  assigned_to = excluded.assigned_to, "
        "  action_type = excluded.action_type, "
        "  status = 'assigned'",
        (exception_id, assigned_to, action_type),
    )
    conn.commit()


def resolve_exception(conn: sqlite3.Connection, exception_id: str, status: str, notes: str = "") -> None:
    conn.execute(
        "UPDATE action_queue SET status = ?, notes = ?, resolved_at = CURRENT_TIMESTAMP "
        "WHERE exception_id = ?",
        (status, notes, exception_id),
    )
    conn.commit()


def get_queue(conn: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
    if status:
        cursor = conn.execute(
            "SELECT exception_id, assigned_to, action_type, status, notes, created_at, resolved_at "
            "FROM action_queue WHERE status = ? ORDER BY created_at DESC",
            (status,),
        )
    else:
        cursor = conn.execute(
            "SELECT exception_id, assigned_to, action_type, status, notes, created_at, resolved_at "
            "FROM action_queue ORDER BY created_at DESC"
        )
    return [
        {
            "exception_id": row[0], "assigned_to": row[1], "action_type": row[2],
            "status": row[3], "notes": row[4], "created_at": row[5], "resolved_at": row[6],
        }
        for row in cursor.fetchall()
    ]
