"""Configuración por variables de entorno y archivo `.env` (ver .env.example en la raíz del repositorio)."""
import os
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve()
BACKEND_DIR = _HERE.parents[1]
REPO_DIR = _HERE.parents[2]


def load_dotenv(paths: list[Path] | None = None) -> list[Path]:
    """Carga archivos `.env` sencillos (CLAVE=valor). Las variables ya definidas en el entorno
    tienen prioridad. Devuelve los archivos leídos."""
    candidates = paths if paths is not None else [Path.cwd() / ".env", BACKEND_DIR / ".env", REPO_DIR / ".env"]
    loaded, seen = [], set()
    for path in candidates:
        if not path.is_file() or path.resolve() in seen:
            continue
        seen.add(path.resolve())
        for raw in path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            elif " #" in value:                      # comentario al final de la línea
                value = value.split(" #", 1)[0].strip()
            os.environ.setdefault(key.strip(), value)
        loaded.append(path)
    return loaded


load_dotenv()


def _csv(name: str, default: str) -> tuple:
    return tuple(o.strip() for o in os.getenv(name, default).split(",") if o.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./commandflow.db"))
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "localhost"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "1025")))
    cors_origins: tuple = field(default_factory=lambda: _csv("CORS_ORIGINS", "http://localhost:5173"))
    mailpit_ui_url: str = field(default_factory=lambda: os.getenv("MAILPIT_UI_URL", "http://localhost:8025"))
    # Carpeta con la interfaz compilada (npm run build:backend). Si existe, la API también la sirve en "/".
    static_dir: str = field(default_factory=lambda: os.getenv("STATIC_DIR", str(BACKEND_DIR / "static")))
    max_source_chars: int = 5000
