from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    return raw.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class HL7Settings:
    enabled: bool = False
    mode: str = "file"
    version: str = "2.5"
    sending_app: str = "ASISTENTE_SIMON"
    sending_facility: str = ""
    receiving_app: str = "HIS_DESTINO"
    receiving_facility: str = ""
    export_dir: str = "exports/hl7"
    require_review: bool = True
    require_patient_identifier: bool = True
    mllp_host: str = ""
    mllp_port: int = 0
    mllp_timeout_seconds: int = 30
    mllp_use_tls: bool = False
    mllp_ca_cert: str = ""
    mllp_client_cert: str = ""
    mllp_client_key: str = ""

    @classmethod
    def from_env(cls) -> "HL7Settings":
        return cls(
            enabled=_env_bool("HL7_ENABLED", False),
            mode=(os.getenv("HL7_MODE", "file").strip().lower() or "file"),
            version=os.getenv("HL7_VERSION", "2.5").strip() or "2.5",
            sending_app=os.getenv("HL7_SENDING_APP", "ASISTENTE_SIMON").strip() or "ASISTENTE_SIMON",
            sending_facility=os.getenv("HL7_SENDING_FACILITY", "").strip(),
            receiving_app=os.getenv("HL7_RECEIVING_APP", "HIS_DESTINO").strip() or "HIS_DESTINO",
            receiving_facility=os.getenv("HL7_RECEIVING_FACILITY", "").strip(),
            export_dir=os.getenv("HL7_EXPORT_DIR", "exports/hl7").strip() or "exports/hl7",
            require_review=_env_bool("HL7_REQUIRE_REVIEW", True),
            require_patient_identifier=_env_bool("HL7_REQUIRE_PATIENT_IDENTIFIER", True),
            mllp_host=os.getenv("HL7_MLLP_HOST", "").strip(),
            mllp_port=_env_int("HL7_MLLP_PORT", 0),
            mllp_timeout_seconds=_env_int("HL7_MLLP_TIMEOUT_SECONDS", 30),
            mllp_use_tls=_env_bool("HL7_MLLP_USE_TLS", False),
            mllp_ca_cert=os.getenv("HL7_MLLP_CA_CERT", "").strip(),
            mllp_client_cert=os.getenv("HL7_MLLP_CLIENT_CERT", "").strip(),
            mllp_client_key=os.getenv("HL7_MLLP_CLIENT_KEY", "").strip(),
        )

    @property
    def transport_label(self) -> str:
        if not self.enabled:
            return "desactivada"
        if self.mode == "file":
            return "archivo local"
        if self.mode == "mllp":
            return "MLLP"
        return self.mode

    def resolved_export_dir(self, base_dir: str | Path) -> Path:
        path = Path(self.export_dir)
        if path.is_absolute():
            return path
        return Path(base_dir) / path

