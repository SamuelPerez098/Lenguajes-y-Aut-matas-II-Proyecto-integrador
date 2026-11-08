"""Máquina virtual que ejecuta el IR sobre la tabla de símbolos."""
from dataclasses import dataclass, field

from .errors import ExecutionError
from .ir import Instr
from .services import EmailService
from .symbols import STATE_TO_ES, SymbolTable


@dataclass
class Output:
    kind: str   # consulta | listado | notificacion | correo
    text: str
    detail: str = ""   # dato crudo: mensaje de la notificación o destinatario del correo


@dataclass
class StateChange:
    device: str
    old: str
    new: str

    def __str__(self) -> str:
        return f"{self.device}: {STATE_TO_ES[self.old]} → {STATE_TO_ES[self.new]}"


@dataclass
class Trace:
    outputs: list = field(default_factory=list)
    events: list = field(default_factory=list)
    steps: int = 0


class VirtualMachine:
    def __init__(self, table: SymbolTable, email_service: EmailService, max_steps: int = 10_000):
        self.table = table
        self.email = email_service
        self.max_steps = max_steps
        self.trace = Trace()

    def run(self, code: list[Instr]) -> Trace:
        self.trace = Trace()
        labels = {ins.args[0]: i for i, ins in enumerate(code) if ins.op == "LABEL"}
        regs: dict[str, str | bool] = {}
        pc = 0
        while pc < len(code):
            self.trace.steps += 1
            if self.trace.steps > self.max_steps:
                raise ExecutionError("Se excedió el máximo de pasos de ejecución.")
            ins = code[pc]
            pc += 1
            op, a = ins.op, ins.args
            if op == "LABEL":
                continue
            if op == "HALT":
                break
            if op == "GET_STATE":
                regs[a[0]] = self._device(a[1], ins).state
            elif op == "COMPARE":
                lhs = self._value(a[1], regs)
                rhs = self._value(a[3], regs)
                regs[a[0]] = (lhs == rhs) if a[2] == "==" else (lhs != rhs)
            elif op == "JUMP_IF_FALSE":
                if not regs[a[0]]:
                    pc = labels[a[1]]
            elif op == "SET_STATE":
                self._set_state(a[0], a[1], ins)
            elif op == "QUERY":
                d = self._device(a[0], ins)
                self.trace.outputs.append(Output("consulta", f"{d.id} ({d.type.name}): {d.state_es}"))
            elif op == "LIST_DEVICES":
                rows = [f"{d.id:<14}{d.type.name:<12}{d.state_es}" for d in self.table.devices()]
                self.trace.outputs.append(Output("listado", "\n".join(rows)))
            elif op == "NOTIFY":
                self.trace.outputs.append(Output("notificacion", f"Notificación registrada: {a[0]}", a[0]))
            elif op == "SEND_EMAIL":
                self.email.send(a[0], a[1])
                self.trace.outputs.append(Output("correo", f"Correo enviado a {a[0]}", a[0]))
            else:
                raise ExecutionError(f"Instrucción IR desconocida: {op}", ins.line)
        return self.trace

    # --- auxiliares -------------------------------------------------
    def _device(self, dev_id: str, ins: Instr):
        dev = self.table.lookup(dev_id)
        if dev is None:
            raise ExecutionError(f"Dispositivo inexistente en tiempo de ejecución: {dev_id}", ins.line)
        return dev

    @staticmethod
    def _value(operand: str, regs: dict):
        return regs[operand] if operand.startswith("%") else operand

    def _set_state(self, dev_id: str, state: str, ins: Instr) -> None:
        dev = self._device(dev_id, ins)
        if state not in dev.type.states:
            raise ExecutionError(f"Estado '{state}' inválido para {dev.id}", ins.line)
        if dev.state != state:   # idempotente: asignar el mismo estado no genera evento
            self.trace.events.append(StateChange(dev.id, dev.state, state))
            self.table.set_state(dev.id, state)
