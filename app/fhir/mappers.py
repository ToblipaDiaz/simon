from __future__ import annotations

import base64
import html
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.clinical_note import ClinicalNote, DiagnosisInput


LOINC_SYSTEM = "http://loinc.org"
ICD10_SYSTEM = "http://hl7.org/fhir/sid/icd-10"


def normalize_gender(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    mapping = {
        "m": "male",
        "masculino": "male",
        "male": "male",
        "hombre": "male",
        "f": "female",
        "femenino": "female",
        "female": "female",
        "mujer": "female",
        "o": "other",
        "otro": "other",
        "other": "other",
        "u": "unknown",
        "desconocido": "unknown",
        "unknown": "unknown",
    }
    return mapping.get(raw, "unknown")


def _resource_id(prefix: str, value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9.-]", "-", value or "")
    safe = safe.strip("-")[:48] or uuid.uuid4().hex[:12]
    return f"{prefix}-{safe}"


def _iso_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        return dt.isoformat(timespec="seconds")
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _narrative(text: str) -> Dict[str, str]:
    return {
        "status": "generated",
        "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{html.escape(text or '')}</div>",
    }


def _reference(resource_type: str, resource_id: str, display: Optional[str] = None) -> Dict[str, str]:
    ref = {"reference": f"{resource_type}/{resource_id}"}
    if display:
        ref["display"] = display
    return ref


def patient_to_fhir(note: ClinicalNote) -> Dict[str, Any]:
    patient = note.patient
    identifiers: List[Dict[str, Any]] = []
    if patient.document_type and patient.document_number:
        identifiers.append(
            {
                "system": f"urn:id:{patient.document_type.strip().lower()}",
                "value": patient.document_number,
                "type": {"text": patient.document_type},
            }
        )
    if patient.patient_id:
        identifiers.append({"system": "urn:asistente-simon:patient-id", "value": patient.patient_id})

    resource = {
        "resourceType": "Patient",
        "id": _resource_id("patient", patient.patient_id or patient.document_number or note.note_id),
        "name": [{"use": "official", "family": patient.last_name, "given": [patient.first_name]}],
        "gender": normalize_gender(patient.administrative_gender),
    }
    if identifiers:
        resource["identifier"] = identifiers
    if patient.birth_date:
        resource["birthDate"] = patient.birth_date.isoformat()
    return resource


def practitioner_to_fhir(note: ClinicalNote) -> Dict[str, Any]:
    clinician = note.clinician
    resource = {
        "resourceType": "Practitioner",
        "id": _resource_id("practitioner", clinician.clinician_id or clinician.full_name),
        "name": [{"text": clinician.full_name}],
    }
    identifiers = []
    if clinician.clinician_id:
        identifiers.append({"system": "urn:asistente-simon:clinician-id", "value": clinician.clinician_id})
    if clinician.license_number:
        identifiers.append({"system": "urn:professional-license", "value": clinician.license_number})
    if identifiers:
        resource["identifier"] = identifiers
    if clinician.specialty:
        resource["qualification"] = [{"code": {"text": clinician.specialty}}]
    return resource


def encounter_to_fhir(note: ClinicalNote, patient: Dict[str, Any], practitioner: Dict[str, Any]) -> Dict[str, Any]:
    return _strip_none({
        "resourceType": "Encounter",
        "id": _resource_id("encounter", note.note_id),
        "status": "finished" if note.physician_validated else "in-progress",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
        "subject": _reference("Patient", patient["id"], f"{note.patient.first_name} {note.patient.last_name}".strip()),
        "participant": [{"individual": _reference("Practitioner", practitioner["id"], note.clinician.full_name)}],
        "period": {"start": _iso_datetime(note.encounter_datetime)},
        "serviceProvider": {"display": note.center_name} if note.center_name else None,
        "reasonCode": [{"text": note.chief_complaint}] if note.chief_complaint else None,
    })


def _strip_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_none(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [_strip_none(v) for v in value if v is not None]
    return value


def _normalize_condition_verification(value: Optional[str]) -> str:
    raw = (value or "").strip().lower()
    mapping = {
        "sospecha": "provisional",
        "sospechoso": "provisional",
        "probable": "provisional",
        "diferencial": "differential",
        "confirmado": "confirmed",
        "confirmada": "confirmed",
        "confirmed": "confirmed",
        "descartado": "refuted",
        "descartada": "refuted",
        "refuted": "refuted",
    }
    return mapping.get(raw, raw if raw in {"unconfirmed", "provisional", "differential", "confirmed", "refuted", "entered-in-error"} else "unconfirmed")


def condition_to_fhir(
    note: ClinicalNote,
    diagnosis: DiagnosisInput,
    index: int,
    patient: Dict[str, Any],
    encounter: Dict[str, Any],
) -> Dict[str, Any]:
    coding = []
    if diagnosis.code:
        coding.append({"system": diagnosis.system or ICD10_SYSTEM, "code": diagnosis.code, "display": diagnosis.description})
    verification_text = _normalize_condition_verification(diagnosis.verification_status)
    return _strip_none(
        {
            "resourceType": "Condition",
            "id": _resource_id("condition", f"{note.note_id}-{index}"),
            "clinicalStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": diagnosis.clinical_status or "active"}]
            },
            "verificationStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": verification_text}]
            },
            "code": {"coding": coding, "text": diagnosis.description},
            "subject": _reference("Patient", patient["id"]),
            "encounter": _reference("Encounter", encounter["id"]),
            "recordedDate": _iso_datetime(note.encounter_datetime),
        }
    )


