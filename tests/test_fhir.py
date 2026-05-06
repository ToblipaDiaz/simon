from __future__ import annotations

import unittest
from datetime import datetime

from app.core.clinical_note import ClinicianInput, ClinicalNote, DiagnosisInput, PatientInput
from app.fhir.bundles import build_document_bundle
from app.fhir.client import FHIRClient
from app.fhir.mappers import composition_to_fhir, encounter_to_fhir, patient_to_fhir, practitioner_to_fhir
from app.fhir.models import FHIRSettings


def sample_note(physician_validated: bool = False) -> ClinicalNote:
    return ClinicalNote(
        note_id="test-001",
        patient=PatientInput(
            patient_id="MRN123",
            document_type="RUN",
            document_number="12345678-9",
            first_name="Ana",
            last_name="Perez",
            birth_date="2010-01-15",
            administrative_gender="F",
        ),
        clinician=ClinicianInput(full_name="Dra. Simon", specialty="Neurologia pediatrica", license_number="MED123"),
        encounter_datetime=datetime(2026, 5, 6, 10, 30, 0),
        center_name="Consulta ambulatoria",
        chief_complaint="Cefalea",
        subjective="Paciente refiere cefalea.",
        objective="Examen neurologico sin focalidad.",
        assessment="Cefalea primaria probable.",
        plan="Control y signos de alarma.",
        diagnoses=[DiagnosisInput(code="R51", description="Cefalea")],
        physician_validated=physician_validated,
    )


class FHIRTests(unittest.TestCase):
    def test_create_patient_fhir(self) -> None:
        patient = patient_to_fhir(sample_note())
        self.assertEqual(patient["resourceType"], "Patient")
        self.assertEqual(patient["name"][0]["family"], "Perez")
        self.assertEqual(patient["gender"], "female")
        self.assertEqual(patient["identifier"][0]["value"], "12345678-9")

    def test_create_composition_soap(self) -> None:
        note = sample_note()
        patient = patient_to_fhir(note)
        practitioner = practitioner_to_fhir(note)
        encounter = encounter_to_fhir(note, patient, practitioner)
        composition = composition_to_fhir(note, patient, practitioner, encounter)
        self.assertEqual(composition["resourceType"], "Composition")
        self.assertEqual(composition["status"], "preliminary")
        self.assertEqual([s["title"] for s in composition["section"]], ["Subjetivo", "Objetivo", "Evaluacion", "Plan"])

    def test_create_document_bundle(self) -> None:
        bundle = build_document_bundle(sample_note())
        self.assertEqual(bundle["resourceType"], "Bundle")
        self.assertEqual(bundle["type"], "document")
        self.assertEqual(bundle["entry"][0]["resource"]["resourceType"], "Composition")
        self.assertTrue(any(e["resource"]["resourceType"] == "DocumentReference" for e in bundle["entry"]))

    def test_block_submit_when_fhir_disabled(self) -> None:
        settings = FHIRSettings(enabled=False, base_url="", write_mode="draft")
        client = FHIRClient(settings=settings)
        with self.assertRaises(PermissionError):
            client.submit_bundle(build_document_bundle(sample_note(physician_validated=True)), clinical_note=sample_note(True))


if __name__ == "__main__":
    unittest.main()
