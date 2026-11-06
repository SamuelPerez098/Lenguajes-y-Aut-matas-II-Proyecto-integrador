"""Servicios externos: correo. El VM solo conoce la interfaz EmailService."""
import os
import smtplib
from email.message import EmailMessage
from typing import Protocol

from .errors import ExecutionError


class EmailService(Protocol):
    def send(self, to: str, message: str) -> None: ...


class InMemoryEmailService:
    """Guarda los correos en memoria (pruebas y modo demo)."""

    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send(self, to: str, message: str) -> None:
        self.sent.append((to, message))


class SmtpEmailService:
    """Envía por SMTP; con Mailpit: host=localhost, port=1025 (sin autenticación)."""

    def __init__(self, host: str | None = None, port: int | None = None,
                 sender: str = "commandflow@localhost"):
        self.host = host or os.getenv("SMTP_HOST", "localhost")
        self.port = port or int(os.getenv("SMTP_PORT", "1025"))
        self.sender = sender

    def send(self, to: str, message: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.sender, to, "Notificación de CommandFlow"
        msg.set_content(message)
        try:
            with smtplib.SMTP(self.host, self.port, timeout=5) as smtp:
                smtp.send_message(msg)
        except (OSError, smtplib.SMTPException) as exc:
            raise ExecutionError(f"No se pudo enviar el correo a {to}: {exc}") from exc
