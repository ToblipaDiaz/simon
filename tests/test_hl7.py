from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.hl7.config import HL7Settings
from app.hl7.escape import hl7_escape
from app.hl7.messages import build_adt_a04, build_mdm_t02
from app.hl7.transport import DisabledHL7Transport, FileHL7Transport
from app.hl7.validators import HL7ValidationError, extract_msa_status, parse_ack, validate_message_ready
from app.security import validate_admin_password_policy


PATIENT = {
    "id": 1,
    "mrn": "CA00001",
    "first_name": "Ana",
    "last_name": "Perez",
    "national_id": "12345678-9",
    "birth_date": "2010-01-15",
    "sex": "F",
}

ENCOUNTER = {
    "id": 10,
    "provider_name": "Dra. Simon",
    "note_text": "S: cefalea\nO: examen normal\nA: cefalea\nP: control",
    "status": "reviewed",
    "physician_reviewed": True,
}

SETTINGS = HL7Settings(require_review=True, require_patient_identifier=True)


class HL7Tests(unittest.TestCase):
    def test_escape_hl7(self) -> None:
        self.assertEqual(hl7_escape("a|b^c&d~e"), r"a\\F\\b\\S\\c\\T\\d\\R\\e")

    def test_adt_a04_contains_required_segments(self) -> None:
        msg = build_adt_a04(PATIENT, ENCOUNTER, settings=SETTINGS, control_id="CTRL1")
        for segment in ["MSH", "EVN", "PID", "PV1"]:
            self.assertIn(segment + "|", msg)

    def test_mdm_t02_contains_required_segments_and_obx(self) -> None:
        msg = build_mdm_t02(PATIENT, ENCOUNTER, [{"code": "R51", "description": "Cefalea"}], settings=SETTINGS, control_id="CTRL2")
        for segment in ["MSH", "EVN", "PID", "PV1", "TXA", "OBX"]:
            self.assertIn(segment + "|", msg)

    def test_dg1_with_icd10(self) -> None:
        msg = build_mdm_t02(PATIENT, ENCOUNTER, [{"code": "R51", "description": "Cefalea"}], settings=SETTINGS, control_id="CTRL3")
        self.assertIn("DG1|1|I10|R51^Cefalea^CIE10", msg)

    def test_missing_patient_identifier_fails_validation(self) -> None:
        patient = {**PATIENT, "mrn": "", "national_id": ""}
        msg = build_adt_a04(patient, ENCOUNTER, settings=SETTINGS, control_id="CTRL4")
        with self.assertRaises(HL7ValidationError):
            validate_message_ready(msg, "ADT_A04", settings=SETTINGS, physician_reviewed=True)

    def test_mdm_without_note_fails_validation(self) -> None:
        encounter = {**ENCOUNTER, "note_text": ""}
        msg = build_mdm_t02(PATIENT, encounter, [], settings=SETTINGS, control_id="CTRL5", note_text="")
        with self.assertRaises(HL7ValidationError):
            validate_message_ready(msg, "MDM_T02", settings=SETTINGS, note_text="", physician_reviewed=True)

    def test_unreviewed_note_cannot_send_when_required(self) -> None:
        msg = build_mdm_t02(PATIENT, ENCOUNTER, [], settings=SETTINGS, control_id="CTRL6")
        with self.assertRaises(HL7ValidationError):
            validate_message_ready(msg, "MDM_T02", settings=SETTINGS, note_text=ENCOUNTER["note_text"], physician_reviewed=False)

    def test_file_transport_saves_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = FileHL7Transport(tmp).send("MSH|^~\\&|A\r", "CTRL7", "ADT_A04")
            self.assertTrue(Path(path).exists())

    def test_disabled_transport_blocks_send(self) -> None:
        with self.assertRaises(PermissionError):
            DisabledHL7Transport().send("MSH|^~\\&|A\r", "CTRL8", "ADT_A04")

    def test_parse_ack_detects_statuses(self) -> None:
        for code in ["AA", "AE", "AR"]:
            msg = f"MSH|^~\\&|HIS|F|AS|F|202605061200||ACK|ACK1|P|2.5\rMSA|{code}|CTRL9|texto\r"
            ack = parse_ack(msg)
            self.assertEqual(extract_msa_status(msg), code)
            self.assertEqual(ack.status, code)
            self.assertEqual(ack.is_ack, code == "AA")
            self.assertEqual(ack.is_nack, code in {"AE", "AR"})

    def test_default_password_blocks_production(self) -> None:
        with self.assertRaises(RuntimeError):
            validate_admin_password_policy("production", "admin1234")


if __name__ == "__main__":
    unittest.main()