def observation_to_fhir(note: ClinicalNote, observation: Any, index: int, patient: Dict[str, Any], encounter: Dict[str, Any]) -> Dict[str, Any]:
    value = observation.value
    resource: Dict[str, Any] = {
        "resourceType": "Observation",
        "id": _resource_id("observation", f"{note.note_id}-{index}"),
        "status": "final" if note.physician_validated else "preliminary",
        "code": {
            "coding": [{"system": LOINC_SYSTEM, "code": observation.code, "display": observation.display}] if observation.code else [],
            "text": observation.display,
        },
        "subject": _reference("Patient", patient["id"]),
        "encounter": _reference("Encounter", encounter["id"]),
        "effectiveDateTime": _iso_datetime(note.encounter_datetime),
    }
    if isinstance(value, (int, float)):
        resource["valueQuantity"] = {"value": value, "unit": observation.unit} if observation.unit else {"value": value}
    elif value is not None:
        resource["valueString"] = str(value)
    if observation.interpretation:
        resource["interpretation"] = [{"text": observation.interpretation}]
    return _strip_none(resource)


def medication_request_to_fhir(note: ClinicalNote, medication: Any, index: int, patient: Dict[str, Any], practitioner: Dict[str, Any]) -> Dict[str, Any]:
    return _strip_none(
        {
            "resourceType": "MedicationRequest",
            "id": _resource_id("medicationrequest", f"{note.note_id}-{index}"),
            "status": "draft" if not note.physician_validated else "active",
            "intent": medication.intent or "plan",
            "medicationCodeableConcept": {"coding": [{"code": medication.code}] if medication.code else [], "text": medication.name},
            "subject": _reference("Patient", patient["id"]),
            "authoredOn": note.encounter_datetime.date().isoformat(),
            "requester": _reference("Practitioner", practitioner["id"], note.clinician.full_name),
            "dosageInstruction": [{"text": medication.dosage_text}] if medication.dosage_text else None,
        }
    )


def service_request_to_fhir(note: ClinicalNote, request: Any, index: int, patient: Dict[str, Any], practitioner: Dict[str, Any]) -> Dict[str, Any]:
    return _strip_none(
        {
            "resourceType": "ServiceRequest",
            "id": _resource_id("servicerequest", f"{note.note_id}-{index}"),
            "status": "draft" if not note.physician_validated else "active",
            "intent": request.intent or "plan",
            "category": [{"text": request.category}] if request.category else None,
            "code": {"coding": [{"code": request.code}] if request.code else [], "text": request.description},
            "subject": _reference("Patient", patient["id"]),
            "authoredOn": note.encounter_datetime.date().isoformat(),
            "requester": _reference("Practitioner", practitioner["id"], note.clinician.full_name),
        }
    )


