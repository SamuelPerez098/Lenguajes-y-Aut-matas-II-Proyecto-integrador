"""Análisis semántico: valida que las instrucciones tengan sentido en el contexto.

Comprobaciones estáticas (no dependen del estado actual de los dispositivos):
  * el dispositivo existe en la tabla de símbolos
  * la operación es compatible con el tipo del dispositivo
  * el estado de una condición pertenece al dominio del tipo
  * el destinatario del correo tiene formato válido
  * los mensajes no están vacíos y REPETIR tiene un contador razonable
"""
import re

from . import ast_nodes as ast
from .errors import SemanticError
from .symbols import ES_TO_STATE, STATE_TO_ES, Device, SymbolTable

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
MAX_REPEAT = 100
MAX_EMAIL_LEN = 254      # límite práctico de RFC 5321
MAX_MESSAGE_LEN = 1000   # NOTIFICAR y cuerpo del correo


class SemanticAnalyzer:
    def __init__(self, table: SymbolTable):
        self.table = table
        self.errors: list[SemanticError] = []

    def analyze(self, program: ast.Program) -> list[SemanticError]:
        self.errors = []
        for node in program.instructions:
            self._visit(node)
        return self.errors

    def _err(self, node: ast.Node, message: str) -> None:
        self.errors.append(SemanticError(message, node.line, node.col))

    # --- acciones semánticas ---------------------------------------
    def verificar_dispositivo(self, name: str, node: ast.Node) -> Device | None:
        dev = self.table.lookup(name)
        if dev is not None:
            return dev
        hint = ""
        similar = self.table.find_similar(name)
        if similar:
            hint = f" ¿Quiso decir '{similar.id}'? (los identificadores distinguen mayúsculas)"
        available = ", ".join(d.id for d in self.table.devices())
        self._err(node, f"El dispositivo '{name}' no existe.{hint} Disponibles: {available}.")
        return None

    def verificar_operacion(self, operation: str, dev: Device, node: ast.Node) -> bool:
        if operation in dev.type.operations:
            return True
        allowed = ", ".join(dev.type.operations)
        self._err(node, f"'{dev.id}' es de tipo {dev.type.name} y no admite {operation}. "
                        f"Operaciones permitidas: {allowed}.")
        return False

    # --- recorrido --------------------------------------------------
    def _visit(self, node: ast.Node) -> None:
        if isinstance(node, ast.DeviceCommand):
            dev = self.verificar_dispositivo(node.device, node)
            if dev:
                self.verificar_operacion(node.operation, dev, node)
        elif isinstance(node, ast.ConsultCommand):
            dev = self.verificar_dispositivo(node.device, node)
            if dev:
                self.verificar_operacion("CONSULTAR", dev, node)
        elif isinstance(node, ast.NotifyCommand):
            if not node.message.strip():
                self._err(node, "El mensaje de NOTIFICAR no puede estar vacío.")
            elif len(node.message) > MAX_MESSAGE_LEN:
                self._err(node, f"El mensaje de NOTIFICAR excede {MAX_MESSAGE_LEN} caracteres.")
        elif isinstance(node, ast.SendEmailCommand):
            if not EMAIL_RE.match(node.recipient) or len(node.recipient) > MAX_EMAIL_LEN:
                self._err(node, f"La dirección de correo '{node.recipient}' no es válida.")
            if not node.message.strip():
                self._err(node, "El mensaje del correo no puede estar vacío.")
            elif len(node.message) > MAX_MESSAGE_LEN:
                self._err(node, f"El mensaje del correo excede {MAX_MESSAGE_LEN} caracteres.")
        elif isinstance(node, ast.IfStatement):
            self._condition(node.condition)
            self._visit(node.body)
        elif isinstance(node, ast.RepeatStatement):
            if not 1 <= node.count <= MAX_REPEAT:
                self._err(node, f"REPETIR admite entre 1 y {MAX_REPEAT} veces (se pidió {node.count}).")
            self._visit(node.body)

    def _condition(self, cond: ast.Condition) -> None:
        dev = self.verificar_dispositivo(cond.device, cond)
        if dev and ES_TO_STATE[cond.state] not in dev.type.states:
            valid = ", ".join(STATE_TO_ES[s] for s in dev.type.states)
            self._err(cond, f"El estado {cond.state} no es válido para '{dev.id}' "
                            f"({dev.type.name}); estados posibles: {valid}.")


def describe_instruction(node: ast.Node) -> dict:
    """Acción semántica `construirInstruccion`: forma normalizada de una instrucción válida."""
    if isinstance(node, ast.DeviceCommand):
        return {"tipo": "CONTROL_DISPOSITIVO", "operacion": node.operation, "dispositivo": node.device}
    if isinstance(node, ast.ConsultCommand):
        return {"tipo": "CONSULTA", "operacion": "CONSULTAR", "dispositivo": node.device}
    if isinstance(node, ast.ListCommand):
        return {"tipo": "LISTADO", "operacion": "LISTAR"}
    if isinstance(node, ast.NotifyCommand):
        return {"tipo": "NOTIFICACION", "mensaje": node.message}
    if isinstance(node, ast.SendEmailCommand):
        return {"tipo": "CORREO", "destinatario": node.recipient, "mensaje": node.message}
    if isinstance(node, ast.IfStatement):
        c = node.condition
        return {"tipo": "CONDICIONAL",
                "condicion": {"dispositivo": c.device, "operador": c.operator, "estado": c.state},
                "entonces": describe_instruction(node.body)}
    if isinstance(node, ast.RepeatStatement):
        return {"tipo": "REPETICION", "veces": node.count, "cuerpo": describe_instruction(node.body)}
    raise TypeError(f"Nodo desconocido: {type(node).__name__}")
