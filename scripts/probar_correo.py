#!/usr/bin/env python3
"""Prueba el envío de correo con la configuración del archivo .env.

    python scripts/probar_correo.py destino@correo.com

Muestra qué servidor se usa y, si falla, el motivo exacto (contraseña, cifrado, servidor apagado...).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import load_dotenv  # noqa: E402  (también carga .env al importarse)
from commandflow import SmtpEmailService  # noqa: E402
from commandflow.errors import ExecutionError  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2 or "@" not in sys.argv[1]:
        print("Uso: python scripts/probar_correo.py destino@correo.com")
        return 2
    to = sys.argv[1]
    files = load_dotenv()
    svc = SmtpEmailService()
    user = (svc.user[:2] + "***" + svc.user[svc.user.find("@"):]) if "@" in svc.user else (svc.user or "(sin usuario)")
    print("Archivos .env leídos :", ", ".join(map(str, files)) or "ninguno")
    print(f"Servidor SMTP        : {svc.host}:{svc.port}")
    print(f"Cifrado              : {'SSL' if svc.ssl else 'STARTTLS' if svc.starttls else 'ninguno'}")
    print(f"Usuario / remitente  : {user} / {svc.sender}")
    print(f"Enviando a           : {to} ...")
    try:
        svc.send(to, "Correo de prueba enviado desde CommandFlow. Si lo lees, el envío real funciona.")
    except ExecutionError as exc:
        print("\nFALLÓ:", exc.message)
        return 1
    print("\nOK: el servidor aceptó el correo. Revisa la bandeja de entrada (y la carpeta de spam).")
    if svc.host in ("localhost", "127.0.0.1", "mailpit"):
        print("Estás usando la bandeja de PRUEBAS: míralo en http://localhost:8025, no llega a Internet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
