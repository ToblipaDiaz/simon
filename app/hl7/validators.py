from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.hl7.config import HL7Settings


class HL7ValidationError(ValueError):
    pass


@dataclass
class ACKResult:
    status: str
    control_id: str = ""
    text: str = ""
    is_ack: bool = False
    is_nack: bool = False


def _segments(message: str) -> List[List[str]]:
    return [segment.split("|") for segment in (message or "").replace("\n", "\r").split("\r") if segment.strip()]


def _segment_names(message: str) -> set[str]:
    return {parts[0] for parts in _segments(message) if parts}


def get_control_id(message: str) -> str:
    for parts in _segments(message):
        if parts and parts[0] == "MSH" and len(parts) > 9:
            return parts[9]
    return ""


def _patient_identifier_present(message: str) -> bool:
    for parts in _segments(message):
        if parts and parts[0] == "PID":
            pid3 = parts[3] if len(parts) > 3 else ""
            pid18 = parts[18] if len(parts) > 18 else ""
            return bool((pid3 or pid18).strip())
    return False


def validate_message_ready(
    payload: str,
    message_type: str,
    settings: Optional[HL7Settings] = None,
    note_text: Optional[str] = None,
    physician_reviewed: bool = False,
) -> str:
    settings = settings or HL7Settings.from_env()
    names = _segment_names(payload)
    if "MSH" not in names:
        raise HL7ValidationError("MSH es obligatorio.")
    if "PID" not in names:
        raise HL7ValidationError("PID es obligatorio.")
    if message_type in {"ADT_A04", "MDM_T02", "ORU_R01"} and "PV1" not in names:
        raise HL7ValidationError("PV1 es obligatorio para ADT/MDM/ORU.")
    if message_type == "MDM_T02" and "TXA" not in names:
        raise HL7ValidationError("TXA es obligatorio para MDM.")
    control_id = get_control_id(payload)
    if not control_id:
        raise HL7ValidationError("MSH-10 control_id es obligatorio.")
    if settings.require_patient_identifier and not _patient_identifier_present(payload):
        raise HL7ValidationError("Identificador de paciente obligatorio ausente.")
    if message_type == "MDM_T02" and not (note_text or "").strip():
        raise HL7ValidationError("note_text es obligatorio para MDM.")
    if settings.require_review and not physician_reviewed:
        raise HL7ValidationError("La nota debe estar revisada por medico antes de quedar READY/SENT.")
    return control_id


def extract_msa_status(message: str) -> str:
    for parts in _segments(message):
        if parts and parts[0] == "MSA" and len(parts) > 1:
            return parts[1].strip().upper()
    return ""


def parse_ack(message: str) -> ACKResult:
    status = extract_msa_status(message)
    control_id = ""
    text = ""
    for parts in _segments(message):
        if parts and parts[0] == "MSA":
            control_id = parts[2] if len(parts) > 2 else ""
            text = parts[3] if len(parts) > 3 else ""
            break
    return ACKResult(status=status, control_id=control_id, text=text, is_ack=status == "AA", is_nack=status in {"AE", "AR"})

