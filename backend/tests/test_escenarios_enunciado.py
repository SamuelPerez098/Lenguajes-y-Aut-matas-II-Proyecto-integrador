"""Los 13 escenarios obligatorios de la sección 16 del enunciado, con su entrada literal."""
import pytest

from commandflow import CommandFlow, InMemoryEmailService


@pytest.fixture
def cf():
    return CommandFlow(email_service=InMemoryEmailService())


def dev(cf, name):
    return cf.table.lookup(name).state


def test_01_encender_led1(cf):
    assert cf.run("ENCENDER led1").ok and dev(cf, "led1") == "ON"


def test_02_apagar_led1(cf):
    cf.run("ENCENDER led1")
    assert cf.run("APAGAR led1").ok and dev(cf, "led1") == "OFF"


def test_03_activar_alarma1(cf):
    cf.run("DESACTIVAR alarma1")
    assert cf.run("ACTIVAR alarma1").ok and dev(cf, "alarma1") == "ACTIVE"


def test_04_desactivar_alarma1(cf):
    assert cf.run("DESACTIVAR alarma1").ok and dev(cf, "alarma1") == "INACTIVE"


def test_05_consultar_led1_devuelve_estado_actual(cf):
    assert cf.run("CONSULTAR led1").outputs[0].text == "led1 (LED): APAGADO"


def test_06_listar_dispositivos(cf):
    assert "alarma1" in cf.run("LISTAR DISPOSITIVOS").outputs[0].text


def test_07_dispositivo_inexistente_es_error_semantico(cf):
    r = cf.run("ENCENDER dispositivo99")
    assert not r.ok and r.errors[0].kind == "semántico"


def test_08_operacion_incompatible(cf):
    r = cf.run("ENCENDER alarma1")
    assert not r.ok and r.errors[0].kind == "semántico" and "no admite ENCENDER" in r.errors[0].message


def test_09_encender_sin_dispositivo_es_error_sintactico(cf):
    r = cf.run("ENCENDER")
    assert not r.ok and r.errors[0].kind == "sintáctico"


def test_10_led1_arroba_es_error_lexico(cf):
    r = cf.run("ENCENDER led1@")
    assert not r.ok and r.errors[0].kind == "léxico" and r.errors[0].column == 14


def test_11_notificar_prueba_queda_registrada(cf):
    r = cf.run('NOTIFICAR "Prueba"')
    assert r.ok and r.outputs[0].kind == "notificacion"
    assert r.outputs[0].text.startswith("Notificación registrada") and r.outputs[0].detail == "Prueba"


def test_12_enviar_correo_llega_al_smtp(cf):
    r = cf.run('ENVIAR CORREO A "usuario@ejemplo.com" MENSAJE "Hola, esta es una prueba"')
    assert r.ok and cf.email_service.sent == [("usuario@ejemplo.com", "Hola, esta es una prueba")]
    assert r.outputs[0].text == "Correo enviado a usuario@ejemplo.com"


def test_13_condicional(cf):
    cf.run("ENCENDER led1")
    assert cf.run("SI led1 == ENCENDIDO ENTONCES APAGAR led1").ok and dev(cf, "led1") == "OFF"


def test_doro_baila_y_se_detiene(cf):
    assert cf.run("BAILAR doro1").events[0].new == "DANCING"
    assert cf.run("CONSULTAR doro1").outputs[0].text == "doro1 (BAILARIN): BAILANDO"
    cf.run("SI doro1 == BAILANDO ENTONCES DETENER doro1")
    assert dev(cf, "doro1") == "STOPPED"