def composition_to_fhir(
    note: ClinicalNote,
    patient: Dict[str, Any],
    practitioner: Dict[str, Any],
    encounter: Dict[str, Any],
) -> Dict[str, Any]:
    status = "final" if note.physician_validated else "preliminary"
    sections = [
        ("Subjetivo", "61150-9", note.subjective),
        ("Objetivo", "61149-1", note.objective),
        ("Evaluacion", "51848-0", note.assessment),
        ("Plan", "18776-5", note.plan),
    ]
    return {
        "resourceType": "Composition",
        "id": _resource_id("composition", note.note_id),
        "status": status,
        "type": {"coding": [{"system": LOINC_SYSTEM, "code": "11506-3", "display": "Progress note"}], "text": "Nota clinica SOAP"},
        "subject": _reference("Patient", patient["id"], f"{note.patient.first_name} {note.patient.last_name}".strip()),
        "encounter": _reference("Encounter", encounter["id"]),
        "date": _iso_datetime(note.encounter_datetime),
        "author": [_reference("Practitioner", practitioner["id"], note.clinician.full_name)],
        "title": "Nota clinica ambulatoria SOAP",
        "confidentiality": "N",
        "section": [
            {
                "title": title,
                "code": {"coding": [{"system": LOINC_SYSTEM, "code": code}], "text": title},
                "text": _narrative(text),
            }
            for title, code, text in sections
        ],
    }


def document_reference_to_fhir(
    note: ClinicalNote,
    patient: Dict[str, Any],
    practitioner: Dict[str, Any],
) -> Dict[str, Any]:
    status = "final" if note.physician_validated else "preliminary"
    content = "\n\n".join(
        [
            "SUBJETIVO\n" + note.subjective,
            "OBJETIVO\n" + note.objective,
            "EVALUACION\n" + note.assessment,
            "PLAN\n" + note.plan,
        ]
    )
    reviewed_text = getattr(note, "reviewed_note_text", None)
    if reviewed_text:
        content = str(reviewed_text)
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return {
        "resourceType": "DocumentReference",
        "id": _resource_id("documentreference", note.note_id),
        "status": "current",
        "docStatus": status,
        "type": {"coding": [{"system": LOINC_SYSTEM, "code": "11506-3", "display": "Progress note"}], "text": "Nota clinica SOAP"},
        "subject": _reference("Patient", patient["id"]),
        "date": _iso_datetime(note.encounter_datetime),
        "author": [_reference("Practitioner", practitioner["id"], note.clinician.full_name)],
        "description": "Borrador clinico generado por IA pendiente de validacion medica" if not note.physician_validated else "Nota clinica validada por medico",
        "content": [
            {
                "attachment": {
                    "contentType": "text/plain; charset=utf-8",
                    "title": f"nota_clinica_{note.note_id}.txt",
                    "creation": _iso_datetime(note.encounter_datetime),
                    "data": encoded,
                }
            }
        ],
    }


def map_clinical_note_to_resources(note: ClinicalNote) -> Dict[str, Any]:
    patient = patient_to_fhir(note)
    practitioner = practitioner_to_fhir(note)
    encounter = encounter_to_fhir(note, patient, practitioner)
    encounter = _strip_none(encounter)
    conditions = [condition_to_fhir(note, d, i + 1, patient, encounter) for i, d in enumerate(note.diagnoses)]
    observations = [
        observation_to_fhir(note, obs, i + 1, patient, encounter)
        for i, obs in enumerate(note.objective_observations)
    ]
    medication_requests = [
        medication_request_to_fhir(note, med, i + 1, patient, practitioner)
        for i, med in enumerate(note.medications)
    ]
    service_requests = [
        service_request_to_fhir(note, req, i + 1, patient, practitioner)
        for i, req in enumerate(note.service_requests)
    ]
    composition = composition_to_fhir(note, patient, practitioner, encounter)
    document_reference = document_reference_to_fhir(note, patient, practitioner)
    return {
        "Patient": patient,
        "Practitioner": practitioner,
        "Encounter": encounter,
        "Condition": conditions,
        "Observation": observations,
        "MedicationRequest": medication_requests,
        "ServiceRequest": service_requests,
        "Composition": composition,
        "DocumentReference": document_reference,
    }
