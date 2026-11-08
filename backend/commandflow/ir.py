"""Código intermedio (IR) de tres direcciones y su generador.

Conjunto de instrucciones
  GET_STATE dst dev          dst <- estado actual de dev
  COMPARE dst lhs op rhs     dst <- (lhs op rhs); op es == o !=
  JUMP_IF_FALSE cond label   salta a label si cond es falso
  LABEL name                 destino de saltos (pseudo-instrucción)
  SET_STATE dev state        asigna estado canónico (ON/OFF/ACTIVE/INACTIVE)
  QUERY dev                  emite el estado de dev como salida
  LIST_DEVICES               emite el listado de dispositivos
  NOTIFY msg                 registra una notificación
  SEND_EMAIL to msg          solicita envío de correo (efecto externo)
  HALT                       fin de ejecución
Los registros temporales se escriben con prefijo % (p. ej. %t0).
"""
import json
from dataclasses import dataclass, field

from . import ast_nodes as ast
from .symbols import ES_TO_STATE, OPERATION_TARGET

_QUOTED_OPS = {"NOTIFY", "SEND_EMAIL"}


@dataclass(frozen=True)
class Instr:
    op: str
    args: tuple = ()
    line: int = field(default=0, compare=False)

    def __str__(self) -> str:
        if self.op in _QUOTED_OPS:
            args = [json.dumps(a, ensure_ascii=False) for a in self.args]
        else:
            args = list(self.args)
        return " ".join([self.op, *args])


def format_program(code: list[Instr]) -> str:
    return "\n".join(str(i) if i.op == "LABEL" else f"    {i}" for i in code)


class IRGenerator:
    def __init__(self):
        self._temps = 0
        self._labels = 0
        self.code: list[Instr] = []

    def generate(self, program: ast.Program) -> list[Instr]:
        self._temps = self._labels = 0
        self.code = []
        for node in program.instructions:
            self._node(node)
        self._emit("HALT")
        return self.code

    def _emit(self, op: str, *args: str, line: int = 0) -> None:
        self.code.append(Instr(op, tuple(args), line))

    def _temp(self) -> str:
        t = f"%t{self._temps}"
        self._temps += 1
        return t

    def _label(self) -> str:
        n = f"L{self._labels}"
        self._labels += 1
        return n

    def _node(self, node: ast.Node) -> None:
        ln = node.line
        if isinstance(node, ast.DeviceCommand):
            self._emit("SET_STATE", node.device, OPERATION_TARGET[node.operation], line=ln)
        elif isinstance(node, ast.ConsultCommand):
            self._emit("QUERY", node.device, line=ln)
        elif isinstance(node, ast.ListCommand):
            self._emit("LIST_DEVICES", line=ln)
        elif isinstance(node, ast.NotifyCommand):
            self._emit("NOTIFY", node.message, line=ln)
        elif isinstance(node, ast.SendEmailCommand):
            self._emit("SEND_EMAIL", node.recipient, node.message, line=ln)
        elif isinstance(node, ast.IfStatement):
            c = node.condition
            current, result, end = self._temp(), self._temp(), self._label()
            self._emit("GET_STATE", current, c.device, line=ln)
            self._emit("COMPARE", result, current, c.operator, ES_TO_STATE[c.state], line=ln)
            self._emit("JUMP_IF_FALSE", result, end, line=ln)
            self._node(node.body)
            self._emit("LABEL", end, line=ln)
        elif isinstance(node, ast.RepeatStatement):
            for _ in range(node.count):   # desenrollado: simple y optimizable
                self._node(node.body)
        else:
            raise TypeError(f"Nodo desconocido: {type(node).__name__}")
