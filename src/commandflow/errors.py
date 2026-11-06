"""Jerarquía de errores del lenguaje. Cada etapa del pipeline lanza el suyo."""


class CommandFlowError(Exception):
    kind = "general"

    def __init__(self, message: str, line: int = 0, column: int = 0):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def format(self) -> str:
        pos = f" (línea {self.line}, columna {self.column})" if self.line else ""
        return f"Error {self.kind}{pos}: {self.message}"

    def to_dict(self) -> dict:
        return {"tipo": self.kind, "mensaje": self.message,
                "linea": self.line, "columna": self.column}

    def __str__(self) -> str:
        return self.format()


class LexicalError(CommandFlowError):
    kind = "léxico"


class SyntacticError(CommandFlowError):
    kind = "sintáctico"


class SemanticError(CommandFlowError):
    kind = "semántico"


class ExecutionError(CommandFlowError):
    kind = "de ejecución"
