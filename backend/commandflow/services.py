"""Servicios externos: correo. El VM solo conoce la interfaz EmailService."""
import os
import smtplib
import ssl as ssl_module
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


def _flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "si", "sí")


class SmtpEmailService:
    """Envía por SMTP.

    Modo de pruebas (por defecto): Mailpit en localhost:1025, sin autenticación ni TLS.
    Extensión opcional (proveedor externo): SMTP_USER/SMTP_PASSWORD activan el inicio de sesión;
    SMTP_STARTTLS=true cifra con STARTTLS (puerto 587) y SMTP_SSL=true usa SSL directo (puerto 465).
    El certificado del servidor se verifica siempre, salvo que SMTP_TLS_VERIFY=false (solo para pruebas locales).
    """

    def __init__(self, host: str | None = None, port: int | None = None,
                 sender: str | None = None, user: str | None = None, password: str | None = None,
                 starttls: bool | None = None, ssl: bool | None = None, timeout: float = 10,
                 tls_verify: bool | None = None):
        self.host = host or os.getenv("SMTP_HOST", "localhost")
        self.port = port or int(os.getenv("SMTP_PORT", "1025"))
        self.sender = sender or os.getenv("SMTP_FROM", "commandflow@localhost")
        self.user = user if user is not None else os.getenv("SMTP_USER", "")
        self.password = password if password is not None else os.getenv("SMTP_PASSWORD", "")
        self.starttls = _flag("SMTP_STARTTLS") if starttls is None else starttls
        self.ssl = _flag("SMTP_SSL") if ssl is None else ssl
        if "gmail" in self.host.lower():          # Google muestra la contraseña de aplicación con espacios
            self.password = self.password.replace(" ", "")
        self.timeout = timeout
        self.tls_verify = (os.getenv("SMTP_TLS_VERIFY", "true").strip().lower() not in ("0", "false", "no")
                           if tls_verify is None else tls_verify)

    def _context(self) -> ssl_module.SSLContext:
        ctx = ssl_module.create_default_context()
        if not self.tls_verify:
            ctx.check_hostname = False
            ctx.verify_mode = ssl_module.CERT_NONE
        return ctx

    def send(self, to: str, message: str) -> None:
        msg = EmailMessage()
        msg["From"], msg["To"], msg["Subject"] = self.sender, to, "Notificación de CommandFlow"
        msg.set_content(message)
        where = f"{self.host}:{self.port}"
        try:
            if self.ssl:
                smtp = smtplib.SMTP_SSL(self.host, self.port, timeout=self.timeout, context=self._context())
            else:
                smtp = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            with smtp:
                if self.starttls and not self.ssl:
                    smtp.starttls(context=self._context())
                if self.user:
                    smtp.login(self.user, self.password)
                smtp.send_message(msg)
        except smtplib.SMTPAuthenticationError as exc:
            raise ExecutionError(
                f"No se pudo enviar el correo: {where} rechazó el usuario o la contraseña "
                "(en Gmail se necesita una «contraseña de aplicación», no la contraseña normal).") from exc
        except smtplib.SMTPRecipientsRefused as exc:
            raise ExecutionError(f"No se pudo enviar el correo: {where} rechazó al destinatario {to}.") from exc
        except ConnectionRefusedError as exc:
            raise ExecutionError(
                f"No se pudo enviar el correo a {to}: no hay un servidor SMTP escuchando en {where}. "
                "¿Está Mailpit en ejecución o configuraste SMTP_HOST/SMTP_PORT en el archivo .env?") from exc
        except ssl_module.SSLError as exc:
            raise ExecutionError(
                f"No se pudo enviar el correo a {to}: falló el cifrado TLS con {where} ({exc}). "
                "Revisa SMTP_STARTTLS (puerto 587) o SMTP_SSL (puerto 465).") from exc
        except (OSError, smtplib.SMTPException) as exc:
            raise ExecutionError(f"No se pudo enviar el correo a {to} usando {where}: {exc}") from exc
