from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PatientInput(BaseModel):
    """Internal patient shape used before mapping to any external standard."""

    model_config = ConfigDict(extra="allow")

    patient_id: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    administrative_gender: Optional[str] = None


class ClinicianInput(BaseModel):
    """Internal clinician shape used before mapping to Practitioner."""

    model_config = ConfigDict(extra="allow")

    clinician_id: Optional[str] = None
    full_name: str
    specialty: Optional[str] = None
    license_number: Optional[str] = None


class DiagnosisInput(BaseModel):
    """Diagnosis entry. Free text is accepted through description."""

    model_config = ConfigDict(extra="allow")

    code: Optional[str] = None
    description: str
    system: Optional[str] = "http://hl7.org/fhir/sid/icd-10"
    clinical_status: Optional[str] = "active"
    verification_status: Optional[str] = None


class MedicationInput(BaseModel):
    """Medication request draft entry."""

    model_config = ConfigDict(extra="allow")

    name: str
    code: Optional[str] = None
    dosage_text: Optional[str] = None
    intent: str = "plan"


class ServiceRequestInput(BaseModel):
    """Service request draft entry."""

    model_config = ConfigDict(extra="allow")

    description: str
    code: Optional[str] = None
    category: Optional[str] = None
    intent: str = "plan"


class ObjectiveObservationInput(BaseModel):
    """Structured objective datum that can safely become a FHIR Observation."""

    model_config = ConfigDict(extra="allow")

    code: Optional[str] = None
    display: str
    value: Optional[Any] = None
    unit: Optional[str] = None
    interpretation: Optional[str] = None


class ClinicalNote(BaseModel):
    """FHIR-ready internal representation of an ambulatory clinical note.

    The note is draft-first by default: AI output is considered a clinical draft
    until a physician validates it.
    """

    model_config = ConfigDict(extra="allow")

    note_id: str
    patient: PatientInput
    clinician: ClinicianInput
    encounter_datetime: datetime
    center_name: Optional[str] = None
    chief_complaint: Optional[str] = None
    subjective: str
    objective: str
    assessment: str
    plan: str
    diagnoses: List[DiagnosisInput] = Field(default_factory=list)
    medications: List[MedicationInput] = Field(default_factory=list)
    service_requests: List[ServiceRequestInput] = Field(default_factory=list)
    objective_observations: List[ObjectiveObservationInput] = Field(default_factory=list)
    source_transcript: Optional[str] = None
    ai_generated: bool = True
    physician_validated: bool = False


def _field_value(note_json: Optional[Dict[str, Any]], key: str) -> Optional[str]:
    if not isinstance(note_json, dict):
        return None
    current: Any = note_json
    for part in key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    if isinstance(current, dict):
        value = current.get("value")
        return str(value).strip() if value not in (None, "") else None
    if current not in (None, ""):
        return str(current).strip()
    return None


def _split_name(full_name: str) -> tuple[str, str]:
    parts = [p for p in (full_name or "").strip().split() if p]
    if not parts:
        return "Paciente", "Sin apellido"
    if len(parts) == 1:
        return parts[0], "Sin apellido"
    return parts[0], " ".join(parts[1:])


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.fromisoformat(value.strip())
        except ValueError:
            pass
    return datetime.now()


def _list_from_text(value: Optional[str]) -> List[str]:
    if not value:
        return []
    chunks = []
    for raw in value.replace("\r", "\n").split("\n"):
        item = raw.strip(" -\t")
        if item:
            chunks.append(item)
    return chunks


