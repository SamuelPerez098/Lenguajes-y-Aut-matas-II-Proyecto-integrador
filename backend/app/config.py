"""Configuración por variables de entorno (ver .env.example)."""
import os
from dataclasses import dataclass, field


def _csv(name: str, default: str) -> tuple:
    return tuple(o.strip() for o in os.getenv(name, default).split(",") if o.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./commandflow.db"))
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "localhost"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "1025")))
    cors_origins: tuple = field(default_factory=lambda: _csv("CORS_ORIGINS", "http://localhost:5173"))
    mailpit_ui_url: str = field(default_factory=lambda: os.getenv("MAILPIT_UI_URL", "http://localhost:8025"))
    max_source_chars: int = 5000
