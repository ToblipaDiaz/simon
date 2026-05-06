from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from app.core.clinical_note import ClinicalNote


class HISIntegrationAdapter(ABC):
    """Base adapter for future HIS/RCE integrations."""

    @abstractmethod
    def export_note(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        """Create an exportable representation without sending it."""

    @abstractmethod
    def submit_note(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        """Submit a physician-validated note to an authorized endpoint."""

    @abstractmethod
    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        """Fetch patient data from the target HIS/RCE."""

    @abstractmethod
    def get_encounter(self, encounter_id: str) -> Dict[str, Any]:
        """Fetch encounter data from the target HIS/RCE."""

