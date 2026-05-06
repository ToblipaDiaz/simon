from __future__ import annotations

from typing import Any, Dict

from app.core.clinical_note import ClinicalNote
from app.integrations.base import HISIntegrationAdapter


class MedisynAdapter(HISIntegrationAdapter):
    """Placeholder for Medisyn integration.

    Requires formal vendor documentation, contracted API credentials, test
    environment access, conformance profiles and provider-approved workflow rules.
    """

    def export_note(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        raise NotImplementedError("Medisyn integration requires formal provider API documentation.")

    def submit_note(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        raise NotImplementedError("Medisyn integration requires formal provider API documentation.")

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Medisyn integration requires formal provider API documentation.")

    def get_encounter(self, encounter_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Medisyn integration requires formal provider API documentation.")