def clinical_note_from_project_rows(
    patient_row: Dict[str, Any],
    encounter_row: Dict[str, Any],
    diagnoses: Optional[List[Dict[str, Any]]] = None,
    note_json: Optional[Dict[str, Any]] = None,
    reviewed_note_text: Optional[str] = None,
    clinician_specialty: Optional[str] = None,
    clinician_license_number: Optional[str] = None,
    physician_validated: bool = False,
) -> ClinicalNote:
    """Build the internal note model from the current SQLite-backed app rows."""

    note_json = note_json or {}
    first_name = (patient_row.get("first_name") or "").strip()
    last_name = (patient_row.get("last_name") or "").strip()
    if not first_name or not last_name:
        json_name = _field_value(note_json, "patient_name")
        split_first, split_last = _split_name(json_name or "")
        first_name = first_name or split_first
        last_name = last_name or split_last

    subjective_parts = [
        encounter_row.get("chief_complaint") or _field_value(note_json, "chief_complaint"),
        _field_value(note_json, "hpi_onset"),
        _field_value(note_json, "hpi_course"),
        _field_value(note_json, "hpi_frequency"),
        _field_value(note_json, "hpi_duration"),
        _field_value(note_json, "hpi_triggers"),
        _field_value(note_json, "hpi_relief"),
        _field_value(note_json, "past_medical_history"),
        _field_value(note_json, "allergies"),
    ]
    objective_parts = [
        _field_value(note_json, "exam_neuro"),
        _field_value(note_json, "exams_reviewed"),
        encounter_row.get("images_text"),
    ]
    plan_parts = [
        _field_value(note_json, "indications.general"),
        _field_value(note_json, "indications.school"),
        _field_value(note_json, "indications.meds"),
        _field_value(note_json, "indications.followup"),
        _field_value(note_json, "indications.referrals"),
    ]

    diagnosis_entries = [
        DiagnosisInput(
            code=(d.get("code") or "").strip() or None,
            description=(d.get("description") or "").strip() or "Diagnostico sin descripcion",
            verification_status=d.get("certainty"),
        )
        for d in (diagnoses or [])
    ]
    if not diagnosis_entries:
        assessment_text = _field_value(note_json, "diagnostic_hypothesis")
        if assessment_text:
            diagnosis_entries.append(DiagnosisInput(description=assessment_text))

    medications = [MedicationInput(name=item) for item in _list_from_text(_field_value(note_json, "indications.meds"))]
    service_requests = [ServiceRequestInput(description=item) for item in _list_from_text(_field_value(note_json, "indications.referrals"))]

    return ClinicalNote(
        note_id=str(encounter_row.get("id") or encounter_row.get("note_id") or ""),
        patient=PatientInput(
            patient_id=str(patient_row.get("mrn") or patient_row.get("id") or ""),
            document_type="RUN" if patient_row.get("national_id") else None,
            document_number=patient_row.get("national_id") or None,
            first_name=first_name,
            last_name=last_name,
            birth_date=patient_row.get("birth_date") or None,
            administrative_gender=patient_row.get("sex") or _field_value(note_json, "patient_sex"),
        ),
        clinician=ClinicianInput(
            clinician_id=encounter_row.get("provider_name") or None,
            full_name=encounter_row.get("provider_name") or "Profesional no especificado",
            specialty=clinician_specialty,
            license_number=clinician_license_number,
        ),
        encounter_datetime=_parse_datetime(encounter_row.get("created_at") or encounter_row.get("updated_at")),
        center_name=encounter_row.get("facility_name") or patient_row.get("facility_name") or None,
        chief_complaint=encounter_row.get("chief_complaint") or _field_value(note_json, "chief_complaint"),
        subjective="\n".join(p for p in subjective_parts if p) or "No registrado",
        objective="\n".join(p for p in objective_parts if p) or "No registrado",
        assessment=_field_value(note_json, "diagnostic_hypothesis") or "No registrado",
        plan="\n".join(p for p in plan_parts if p) or "No registrado",
        diagnoses=diagnosis_entries,
        medications=medications,
        service_requests=service_requests,
        source_transcript=encounter_row.get("transcript_text") or encounter_row.get("dictation_text") or None,
        ai_generated=bool(note_json),
        physician_validated=physician_validated,
        reviewed_note_text=reviewed_note_text,
    )

