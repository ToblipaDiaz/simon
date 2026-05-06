from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

from app.hl7.escape import compute_payload_sha256


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_hl7_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS hl7_message_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            encounter_id INTEGER,
            message_type TEXT NOT NULL,
            control_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            ack_payload TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            sent_at TEXT,
            acked_at TEXT,
            created_by_user_id INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_hl7_queue_encounter ON hl7_message_queue(encounter_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_hl7_queue_control ON hl7_message_queue(control_id);

        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            patient_id INTEGER,
            encounter_id INTEGER,
            ip_address TEXT,
            user_agent TEXT,
            metadata_json TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_audit_events_entity ON audit_events(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_audit_events_encounter ON audit_events(encounter_id, created_at);
        """
    )


def enqueue_message(
    conn: sqlite3.Connection,
    encounter_id: int,
    message_type: str,
    control_id: str,
    payload: str,
    created_by_user_id: Optional[int] = None,
    status: str = "DRAFT",
) -> int:
    ts = now_iso()
    cur = conn.execute(
        """
        INSERT INTO hl7_message_queue(encounter_id,message_type,control_id,payload,payload_sha256,status,created_at,updated_at,created_by_user_id)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (encounter_id, message_type, control_id, payload, compute_payload_sha256(payload), status, ts, ts, created_by_user_id),
    )
    return int(cur.lastrowid)


def update_message_status(
    conn: sqlite3.Connection,
    message_id: int,
    status: str,
    ack_payload: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    ts = now_iso()
    sent_at = ts if status == "SENT" else None
    acked_at = ts if status in {"ACKED", "NACKED"} else None
    conn.execute(
        """
        UPDATE hl7_message_queue
        SET status=?, ack_payload=COALESCE(?, ack_payload), error_message=?, updated_at=?,
            sent_at=COALESCE(?, sent_at), acked_at=COALESCE(?, acked_at)
        WHERE id=?
        """,
        (status, ack_payload, error_message, ts, sent_at, acked_at, message_id),
    )


def get_message(conn: sqlite3.Connection, message_id: int) -> Optional[Dict[str, Any]]:
    row = conn.execute("SELECT * FROM hl7_message_queue WHERE id=?", (message_id,)).fetchone()
    return dict(row) if row else None


def get_latest_message(conn: sqlite3.Connection, encounter_id: int) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM hl7_message_queue WHERE encounter_id=? ORDER BY id DESC LIMIT 1",
        (encounter_id,),
    ).fetchone()
    return dict(row) if row else None

