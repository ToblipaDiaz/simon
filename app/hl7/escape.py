from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict


def hl7_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("\\", r"\\E\\")
        .replace("|", r"\\F\\")
        .replace("^", r"\\S\\")
        .replace("&", r"\\T\\")
        .replace("~", r"\\R\\")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def compute_payload_sha256(payload: str) -> str:
    return hashlib.sha256((payload or "").encode("utf-8")).hexdigest()


def redact_patient_identifiers(text: str) -> str:
    if not text:
        return ""
    redacted = str(text)
    redacted = re.sub(r"\b\d{7,8}-?[\dkK]\b", "[RUN_REDACTED]", redacted)
    redacted = re.sub(r"\b\+?56\s?9?\s?\d{4}\s?\d{4}\b", "[PHONE_REDACTED]", redacted)
    redacted = re.sub(r"\b\d{8,12}\b", "[ID_REDACTED]", redacted)
    redacted = re.sub(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", r"\1***\2", redacted)
    return redacted


def safe_log_metadata(metadata: Dict[str, Any] | None) -> Dict[str, Any]:
    safe: Dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        key_l = str(key).lower()
        if any(term in key_l for term in ["payload", "transcript", "note", "run", "phone", "token", "password"]):
            safe[key] = "[REDACTED]"
        elif isinstance(value, (dict, list)):
            safe[key] = json.loads(redact_patient_identifiers(json.dumps(value, ensure_ascii=False)))
        else:
            safe[key] = redact_patient_identifiers(str(value))
    return safe


def prevent_phi_in_logs(text: str, max_len: int = 180) -> str:
    redacted = redact_patient_identifiers(text or "")
    if len(redacted) > max_len:
        return redacted[:max_len] + "...[TRUNCATED]"
    return redacted

