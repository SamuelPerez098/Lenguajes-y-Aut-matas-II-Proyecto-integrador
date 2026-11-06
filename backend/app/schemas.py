"""Esquemas Pydantic de la API (también alimentan la documentación en /docs)."""
from datetime import datetime

from pydantic import BaseModel, Field

from .config import Settings

MAX = Settings().max_source_chars


class SourceRequest(BaseModel):
    source: str = Field(max_length=MAX, description="Programa CommandFlow (una instrucción por línea)")
    optimize: bool = True


class DeviceOut(BaseModel):
    id: str
    type: str
    state: str
    state_es: str


class ErrorOut(BaseModel):
    tipo: str
    mensaje: str
    linea: int
    columna: int


class OutputOut(BaseModel):
    kind: str
    text: str


class EventOut(BaseModel):
    device: str
    old: str
    new: str
    text: str


class TokenOut(BaseModel):
    line: int
    col: int
    type: str
    lexeme: str


class OptimizationOut(BaseModel):
    name: str
    removed: str
    line: int
    reason: str


class CompilationOut(BaseModel):
    tokens: list[TokenOut]
    ast: dict | None
    instructions: list[dict]
    ir: list[str]
    optimized_ir: list[str]
    optimizations: list[OptimizationOut]


class CompileResponse(BaseModel):
    ok: bool
    errors: list[ErrorOut]
    compilation: CompilationOut


class ExecuteResponse(CompileResponse):
    message: str
    outputs: list[OutputOut]
    events: list[EventOut]
    devices: list[DeviceOut]
    history_id: int


class HistoryItem(BaseModel):
    id: int
    source: str
    ok: bool
    optimized: bool
    errors: list[dict]
    outputs: list[dict]
    events: list[str]
    created_at: datetime


class StateEventItem(BaseModel):
    id: int
    history_id: int
    device_id: str
    old_state: str
    new_state: str
    created_at: datetime


class EmailItem(BaseModel):
    id: int
    history_id: int
    recipient: str
    message: str
    created_at: datetime
