import pytest

from commandflow.errors import LexicalError
from commandflow.lexer import tokenize
from commandflow.tokens import TokenType as T


def types(src):
    return [t.type for t in tokenize(src)]


def test_encender_led1():
    assert types("ENCENDER led1") == [T.ENCENDER, T.IDENT, T.EOF]


def test_palabras_reservadas_insensibles_a_mayusculas():
    assert types("encender led1") == types("ENCENDER led1")
    assert types("Si led1 == encendido entonces apagar led1")[0] is T.SI


def test_identificadores_sensibles_a_mayusculas():
    toks = tokenize("APAGAR LED1")
    assert toks[1].value == "LED1"


def test_cadena_y_numero_y_operadores():
    toks = tokenize('REPETIR 3 VECES NOTIFICAR "hola mundo"\nSI a != APAGADO')
    kinds = [t.type for t in toks]
    assert T.NUMBER in kinds and T.STRING in kinds and T.NEQ in kinds and T.NEWLINE in kinds
    assert [t.value for t in toks if t.type is T.STRING] == ["hola mundo"]


def test_comentarios_se_ignoran():
    assert types("# solo comentario\nAPAGAR led1  # fin") == [T.NEWLINE, T.APAGAR, T.IDENT, T.EOF]


def test_posicion_de_tokens():
    toks = tokenize("APAGAR\n  led1")
    assert (toks[2].line, toks[2].col) == (2, 3)


@pytest.mark.parametrize("src,fragment", [
    ("ENCENDER led1 @", "no reconocido"),
    ('NOTIFICAR "hola', "sin cerrar"),
    ("SI led1 = ENCENDIDO", "=="),
    ("ENCENDER 1led", "mal formado"),
    ("ENCENDER led!", "!="),
])
def test_errores_lexicos(src, fragment):
    with pytest.raises(LexicalError) as e:
        tokenize(src)
    assert fragment in e.value.message


def test_error_lexico_trae_posicion():
    with pytest.raises(LexicalError) as e:
        tokenize("ENCENDER led1 @")
    assert (e.value.line, e.value.column) == (1, 15)
