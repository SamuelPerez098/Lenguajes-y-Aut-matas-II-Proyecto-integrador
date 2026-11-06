from commandflow import CommandFlow


def errors(src):
    return CommandFlow().compile(src).errors


def test_programa_valido():
    assert errors("ENCENDER led1\nACTIVAR alarma1\nCONSULTAR ventilador1") == []


def test_dispositivo_inexistente():
    (e,) = errors("ENCENDER led99")
    assert "no existe" in e.message and "led99" in e.message


def test_sugerencia_por_mayusculas():
    (e,) = errors("ENCENDER LED1")
    assert "led1" in e.message and "Quiso decir" in e.message


def test_operacion_incompatible():
    (e,) = errors("ENCENDER alarma1")
    assert "ALARMA" in e.message and "ACTIVAR" in e.message
    (e,) = errors("ACTIVAR led1")
    assert "LED" in e.message


def test_estado_fuera_de_dominio():
    (e,) = errors("SI led1 == ACTIVADA ENTONCES APAGAR led1")
    assert "no es válido" in e.message


def test_condicion_con_dispositivo_inexistente():
    (e,) = errors("SI foo == ENCENDIDO ENTONCES APAGAR led1")
    assert "foo" in e.message


def test_correo_invalido():
    assert errors('ENVIAR CORREO A "no-es-correo" MENSAJE "x"')
    assert errors('ENVIAR CORREO A "a@b" MENSAJE "x"')
    assert not errors('ENVIAR CORREO A "a.b+c@dominio.com.mx" MENSAJE "x"')


def test_mensajes_vacios():
    assert errors('NOTIFICAR ""')
    assert errors('ENVIAR CORREO A "a@b.com" MENSAJE "  "')


def test_limites_de_repetir():
    assert errors("REPETIR 0 VECES APAGAR led1")
    assert errors("REPETIR 101 VECES APAGAR led1")
    assert not errors("REPETIR 100 VECES APAGAR led1")


def test_se_reportan_todos_los_errores_semanticos_con_posicion():
    errs = errors("ENCENDER led99\nAPAGAR led1\nENCENDER alarma1")
    assert [e.line for e in errs] == [1, 3]


def test_acciones_semanticas():
    comp = CommandFlow().compile("ENCENDER led1\nSI led1 == ENCENDIDO ENTONCES APAGAR led1")
    assert comp.instructions[0] == {"tipo": "CONTROL_DISPOSITIVO", "operacion": "ENCENDER", "dispositivo": "led1"}
    assert comp.instructions[1]["tipo"] == "CONDICIONAL"
