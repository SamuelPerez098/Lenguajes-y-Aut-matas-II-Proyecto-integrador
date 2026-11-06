"""Optimizaciones sobre el IR. Ver docs/DOCUMENTACION_TECNICA.md §9 para la justificación.

Contrato observable: estado final de los dispositivos y la secuencia ordenada de
salidas (QUERY, LIST_DEVICES, NOTIFY, SEND_EMAIL). El registro de transiciones
intermedias es una traza de depuración y NO forma parte del contrato.
"""
from dataclasses import dataclass

from .ir import Instr

# Instrucciones que cortan una región lineal o la hacen observable.
_ALWAYS_BARRIER = {"LABEL", "JUMP_IF_FALSE", "NOTIFY", "SEND_EMAIL", "LIST_DEVICES", "HALT"}


@dataclass
class OptimizationNote:
    name: str
    removed: Instr
    reason: str


@dataclass
class OptimizationResult:
    code: list
    notes: list


def eliminate_redundant_sets(code: list[Instr]) -> tuple[list[Instr], list[OptimizationNote]]:
    """Opt. 1: quita SET_STATE cuando el dispositivo ya tiene ese estado (conocido) en la región."""
    known: dict[str, str] = {}
    out, notes = [], []
    for ins in code:
        if ins.op == "LABEL":          # punto de unión: se pierde el conocimiento
            known.clear()
        elif ins.op == "SET_STATE":
            dev, state = ins.args
            if known.get(dev) == state:
                notes.append(OptimizationNote(
                    "instrucción redundante", ins, f"{dev} ya estaba en {state}"))
                continue
            known[dev] = state
        out.append(ins)
    return out, notes


def _is_barrier(ins: Instr, dev: str) -> bool:
    if ins.op in _ALWAYS_BARRIER:
        return True
    if ins.op in ("GET_STATE", "QUERY"):
        return ins.args[-1] == dev      # lectura del mismo dispositivo
    return False


def eliminate_overwritten_sets(code: list[Instr]) -> tuple[list[Instr], list[OptimizationNote]]:
    """Opt. 2: quita un SET_STATE si otro posterior del mismo dispositivo lo sobrescribe
    sin lecturas, saltos, etiquetas ni efectos externos entre ambos."""
    dead: set[int] = set()
    notes = []
    for i, ins in enumerate(code):
        if ins.op != "SET_STATE":
            continue
        dev = ins.args[0]
        for later in code[i + 1:]:
            if later.op == "SET_STATE" and later.args[0] == dev:
                dead.add(i)
                notes.append(OptimizationNote(
                    "asignación sobrescrita", ins, f"{dev} se reasigna antes de ser observado"))
                break
            if _is_barrier(later, dev):
                break
    return [c for i, c in enumerate(code) if i not in dead], notes


class Optimizer:
    def __init__(self, redundant: bool = True, overwritten: bool = True):
        self.redundant = redundant
        self.overwritten = overwritten

    def optimize(self, code: list[Instr]) -> OptimizationResult:
        notes: list[OptimizationNote] = []
        if self.redundant:
            code, n = eliminate_redundant_sets(code)
            notes += n
        if self.overwritten:
            code, n = eliminate_overwritten_sets(code)
            notes += n
        return OptimizationResult(code, notes)
