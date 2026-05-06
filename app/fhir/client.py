from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

from app.fhir.auth import prepare_auth_headers
from app.fhir.models import FHIRSettings
from app.fhir.validators import ensure_submit_allowed, validate_resource

logger = logging.getLogger(__name__)


class FHIRClient:
    """Generic FHIR REST client.

    This client is intentionally disabled unless FHIR_ENABLED=true. Local bundle
    export does not require this class.
    """

    def __init__(self, settings: Optional[FHIRSettings] = None):
        self.settings = settings or FHIRSettings.from_env()

    def _assert_enabled(self) -> None:
        if not self.settings.enabled:
            raise PermissionError("FHIR_ENABLED=false: cliente FHIR desactivado.")
        if not self.settings.base_url:
            raise ValueError("FHIR_BASE_URL es obligatorio cuando FHIR_ENABLED=true.")

    def _url(self, path: str) -> str:
        base = self.settings.base_url.rstrip("/") + "/"
        return urljoin(base, path.lstrip("/"))

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        self._assert_enabled()
        headers = prepare_auth_headers(self.settings)
        logger.info("FHIR %s %s", method.upper(), path)
        response = requests.request(
            method,
            self._url(path),
            headers=headers,
            timeout=self.settings.timeout_seconds,
            verify=self.settings.verify_ssl,
            **kwargs,
        )
        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()

    def get_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        return self._request("GET", f"{resource_type}/{resource_id}")

    def search(self, resource_type: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self._request("GET", resource_type, params=params or {})

    def create_resource(self, resource_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        validate_resource(payload)
        return self._request("POST", resource_type, json=payload)

    def update_resource(self, resource_type: str, resource_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        validate_resource(payload)
        return self._request("PUT", f"{resource_type}/{resource_id}", json=payload)

    def submit_bundle(self, bundle: Dict[str, Any], clinical_note: Any = None) -> Dict[str, Any]:
        ensure_submit_allowed(bundle, clinical_note=clinical_note, settings=self.settings)
        logger.info("Submitting FHIR Bundle id=%s entries=%s", bundle.get("id"), len(bundle.get("entry", [])))
        return self._request("POST", "", json=bundle)

