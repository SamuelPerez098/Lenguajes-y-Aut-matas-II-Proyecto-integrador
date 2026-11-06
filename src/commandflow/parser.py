"""Analizador sintáctico descendente recursivo (LL(1)) que construye el AST."""
from . import ast_nodes as ast
from .errors import SyntacticError
from .tokens import DEVICE_COMMANDS, Token, TokenType as T

_INSTRUCTIONS_HINT = ("ENCENDER, APAGAR, ACTIVAR, DESACTIVAR, CONSULTAR, LISTAR, "
                      "NOTIFICAR, ENVIAR, SI o REPETIR")


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # --- utilidades -------------------------------------------------
    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _check(self, *types: T) -> bool:
        return self._peek().type in types

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type is not T.EOF:
            self.pos += 1
        return tok

    def _error(self, expectation: str) -> SyntacticError:
        tok = self._peek()
        return SyntacticError(f"{expectation}; se encontró {tok.describe()}.", tok.line, tok.col)

    def _expect(self, ttype: T, expectation: str) -> Token:
        if not self._check(ttype):
            raise self._error(expectation)
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._check(T.NEWLINE):
            self._advance()

    # --- programa ---------------------------------------------------
    def parse(self) -> ast.Program:
        instructions = []
        self._skip_newlines()
        while not self._check(T.EOF):
            instructions.append(self._instruction())
            if not self._check(T.NEWLINE, T.EOF):
                raise self._error("Se esperaba el fin de la instrucción")
            self._skip_newlines()
        return ast.Program(instructions, line=1, col=1)

    # --- instrucciones ----------------------------------------------
    def _instruction(self) -> ast.Node:
        tok = self._peek()
        if tok.type in DEVICE_COMMANDS:
            return self._device_command()
        if tok.type is T.CONSULTAR:
            return self._consult()
        if tok.type is T.LISTAR:
            return self._list()
        if tok.type is T.NOTIFICAR:
            return self._notify()
        if tok.type is T.ENVIAR:
            return self._send_email()
        if tok.type is T.SI:
            return self._if()
        if tok.type is T.REPETIR:
            return self._repeat()
        raise self._error(f"Se esperaba una instrucción ({_INSTRUCTIONS_HINT})")

    def _device_command(self) -> ast.DeviceCommand:
        tok = self._advance()
        name = tok.value
        dev = self._expect(T.IDENT, f"Se esperaba un identificador de dispositivo después de {name}")
        return ast.DeviceCommand(name, dev.value, line=tok.line, col=tok.col)

    def _consult(self) -> ast.ConsultCommand:
        tok = self._advance()
        dev = self._expect(T.IDENT, "Se esperaba un identificador de dispositivo después de CONSULTAR")
        return ast.ConsultCommand(dev.value, line=tok.line, col=tok.col)

    def _list(self) -> ast.ListCommand:
        tok = self._advance()
        self._expect(T.DISPOSITIVOS, "Se esperaba DISPOSITIVOS después de LISTAR")
        return ast.ListCommand(line=tok.line, col=tok.col)

    def _notify(self) -> ast.NotifyCommand:
        tok = self._advance()
        msg = self._expect(T.STRING, "Se esperaba un mensaje entre comillas después de NOTIFICAR")
        return ast.NotifyCommand(msg.value, line=tok.line, col=tok.col)

    def _send_email(self) -> ast.SendEmailCommand:
        tok = self._advance()
        self._expect(T.CORREO, "Se esperaba CORREO después de ENVIAR")
        self._expect(T.A, "Se esperaba A (destinatario) después de ENVIAR CORREO")
        to = self._expect(T.STRING, "Se esperaba la dirección de correo entre comillas")
        self._expect(T.MENSAJE, "Se esperaba MENSAJE después del destinatario")
        msg = self._expect(T.STRING, "Se esperaba el texto del mensaje entre comillas")
        return ast.SendEmailCommand(to.value, msg.value, line=tok.line, col=tok.col)

    def _if(self) -> ast.IfStatement:
        tok = self._advance()
        cond = self._condition()
        self._expect(T.ENTONCES, "Se esperaba ENTONCES después de la condición")
        body = self._instruction()
        return ast.IfStatement(cond, body, line=tok.line, col=tok.col)

    def _condition(self) -> ast.Condition:
        dev = self._expect(T.IDENT, "Se esperaba un identificador de dispositivo después de SI")
        if not self._check(T.EQ, T.NEQ):
            raise self._error("Se esperaba '==' o '!=' después del dispositivo")
        op = self._advance()
        state = self._expect(
            T.ESTADO, "Se esperaba un estado (ENCENDIDO, APAGADO, ACTIVADA o DESACTIVADA)")
        return ast.Condition(dev.value, op.lexeme, state.value, line=dev.line, col=dev.col)

    def _repeat(self) -> ast.RepeatStatement:
        tok = self._advance()
        n = self._expect(T.NUMBER, "Se esperaba un número de repeticiones después de REPETIR")
        self._expect(T.VECES, "Se esperaba VECES después del número")
        body = self._instruction()
        return ast.RepeatStatement(n.value, body, line=tok.line, col=tok.col)


def parse(tokens: list[Token]) -> ast.Program:
    return Parser(tokens).parse()
