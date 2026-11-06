"""Definición de tokens del lenguaje CommandFlow."""
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    # Palabras reservadas (insensibles a mayúsculas)
    ENCENDER = "ENCENDER"
    APAGAR = "APAGAR"
    ACTIVAR = "ACTIVAR"
    DESACTIVAR = "DESACTIVAR"
    CONSULTAR = "CONSULTAR"
    LISTAR = "LISTAR"
    DISPOSITIVOS = "DISPOSITIVOS"
    NOTIFICAR = "NOTIFICAR"
    ENVIAR = "ENVIAR"
    CORREO = "CORREO"
    A = "A"
    MENSAJE = "MENSAJE"
    SI = "SI"
    ENTONCES = "ENTONCES"
    REPETIR = "REPETIR"
    VECES = "VECES"
    # Literales de estado
    ESTADO = "ESTADO"
    # Otros
    IDENT = "IDENT"
    STRING = "STRING"
    NUMBER = "NUMBER"
    EQ = "=="
    NEQ = "!="
    NEWLINE = "SALTO_LINEA"
    EOF = "EOF"


_NON_KEYWORDS = {
    TokenType.ESTADO, TokenType.IDENT, TokenType.STRING, TokenType.NUMBER,
    TokenType.EQ, TokenType.NEQ, TokenType.NEWLINE, TokenType.EOF,
}
KEYWORDS = {t.value: t for t in TokenType if t not in _NON_KEYWORDS}
STATE_WORDS = ("ENCENDIDO", "APAGADO", "ACTIVADA", "DESACTIVADA")

DEVICE_COMMANDS = {
    TokenType.ENCENDER, TokenType.APAGAR, TokenType.ACTIVAR, TokenType.DESACTIVAR,
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    line: int
    col: int
    value: object = None

    def describe(self) -> str:
        if self.type in (TokenType.NEWLINE, TokenType.EOF):
            return "fin de instrucción"
        if self.type is TokenType.STRING:
            return f'la cadena "{self.value}"'
        return f"'{self.lexeme}'"
