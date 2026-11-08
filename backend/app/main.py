"""API REST de CommandFlow (FastAPI). Documentación interactiva en /docs."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from commandflow import SmtpEmailService

from .config import Settings
from .db import init_db, make_engine
from .schemas import (CompileResponse, DeviceOut, EmailItem, ExecuteResponse, HistoryItem,
                      NotificationItem, SourceRequest, StateEventItem)
from .service import CommandService


def create_app(settings: Settings | None = None, email_service=None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    email = email_service or SmtpEmailService(settings.smtp_host, settings.smtp_port)
    service = CommandService(session_factory, email)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        init_db(engine)
        yield
        engine.dispose()

    app = FastAPI(title="CommandFlow API", version="1.0.0", lifespan=lifespan,
                  description="Intérprete de instrucciones: léxico → sintaxis → semántica → IR → "
                              "optimizador → máquina virtual, con persistencia en PostgreSQL.")
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins),
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/api/health", tags=["sistema"])
    def health():
        with session_factory() as s:
            s.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}

    @app.get("/api/config", tags=["sistema"])
    def config():
        """Configuración visible para la interfaz. Nunca incluye usuario ni contraseña del SMTP."""
        host = getattr(email, "host", "en memoria")
        local = host in ("localhost", "127.0.0.1", "::1", "mailpit", "en memoria")
        return {
            "mailpit_ui_url": settings.mailpit_ui_url,
            "max_source_chars": settings.max_source_chars,
            "email": {"host": host, "port": getattr(email, "port", None), "real": not local,
                      "authenticated": bool(getattr(email, "user", "")),
                      "encrypted": bool(getattr(email, "starttls", False) or getattr(email, "ssl", False))},
        }

    @app.get("/api/devices", response_model=list[DeviceOut], tags=["dispositivos"])
    def devices():
        return service.devices()

    @app.post("/api/devices/reset", response_model=list[DeviceOut], tags=["dispositivos"])
    def reset_devices():
        return service.reset_devices()

    @app.post("/api/commands", response_model=ExecuteResponse, tags=["comandos"],
              summary="Compila y ejecuta un programa")
    def run_commands(req: SourceRequest):
        """Los errores del lenguaje devuelven HTTP 200 con `ok=false` y la lista de errores;
        un programa con errores no ejecuta ninguna instrucción."""
        return service.execute(req.source, req.optimize, req.preserve_events)

    @app.post("/api/compile", response_model=CompileResponse, tags=["comandos"],
              summary="Valida y genera IR sin ejecutar")
    def compile_only(req: SourceRequest):
        return service.compile_only(req.source, req.optimize, req.preserve_events)

    @app.get("/api/history", response_model=list[HistoryItem], tags=["historial"])
    def history(limit: int = Query(50, ge=1, le=500)):
        return service.history(limit)

    @app.delete("/api/history", status_code=204, tags=["historial"])
    def clear_history():
        service.clear_history()

    @app.get("/api/events", response_model=list[StateEventItem], tags=["historial"])
    def events(limit: int = Query(100, ge=1, le=1000)):
        return service.events(limit)

    @app.get("/api/notifications", response_model=list[NotificationItem], tags=["historial"],
             summary="Notificaciones generadas con NOTIFICAR")
    def notifications(limit: int = Query(50, ge=1, le=500)):
        return service.notifications(limit)

    @app.get("/api/emails", response_model=list[EmailItem], tags=["historial"],
             summary="Intentos de envío de correo (status: sent | failed)")
    def emails(limit: int = Query(50, ge=1, le=500)):
        return service.emails(limit)

    # Interfaz web compilada: se sirve al final para que las rutas /api y /docs tengan prioridad.
    static = Path(settings.static_dir)
    if (static / "index.html").is_file():
        app.mount("/", StaticFiles(directory=static, html=True), name="ui")

    return app


app = create_app()
