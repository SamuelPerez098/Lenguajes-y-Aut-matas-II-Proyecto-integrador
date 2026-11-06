from commandflow import CommandFlow
from commandflow.ir import Instr


def ir(src, optimize=False):
    return CommandFlow(optimize=optimize).compile(src).optimized_ir


def ops(code):
    return [str(i) for i in code]


def test_ir_comando_simple():
    assert ops(ir("ENCENDER led1")) == ["SET_STATE led1 ON", "HALT"]


def test_ir_condicional():
    code = ir("SI led1 == ENCENDIDO ENTONCES APAGAR led1")
    assert ops(code) == ["GET_STATE %t0 led1", "COMPARE %t1 %t0 == ON",
                         "JUMP_IF_FALSE %t1 L0", "SET_STATE led1 OFF", "LABEL L0", "HALT"]


def test_ir_repetir_desenrolla():
    assert ops(ir("REPETIR 3 VECES NOTIFICAR \"x\"")).count('NOTIFY "x"') == 3


# --- Optimización 1: instrucciones redundantes -------------------------
def test_opt1_elimina_redundante():
    assert ops(ir("ENCENDER led1\nENCENDER led1", True)) == ["SET_STATE led1 ON", "HALT"]


def test_opt1_repetir():
    assert ops(ir("REPETIR 5 VECES ENCENDER led1", True)).count("SET_STATE led1 ON") == 1


def test_opt1_no_cruza_etiquetas():
    code = ir("ENCENDER led1\nSI led2 == ENCENDIDO ENTONCES ENCENDER led1\nENCENDER led1", True)
    # el SET dentro del SI es redundante (fall-through), el de después del LABEL NO
    assert ops(code).count("SET_STATE led1 ON") == 2


# --- Optimización 2: asignaciones sobrescritas --------------------------
def test_opt2_elimina_sobrescrita():
    assert ops(ir("ENCENDER led1\nAPAGAR led1", True)) == ["SET_STATE led1 OFF", "HALT"]


def test_opt2_cadena():
    assert ops(ir("ENCENDER led1\nAPAGAR led1\nENCENDER led1", True)) == ["SET_STATE led1 ON", "HALT"]


def test_opt2_otros_dispositivos_no_interfieren():
    code = ir("ENCENDER led1\nCONSULTAR led2\nAPAGAR led1", True)
    assert ops(code) == ["QUERY led2", "SET_STATE led1 OFF", "HALT"]


def test_opt2_respeta_consulta_del_mismo_dispositivo():
    code = ir("ENCENDER led1\nCONSULTAR led1\nAPAGAR led1", True)
    assert ops(code).count("SET_STATE led1 ON") == 1


def test_opt2_respeta_efectos_externos_y_listado():
    for barrier in ('NOTIFICAR "x"', 'ENVIAR CORREO A "a@b.com" MENSAJE "x"', "LISTAR DISPOSITIVOS"):
        code = ir(f"ENCENDER led1\n{barrier}\nAPAGAR led1", True)
        assert ops(code).count("SET_STATE led1 ON") == 1, barrier


def test_opt2_respeta_condicionales():
    code = ir("ENCENDER led1\nSI led2 == ENCENDIDO ENTONCES APAGAR led1", True)
    assert ops(code).count("SET_STATE led1 ON") == 1


def test_opt2_condicional_lee_el_dispositivo():
    code = ir("ENCENDER led1\nSI led1 == ENCENDIDO ENTONCES APAGAR led1", True)
    assert ops(code).count("SET_STATE led1 ON") == 1


def test_se_reportan_las_optimizaciones():
    comp = CommandFlow().compile("ENCENDER led1\nENCENDER led1\nAPAGAR led2\nENCENDER led2")
    assert {n.name for n in comp.optimizations} == {"instrucción redundante", "asignación sobrescrita"}
    assert all(isinstance(n.removed, Instr) for n in comp.optimizations)
