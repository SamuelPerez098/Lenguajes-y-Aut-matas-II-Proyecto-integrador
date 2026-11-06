"""Analizador léxico: convierte el texto fuente en una lista de tokens."""
from .errors import LexicalError
from .tokens import KEYWORDS, STATE_WORDS, Token, TokenType


class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.col = 1

    # --- utilidades -------------------------------------------------
    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.src[i] if i < len(self.src) else ""

    def _advance(self) -> str:
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    @staticmethod
    def _is_letter(ch: str) -> bool:
        return bool(ch) and ch.isascii() and (ch.isalpha() or ch == "_")

    @staticmethod
    def _is_digit(ch: str) -> bool:
        return bool(ch) and ch.isascii() and ch.isdigit()

    # --- reconocimiento ---------------------------------------------
    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.pos < len(self.src):
            ch = self._peek()
            line, col = self.line, self.col
            if ch in " \t\r":
                self._advance()
            elif ch == "\n":
                self._advance()
                tokens.append(Token(TokenType.NEWLINE, "\\n", line, col))
            elif ch == "#":  # comentario hasta fin de línea
                while self._peek() not in ("", "\n"):
                    self._advance()
            elif self._is_letter(ch):
                tokens.append(self._word(line, col))
            elif self._is_digit(ch):
                tokens.append(self._number(line, col))
            elif ch == '"':
                tokens.append(self._string(line, col))
            elif ch == "=":
                self._advance()
                if self._peek() != "=":
                    raise LexicalError("Operador '=' incompleto: se esperaba '=='.", line, col)
                self._advance()
                tokens.append(Token(TokenType.EQ, "==", line, col))
            elif ch == "!":
                self._advance()
                if self._peek() != "=":
                    raise LexicalError("Operador '!' incompleto: se esperaba '!='.", line, col)
                self._advance()
                tokens.append(Token(TokenType.NEQ, "!=", line, col))
            else:
                raise LexicalError(f"Carácter '{ch}' no reconocido.", line, col)
        tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return tokens

    def _word(self, line: int, col: int) -> Token:
        start = self.pos
        while self._is_letter(self._peek()) or self._is_digit(self._peek()):
            self._advance()
        lexeme = self.src[start:self.pos]
        upper = lexeme.upper()
        if upper in KEYWORDS:
            return Token(KEYWORDS[upper], lexeme, line, col, upper)
        if upper in STATE_WORDS:
            return Token(TokenType.ESTADO, lexeme, line, col, upper)
        return Token(TokenType.IDENT, lexeme, line, col, lexeme)

    def _number(self, line: int, col: int) -> Token:
        start = self.pos
        while self._is_digit(self._peek()):
            self._advance()
        if self._is_letter(self._peek()):
            raise LexicalError(
                "Número mal formado: un identificador no puede comenzar con un dígito.",
                line, col)
        lexeme = self.src[start:self.pos]
        return Token(TokenType.NUMBER, lexeme, line, col, int(lexeme))

    def _string(self, line: int, col: int) -> Token:
        self._advance()  # comilla de apertura
        chars: list[str] = []
        while True:
            ch = self._peek()
            if ch in ("", "\n"):
                raise LexicalError("Cadena sin cerrar: falta la comilla de cierre.", line, col)
            self._advance()
            if ch == '"':
                break
            chars.append(ch)
        text = "".join(chars)
        return Token(TokenType.STRING, f'"{text}"', line, col, text)


def tokenize(source: str) -> list[Token]:
    return Lexer(source).tokenize()
