from __future__ import annotations

import socket
import ssl
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.hl7.config import HL7Settings
from app.hl7.escape import compute_payload_sha256


class HL7Transport(ABC):
    @abstractmethod
    def send(self, payload: str, control_id: str, message_type: str) -> str:
        """Send/export a message and return a path, ACK payload or transport receipt."""


class DisabledHL7Transport(HL7Transport):
    def send(self, payload: str, control_id: str, message_type: str) -> str:
        raise PermissionError("HL7_ENABLED=false: envio HL7 bloqueado.")


class FileHL7Transport(HL7Transport):
    def __init__(self, export_dir: str | Path):
        self.export_dir = Path(export_dir)

    def send(self, payload: str, control_id: str, message_type: str) -> str:
        self.export_dir.mkdir(parents=True, exist_ok=True)
        safe_type = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in message_type)
        filename = f"hl7_{safe_type}_{control_id}_{compute_payload_sha256(payload)[:8]}.hl7"
        path = self.export_dir / filename
        path.write_text(payload, encoding="utf-8", newline="")
        return str(path)


class MLLPHL7Transport(HL7Transport):
    """Basic MLLP transport skeleton. Disabled unless explicitly configured."""

    def __init__(self, settings: HL7Settings):
        self.settings = settings

    def send(self, payload: str, control_id: str, message_type: str) -> str:
        if not self.settings.mllp_host or not self.settings.mllp_port:
            raise ValueError("HL7_MLLP_HOST y HL7_MLLP_PORT son obligatorios para modo MLLP.")
        frame = b"\x0b" + payload.encode("utf-8") + b"\x1c\x0d"
        raw_sock = socket.create_connection((self.settings.mllp_host, self.settings.mllp_port), timeout=self.settings.mllp_timeout_seconds)
        try:
            sock = raw_sock
            if self.settings.mllp_use_tls:
                context = ssl.create_default_context(cafile=self.settings.mllp_ca_cert or None)
                if self.settings.mllp_client_cert:
                    context.load_cert_chain(self.settings.mllp_client_cert, self.settings.mllp_client_key or None)
                sock = context.wrap_socket(raw_sock, server_hostname=self.settings.mllp_host)
            with sock:
                sock.sendall(frame)
                ack = sock.recv(65536)
            return ack.decode("utf-8", errors="replace").strip("\x0b\x1c\r\n")
        finally:
            try:
                raw_sock.close()
            except Exception:
                pass


def get_hl7_transport(settings: Optional[HL7Settings] = None, base_dir: str | Path = ".") -> HL7Transport:
    settings = settings or HL7Settings.from_env()
    if not settings.enabled:
        return DisabledHL7Transport()
    if not settings.receiving_app or not settings.receiving_facility:
        raise ValueError("HL7_RECEIVING_APP y HL7_RECEIVING_FACILITY son obligatorios para envio HL7.")
    if settings.mode == "file":
        return FileHL7Transport(settings.resolved_export_dir(base_dir))
    if settings.mode == "mllp":
        return MLLPHL7Transport(settings)
    raise ValueError(f"HL7_MODE no soportado: {settings.mode}")
