"""Motor de base de datos, creación de tablas y datos iniciales."""
import time

from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from commandflow.symbols import DEVICE_TYPES, SymbolTable

from .models import Base, DeviceRow


def make_engine(url: str):
    if url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url or url in ("sqlite://", "sqlite:///"):
            kwargs["poolclass"] = StaticPool
        return create_engine(url, **kwargs)
    return create_engine(url, pool_pre_ping=True)


def seed_devices(session: Session) -> None:
    """Crea los dispositivos iniciales y reconcilia una base de datos de una versión anterior:
    elimina dispositivos de tipos que ya no existen (p. ej. el antiguo VENTILADOR) y agrega los que falten."""
    existing = {row.id: row for row in session.scalars(select(DeviceRow))}
    for row in list(existing.values()):
        if row.type not in DEVICE_TYPES:
            session.delete(row)
            del existing[row.id]
    for i, dev in enumerate(SymbolTable.default().devices()):
        if dev.id not in existing:
            session.add(DeviceRow(id=dev.id, type=dev.type.name, state=dev.state, ordinal=i))


def init_db(engine, retries: int = 30, delay: float = 1.0) -> None:
    """Crea tablas y siembra dispositivos. Reintenta mientras PostgreSQL termina de arrancar."""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(engine)
            break
        except OperationalError:
            if attempt == retries:
                raise
            time.sleep(delay)
    with Session(engine) as session, session.begin():
        seed_devices(session)
