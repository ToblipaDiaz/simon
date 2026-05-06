from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from app.hl7.config import HL7Settings
from app.hl7.escape import hl7_escape


def hl7_ts(dt: Optional[datetime] = None) -> str:
    return (dt or datetime.now()).strftime("%Y%m%d%H%M%S")


def make_control_id(prefix: str, encounter_id: Any) -> str:
    return f"AS{prefix}{encounter_id or 'X'}{int(time.time())}"


def _patient_identifier(patient: Dict[str, Any]) -> str:
    return str(patient.get("mrn") or patient.get("patient_id") or patient.get("document_number") or "")


def patient_hl7_name(patient: Dict[str, Any]) -> str:
    last = hl7_escape(patient.get("last_name"))
    first = hl7_escape(patient.get("first_name"))
    return f"{last}^{first}"


def patient_birthdate_hl7(patient: Dict[str, Any]) -> str:
    bd = str(patient.get("birth_date") or "")
    if not bd:
        return ""
    try:
        return datetime.strptime(bd, "%Y-%m-%d").strftime("%Y%m%d")
    except ValueError:
        return bd.replace("-", "")


def _msh(message_code: str, control_id: str, settings: HL7Settings) -> str:
    return "|".join(
        [
            "MSH",
            "^~\\&",
            hl7_escape(settings.sending_app),
            hl7_escape(settings.sending_facility),
            hl7_escape(settings.receiving_app),
            hl7_escape(settings.receiving_facility),
            hl7_ts(),
            "",
            message_code,
            hl7_escape(control_id),
            "P",
            hl7_escape(settings.version),
        ]
    )


def _pid(patient: Dict[str, Any]) -> str:
    return "|".join(
        [
            "PID",
            "1",
            "",
            hl7_escape(_patient_identifier(patient)),
            "",
            patient_hl7_name(patient),
            "",
            patient_birthdate_hl7(patient),
            hl7_escape(patient.get("sex")),
            "",
            "",
            hl7_escape(patient.get("address")),
            "",
            hl7_escape(patient.get("phone")),
            "",
            "",
            "",
            "",
            hl7_escape(patient.get("national_id") or patient.get("document_number")),
        ]
    )


def _pv1(encounter: Dict[str, Any]) -> str:
    return "|".join(
        [
            "PV1",
            "1",
            "O",
            "AMBULATORIO",
            "",
            "",
            "",
            hl7_escape(encounter.get("provider_name")),
            "",
            "",
            hl7_escape(encounter.get("specialty") or "NEUROPED"),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            hl7_escape(str(encounter.get("id") or encounter.get("encounter_id") or "")),
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            hl7_ts(),
        ]
    )


def split_obx_text(text: str, chunk_size: int = 180) -> List[str]:
    clean = str(text or "").strip()
    chunks: List[str] = []
    cur = ""
    for word in clean.split():
        if len(cur) + len(word) + 1 > chunk_size:
            if cur:
                chunks.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        chunks.append(cur)
    return chunks


def _records(rows: Any) -> Iterable[Dict[str, Any]]:
    if rows is None:
        return []
    if hasattr(rows, "to_dict"):
        return rows.to_dict("records")
    return rows


def build_adt_a04(
    patient: Dict[str, Any],
    encounter: Dict[str, Any],
    settings: Optional[HL7Settings] = None,
    control_id: Optional[str] = None,
) -> str:
    settings = settings or HL7Settings.from_env()
    control_id = control_id or make_control_id("ADT", encounter.get("id") or encounter.get("encounter_id"))
    segments = [
        _msh("ADT^A04^ADT_A01", control_id, settings),
        f"EVN|A04|{hl7_ts()}",
        _pid(patient),
        _pv1(encounter),
    ]
    return "\r".join(segments) + "\r"


def build_mdm_t02(
    patient: Dict[str, Any],
    encounter: Dict[str, Any],
    diagnoses: Any = None,
    settings: Optional[HL7Settings] = None,
    control_id: Optional[str] = None,
    note_text: Optional[str] = None,
) -> str:
    settings = settings or HL7Settings.from_env()
    control_id = control_id or make_control_id("MDM", encounter.get("id") or encounter.get("encounter_id"))
    note = str(note_text if note_text is not None else encounter.get("note_text") or "")
    txa_status = "AV" if encounter.get("physician_reviewed") or encounter.get("status") in {"reviewed", "closed"} else "UN"
    segments = [
        _msh("MDM^T02^MDM_T02", control_id, settings),
        f"EVN|T02|{hl7_ts()}",
        _pid(patient),
        _pv1(encounter),
        "|".join(
            [
                "TXA",
                "1",
                "CN",
                "AP",
                hl7_ts(),
                "",
                hl7_ts(),
                "",
                hl7_escape(encounter.get("provider_name")),
                "",
                "",
                hl7_escape(f"AS-DOC-{encounter.get('id') or encounter.get('encounter_id') or ''}"),
                "",
                "",
                "",
                "",
                "AU",
                "",
                txa_status,
            ]
        ),
    ]
    for index, diagnosis in enumerate(_records(diagnoses), start=1):
        segments.append(
            "|".join(
                [
                    "DG1",
                    str(index),
                    "I10",
                    f"{hl7_escape(diagnosis.get('code'))}^{hl7_escape(diagnosis.get('description'))}^CIE10",
                    "",
                    hl7_ts(),
                    hl7_escape(diagnosis.get("diagnosis_type", "")),
                ]
            )
        )
    for index, chunk in enumerate(split_obx_text(note), start=1):
        segments.append("|".join(["OBX", str(index), "TX", "CLINNOTE^Nota Clinica^L", "1", hl7_escape(chunk), "", "", "", "", "F"]))
    return "\r".join(segments) + "\r"


def build_oru_r01(
    patient: Dict[str, Any],
    encounter: Dict[str, Any],
    observations: Iterable[Dict[str, Any]],
    settings: Optional[HL7Settings] = None,
    control_id: Optional[str] = None,
) -> str:
    settings = settings or HL7Settings.from_env()
    control_id = control_id or make_control_id("ORU", encounter.get("id") or encounter.get("encounter_id"))
    segments = [_msh("ORU^R01^ORU_R01", control_id, settings), _pid(patient), _pv1(encounter)]
    for index, obs in enumerate(observations or [], start=1):
        segments.append("|".join(["OBX", str(index), "TX", hl7_escape(obs.get("code") or "OBS^Observacion^L"), "1", hl7_escape(obs.get("value")), "", "", "", "", "F"]))
    return "\r".join(segments) + "\r"


def build_siu_s12_placeholder(*_: Any, **__: Any) -> str:
    raise NotImplementedError("SIU^S12 queda como placeholder hasta definir reglas formales de agenda con el HIS/RCE destino.")
