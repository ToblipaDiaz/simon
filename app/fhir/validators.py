from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.clinical_note import ClinicalNote
from app.fhir.models import FHIRSettings


class FHIRValidationError(ValueError):
    """Raised when a minimal FHIR safety or structure rule fails."""


def validate_resource(resource: Dict[str, Any]) -> None:
    if not isinstance(resource, dict) or not resource.get("resourceType"):
        raise FHIRValidationError("FHIR resourceType es obligatorio.")

    resource_type = resource["resourceType"]
    if resource_type == "Bundle":
        validate_bundle(resource)
    elif resource_type == "Patient":
        if not resource.get("name") and not resource.get("identifier"):
            raise FHIRValidationError("Patient requiere name o identifier.")
    elif resource_type == "Composition":
        required = ["status", "type", "subject", "date", "author", "title"]
        missing = [field for field in required if not resource.get(field)]
        if missing:
            raise FHIRValidationError(f"Composition incompleta. Faltan: {', '.join(missing)}")


def validate_bundle(bundle: Dict[str, Any]) -> None:
    if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
        raise FHIRValidationError("Se esperaba un recurso Bundle.")
    entries = bundle.get("entry")
    if not isinstance(entries, list) or not entries:
        raise FHIRValidationError("Bundle.entry es obligatorio.")
    for entry in entries:
        resource = entry.get("resource") if isinstance(entry, dict) else None
        validate_resource(resource)


def ensure_submit_allowed(
    bundle: Dict[str, Any],
    clinical_note: Optional[ClinicalNote] = None,
    settings: Optional[FHIRSettings] = None,
) -> None:
    settings = settings or FHIRSettings.from_env()
    validate_bundle(bundle)
    if not settings.enabled:
        raise PermissionError("FHIR_ENABLED=false: envio a endpoint FHIR bloqueado. Solo se permite exportacion local.")
    if settings.write_mode not in {"draft", "write", "send", "production", "real"}:
        raise PermissionError(f"FHIR_WRITE_MODE invalido: {settings.write_mode}")
    if settings.write_mode in {"write", "send", "production", "real"} and clinical_note and not clinical_note.physician_validated:
        raise PermissionError("La nota no esta validada por medico; se bloquea envio real a HIS/RCE.")

