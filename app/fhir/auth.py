from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

from app.fhir.models import FHIRSettings

_TOKEN_CACHE: Dict[str, Any] = {"access_token": None, "expires_at": 0.0}


def _get_oauth2_token(settings: FHIRSettings) -> str:
    now = time.time()
    cached = _TOKEN_CACHE.get("access_token")
    if cached and float(_TOKEN_CACHE.get("expires_at") or 0) > now + 30:
        return str(cached)
    if not settings.token_url or not settings.client_id or not settings.client_secret:
        raise ValueError("OAuth2 Client Credentials requiere FHIR_TOKEN_URL, FHIR_CLIENT_ID y FHIR_CLIENT_SECRET.")

    response = requests.post(
        settings.token_url,
        data={"grant_type": "client_credentials"},
        auth=(settings.client_id, settings.client_secret),
        timeout=settings.timeout_seconds,
        verify=settings.verify_ssl,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise ValueError("El servidor OAuth2 no retorno access_token.")
    expires_in = int(payload.get("expires_in") or 300)
    _TOKEN_CACHE["access_token"] = token
    _TOKEN_CACHE["expires_at"] = now + expires_in
    return str(token)


def prepare_auth_headers(settings: Optional[FHIRSettings] = None) -> Dict[str, str]:
    settings = settings or FHIRSettings.from_env()
    mode = settings.auth_mode
    headers = {"Accept": "application/fhir+json", "Content-Type": "application/fhir+json"}

    if mode == "none":
        return headers
    if mode == "api_key":
        if not settings.api_key:
            raise ValueError("FHIR_AUTH_MODE=api_key requiere FHIR_API_KEY.")
        headers["X-API-Key"] = settings.api_key
        return headers
    if mode == "bearer":
        if not settings.bearer_token:
            raise ValueError("FHIR_AUTH_MODE=bearer requiere FHIR_BEARER_TOKEN.")
        headers["Authorization"] = f"Bearer {settings.bearer_token}"
        return headers
    if mode == "oauth2_client_credentials":
        headers["Authorization"] = f"Bearer {_get_oauth2_token(settings)}"
        return headers
    raise ValueError(f"FHIR_AUTH_MODE no soportado: {mode}")

