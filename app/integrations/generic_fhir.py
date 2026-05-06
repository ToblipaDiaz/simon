from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from app.core.clinical_note import ClinicalNote
from app.fhir.bundles import build_document_bundle, build_transaction_bundle, export_bundle_json
from app.fhir.client import FHIRClient
from app.fhir.models import FHIRSettings
from app.integrations.base import HISIntegrationAdapter


class GenericFHIRAdapter(HISIntegrationAdapter):
    """Generic standards-based adapter for FHIR R4 servers."""

    def __init__(self, client: Optional[FHIRClient] = None, settings: Optional[FHIRSettings] = None):
        self.settings = settings or FHIRSettings.from_env()
        self.client = client or FHIRClient(self.settings)

    def export_note(self, clinical_note: ClinicalNote, output_dir: Optional[str | Path] = None) -> Dict[str, Any]:
        bundle = build_document_bundle(clinical_note)
        if output_dir:
            export_bundle_json(bundle, Path(output_dir) / f"fhir_bundle_{clinical_note.note_id}.json")
        return bundle

    def export_transaction(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        return build_transaction_bundle(clinical_note)

    def submit_note(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        bundle = build_transaction_bundle(clinical_note)
        return self.client.submit_bundle(bundle, clinical_note=clinical_note)

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        return self.client.get_resource("Patient", patient_id)

    def get_encounter(self, encounter_id: str) -> Dict[str, Any]:
        return self.client.get_resource("Encounter", encounter_id)

