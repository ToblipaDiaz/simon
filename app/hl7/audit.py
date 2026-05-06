from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, Optional

from app.hl7.escape import safe_log_metadata


def audit_event(
    conn: sqlite3.Connection,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    encounter_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    conn.execute(
        """
        INSERT INTO audit_events(user_id,action,entity_type,entity_id,patient_id,encounter_id,ip_address,user_agent,metadata_json,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        (
            user_id,
            action,
            entity_type,
            entity_id,
            patient_id,
            encounter_id,
            ip_address,
            user_agent,
            json.dumps(safe_log_metadata(metadata), ensure_ascii=False),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )

