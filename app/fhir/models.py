from __future__ import annotations

import os
from dataclasses import dataclass


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
class FHIRSettings:
    """Runtime FHIR configuration loaded from environment variables."""

    enabled: bool = False
    base_url: str = ""
    auth_mode: str = "none"
    api_key: str = ""
    bearer_token: str = ""
    client_id: str = ""
    client_secret: str = ""
    token_url: str = ""
    timeout_seconds: int = 30
    verify_ssl: bool = True
    write_mode: str = "draft"
    country_profile: str = "CL"

    @classmethod
    def from_env(cls) -> "FHIRSettings":
        return cls(
            enabled=_env_bool("FHIR_ENABLED", False),
            base_url=os.getenv("FHIR_BASE_URL", "").strip(),
            auth_mode=os.getenv("FHIR_AUTH_MODE", "none").strip().lower() or "none",
            api_key=os.getenv("FHIR_API_KEY", "").strip(),
            bearer_token=os.getenv("FHIR_BEARER_TOKEN", "").strip(),
            client_id=os.getenv("FHIR_CLIENT_ID", "").strip(),
            client_secret=os.getenv("FHIR_CLIENT_SECRET", "").strip(),
            token_url=os.getenv("FHIR_TOKEN_URL", "").strip(),
            timeout_seconds=_env_int("FHIR_TIMEOUT_SECONDS", 30),
            verify_ssl=_env_bool("FHIR_VERIFY_SSL", True),
            write_mode=os.getenv("FHIR_WRITE_MODE", "draft").strip().lower() or "draft",
            country_profile=os.getenv("FHIR_COUNTRY_PROFILE", "CL").strip() or "CL",
        )

    @property
    def can_write(self) -> bool:
        return self.enabled and self.write_mode in {"write", "send", "production", "real"}

