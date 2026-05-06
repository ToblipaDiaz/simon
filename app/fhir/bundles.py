from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.core.clinical_note import ClinicalNote
from app.fhir.mappers import map_clinical_note_to_resources
from app.fhir.validators import validate_bundle


def _bundle_id(note: ClinicalNote, bundle_type: str) -> str:
    safe_note_id = "".join(ch if ch.isalnum() or ch in ".-" else "-" for ch in note.note_id)
    return f"{bundle_type}-{safe_note_id or uuid.uuid4().hex[:12]}"


def _flatten_resources(mapped: Dict[str, Any], document_first: bool = False) -> List[Dict[str, Any]]:
    ordered: List[Dict[str, Any]] = []
    if document_first:
        ordered.append(mapped["Composition"])
    for key in ["Patient", "Practitioner", "Encounter", "Condition", "Observation", "MedicationRequest", "ServiceRequest", "DocumentReference"]:
        value = mapped.get(key)
        if isinstance(value, list):
            ordered.extend(value)
        elif value:
            ordered.append(value)
    if not document_first:
        ordered.append(mapped["Composition"])
    return ordered


def _document_entry(resource: Dict[str, Any]) -> Dict[str, Any]:
    return {"fullUrl": f"urn:uuid:{uuid.uuid4()}", "resource": resource}


def _transaction_entry(resource: Dict[str, Any]) -> Dict[str, Any]:
    resource_type = resource["resourceType"]
    resource_id = resource.get("id")
    return {
        "fullUrl": f"urn:uuid:{uuid.uuid4()}",
        "resource": resource,
        "request": {
            "method": "PUT" if resource_id else "POST",
            "url": f"{resource_type}/{resource_id}" if resource_id else resource_type,
        },
    }


def build_document_bundle(note: ClinicalNote) -> Dict[str, Any]:
    mapped = map_clinical_note_to_resources(note)
    bundle = {
        "resourceType": "Bundle",
        "id": _bundle_id(note, "document"),
        "type": "document",
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "entry": [_document_entry(resource) for resource in _flatten_resources(mapped, document_first=True)],
    }
    validate_bundle(bundle)
    return bundle


def build_transaction_bundle(note: ClinicalNote) -> Dict[str, Any]:
    mapped = map_clinical_note_to_resources(note)
    bundle = {
        "resourceType": "Bundle",
        "id": _bundle_id(note, "transaction"),
        "type": "transaction",
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "entry": [_transaction_entry(resource) for resource in _flatten_resources(mapped, document_first=False)],
    }
    validate_bundle(bundle)
    return bundle


def export_bundle_json(bundle: Dict[str, Any], output_path: str | Path) -> str:
    validate_bundle(bundle)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
    return str(path)

