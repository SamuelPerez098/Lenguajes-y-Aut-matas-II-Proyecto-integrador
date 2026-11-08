import pytest

from commandflow import ast_nodes as ast
from commandflow.errors import SyntacticError
from commandflow.lexer import tokenize
from commandflow.parser import parse


def p(src):
    return parse(tokenize(src))


def test_comando_simple():
    prog = p("ENCENDER led1")
    assert prog.instructions == [ast.DeviceCommand("ENCENDER", "led1")]


def test_correo():
    n = p('ENVIAR CORREO A "a@b.com" MENSAJE "Hola"').instructions[0]
    assert (n.recipient, n.message) == ("a@b.com", "Hola")


def test_varias_lineas_y_lineas_vacias():
    prog = p("\n\nENCENDER led1\n\n\nAPAGAR led2\n")
    assert len(prog.instructions) == 2


def test_programa_vacio():
    assert p("  # nada\n").instructions == []


def test_condicional():
    n = p("SI led1 == ENCENDIDO ENTONCES APAGAR led1").instructions[0]
    assert isinstance(n, ast.IfStatement)
    assert (n.condition.device, n.condition.operator, n.condition.state) == ("led1", "==", "ENCENDIDO")
    assert n.body == ast.DeviceCommand("APAGAR", "led1")


def test_anidamiento():
    n = p("REPETIR 2 VECES SI led1 != APAGADO ENTONCES CONSULTAR led1").instructions[0]
    assert isinstance(n, ast.RepeatStatement) and isinstance(n.body, ast.IfStatement)


def test_to_dict():
    d = p("APAGAR led1").to_dict()
    assert d["instructions"][0] == {"nodo": "DeviceCommand", "operation": "APAGAR", "device": "led1"}


@pytest.mark.parametrize("src,fragment", [
    ("ENCENDER", "identificador de dispositivo después de ENCENDER"),
    ("ENCENDER led1 led2", "fin de la instrucción"),
    ("LISTAR", "DISPOSITIVOS"),
    ('ENVIAR "a@b.com" MENSAJE "x"', "CORREO"),
    ('ENVIAR CORREO "a@b.com" MENSAJE "x"', "A (destinatario)"),
    ('ENVIAR CORREO A "a@b.com" "x"', "MENSAJE"),
    ('ENVIAR CORREO A "a@b.com" MENSAJE', "texto del mensaje"),
    ("SI led1 ENCENDIDO ENTONCES APAGAR led1", "'==' o '!='"),
    ("SI led1 == ENTONCES APAGAR led1", "estado"),
    ("SI led1 == ENCENDIDO APAGAR led1", "ENTONCES"),
    ("SI led1 == ENCENDIDO ENTONCES", "instrucción"),
    ("REPETIR VECES APAGAR led1", "número"),
    ("REPETIR 2 APAGAR led1", "VECES"),
    ('NOTIFICAR', "mensaje entre comillas"),
    ("led1", "una instrucción"),
])
def test_errores_sintacticos(src, fragment):
    with pytest.raises(SyntacticError) as e:
        p(src)
    assert fragment in e.value.message
