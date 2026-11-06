"""Nodos del árbol sintáctico abstracto (AST)."""
from dataclasses import dataclass, field, fields


@dataclass(kw_only=True)
class Node:
    line: int = field(default=0, compare=False)
    col: int = field(default=0, compare=False)

    def to_dict(self) -> dict:
        d = {"nodo": type(self).__name__}
        for f in fields(self):
            if f.name in ("line", "col"):
                continue
            d[f.name] = _convert(getattr(self, f.name))
        return d


def _convert(value):
    if isinstance(value, Node):
        return value.to_dict()
    if isinstance(value, list):
        return [_convert(v) for v in value]
    return value


@dataclass
class Program(Node):
    instructions: list = field(default_factory=list)


@dataclass
class DeviceCommand(Node):
    operation: str = ""   # ENCENDER | APAGAR | ACTIVAR | DESACTIVAR
    device: str = ""


@dataclass
class ConsultCommand(Node):
    device: str = ""


@dataclass
class ListCommand(Node):
    pass


@dataclass
class NotifyCommand(Node):
    message: str = ""


@dataclass
class SendEmailCommand(Node):
    recipient: str = ""
    message: str = ""


@dataclass
class Condition(Node):
    device: str = ""
    operator: str = "=="  # == | !=
    state: str = ""       # ENCENDIDO | APAGADO | ACTIVADA | DESACTIVADA


@dataclass
class IfStatement(Node):
    condition: Condition = None
    body: Node = None


@dataclass
class RepeatStatement(Node):
    count: int = 0
    body: Node = None


def pretty(node: Node, indent: int = 0) -> str:
    """Representación en árbol, útil para documentación y depuración."""
    pad = "  " * indent
    scalars, children = [], []
    for f in fields(node):
        if f.name in ("line", "col"):
            continue
        v = getattr(node, f.name)
        if isinstance(v, Node):
            children.append((f.name, [v]))
        elif isinstance(v, list):
            children.append((f.name, v))
        else:
            scalars.append(f"{f.name}={v!r}")
    lines = [f"{pad}{type(node).__name__}({', '.join(scalars)})"]
    for name, items in children:
        lines.append(f"{pad}  .{name}:")
        lines.extend(pretty(i, indent + 2) for i in items)
    return "\n".join(lines)
