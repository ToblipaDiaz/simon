from __future__ import annotations

from typing import Any, Dict

from app.core.clinical_note import ClinicalNote
from app.integrations.base import HISIntegrationAdapter


class TrakCareAdapter(HISIntegrationAdapter):
    """Placeholder for InterSystems TrakCare integration.

    Requires formal vendor documentation, contracted API endpoints, authentication
    details, conformance profiles, test patients and an approved clinical workflow.
    No reverse engineering is intended or supported here.
    """

    def export_note(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        raise NotImplementedError("TrakCare integration requires formal provider API documentation.")

    def submit_note(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        raise NotImplementedError("TrakCare integration requires formal provider API documentation.")

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        raise NotImplementedError("TrakCare integration requires formal provider API documentation.")

    def get_encounter(self, encounter_id: str) -> Dict[str, Any]:
        raise NotImplementedError("TrakCare integration requires formal provider API documentation.")

