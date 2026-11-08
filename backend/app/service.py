"""Capa de servicio: conecta el compilador/VM (paquete `commandflow`) con la base de datos."""
import threading

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from commandflow import CommandFlow
from commandflow.symbols import STATE_TO_ES, SymbolTable

from commandflow.optimizer import Optimizer

from .models import DeviceRow, EmailRow, EventRow, HistoryRow, NotificationRow


class _RecordingEmail:
    """Envuelve el servicio real y recuerda cada intento de envío (entregado o fallido)."""

    def __init__(self, inner):
        self.inner = inner
        self.attempts: list[tuple[str, str, str, str]] = []   # (to, message, status, error)

    def send(self, to: str, message: str) -> None:
        try:
            self.inner.send(to, message)
        except Exception as exc:
            self.attempts.append((to, message, "failed", str(getattr(exc, "message", exc))))
            raise
        self.attempts.append((to, message, "sent", ""))


def _compilation_dict(comp) -> dict:
    return {
        "tokens": [{"line": t.line, "col": t.col, "type": t.type.name, "lexeme": t.lexeme}
                   for t in comp.tokens],
        "ast": comp.ast.to_dict() if comp.ast else None,
        "instructions": comp.instructions,
        "ir": [str(i) for i in comp.ir],
        "optimized_ir": [str(i) for i in comp.optimized_ir],
        "optimizations": [{"name": n.name, "removed": str(n.removed), "line": n.removed.line,
                           "reason": n.reason} for n in comp.optimizations],
    }


def _devices_out(table: SymbolTable) -> list[dict]:
    return [{"id": d.id, "type": d.type.name, "state": d.state, "state_es": d.state_es}
            for d in table.devices()]


class CommandService:
    def __init__(self, session_factory: sessionmaker, email_service):
        self._sf = session_factory
        self._email = email_service
        # Serializa ejecuciones dentro del proceso; entre procesos lo hace SELECT ... FOR UPDATE.
        self._lock = threading.Lock()

    # --- lectura -----------------------------------------------------------
    @staticmethod
    def _load_table(session: Session, lock: bool = False) -> SymbolTable:
        stmt = select(DeviceRow).order_by(DeviceRow.ordinal)
        if lock:
            stmt = stmt.with_for_update()
        table = SymbolTable()
        for row in session.scalars(stmt):
            table.declare(row.id, row.type, row.state)
        return table

    def devices(self) -> list[dict]:
        with self._sf() as s:
            return _devices_out(self._load_table(s))

    @staticmethod
    def _optimizer(preserve_events: bool) -> Optimizer:
        # La optimización 2 elimina cambios transitorios; si la bitácora debe registrar cada
        # cambio, no es válida (enunciado, sección de optimizaciones), así que se desactiva.
        return Optimizer(overwritten=not preserve_events)

    def compile_only(self, source: str, optimize: bool = True, preserve_events: bool = True) -> dict:
        """Valida y genera IR sin ejecutar ni modificar nada."""
        with self._sf() as s:
            cf = CommandFlow(table=self._load_table(s), optimize=optimize,
                             optimizer=self._optimizer(preserve_events))
            comp = cf.compile(source)
        return {"ok": comp.ok, "errors": [e.to_dict() for e in comp.errors],
                "compilation": _compilation_dict(comp)}

    # --- ejecución -----------------------------------------------------------
    def execute(self, source: str, optimize: bool = True, preserve_events: bool = True) -> dict:
        with self._lock, self._sf() as s, s.begin():
            table = self._load_table(s, lock=True)
            recorder = _RecordingEmail(self._email)
            res = CommandFlow(table=table, email_service=recorder, optimize=optimize,
                              optimizer=self._optimizer(preserve_events)).run(source)

            # Se persiste el estado resultante incluso si falló a mitad (p. ej. SMTP caído):
            # los efectos ya aplicados sobre los dispositivos no se pueden "deshacer".
            rows = {r.id: r for r in s.scalars(select(DeviceRow))}
            for dev in table.devices():
                rows[dev.id].state = dev.state

            hist = HistoryRow(
                source=source, ok=res.ok, optimized=optimize,
                errors=[e.to_dict() for e in res.errors],
                outputs=[{"kind": o.kind, "text": o.text} for o in res.outputs],
                events=[str(e) for e in res.events])
            s.add(hist)
            s.flush()
            for ev in res.events:
                s.add(EventRow(history_id=hist.id, device_id=ev.device,
                               old_state=ev.old, new_state=ev.new))
            for to, msg, status, error in recorder.attempts:
                s.add(EmailRow(history_id=hist.id, recipient=to, message=msg, status=status, error=error))
            for out in res.outputs:
                if out.kind == "notificacion":
                    s.add(NotificationRow(history_id=hist.id, message=out.detail))

            return {
                "ok": res.ok, "message": res.message,
                "errors": [e.to_dict() for e in res.errors],
                "outputs": [{"kind": o.kind, "text": o.text, "detail": o.detail} for o in res.outputs],
                "events": [{"device": e.device, "old": STATE_TO_ES[e.old],
                            "new": STATE_TO_ES[e.new], "text": str(e)} for e in res.events],
                "devices": _devices_out(table),
                "history_id": hist.id,
                "compilation": _compilation_dict(res.compilation),
            }

    # --- administración --------------------------------------------------------
    def reset_devices(self) -> list[dict]:
        with self._lock, self._sf() as s, s.begin():
            defaults = {d.id: d.state for d in SymbolTable.default().devices()}
            for row in s.scalars(select(DeviceRow).with_for_update()):
                if row.id in defaults:
                    row.state = defaults[row.id]
            table = self._load_table(s)
        return _devices_out(table)

    def clear_history(self) -> None:
        with self._lock, self._sf() as s, s.begin():
            s.execute(delete(NotificationRow))
            s.execute(delete(EmailRow))
            s.execute(delete(EventRow))
            s.execute(delete(HistoryRow))

    def history(self, limit: int) -> list[HistoryRow]:
        with self._sf() as s:
            return list(s.scalars(select(HistoryRow).order_by(HistoryRow.id.desc()).limit(limit)))

    def events(self, limit: int) -> list[EventRow]:
        with self._sf() as s:
            return list(s.scalars(select(EventRow).order_by(EventRow.id.desc()).limit(limit)))

    def notifications(self, limit: int) -> list[NotificationRow]:
        with self._sf() as s:
            return list(s.scalars(select(NotificationRow).order_by(NotificationRow.id.desc()).limit(limit)))

    def emails(self, limit: int) -> list[EmailRow]:
        with self._sf() as s:
            return list(s.scalars(select(EmailRow).order_by(EmailRow.id.desc()).limit(limit)))
