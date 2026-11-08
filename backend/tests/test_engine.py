"""Escenarios funcionales del enunciado (sección de pruebas) + atomicidad."""
import pytest

from commandflow import CommandFlow, SymbolTable
from commandflow.errors import ExecutionError
from commandflow.vm import VirtualMachine
from commandflow.ir import Instr


def state(cf, dev):
    return cf.table.lookup(dev).state


def test_01_encender_led(cf):
    r = cf.run("ENCENDER led1")
    assert r.ok and state(cf, "led1") == "ON" and str(r.events[0]) == "led1: APAGADO → ENCENDIDO"


def test_02_apagar_led(cf):
    cf.run("ENCENDER led1")
    assert cf.run("APAGAR led1").ok and state(cf, "led1") == "OFF"


def test_03_activar_alarma(cf):
    cf.run("DESACTIVAR alarma1")
    assert cf.run("ACTIVAR alarma1").ok and state(cf, "alarma1") == "ACTIVE"


def test_04_desactivar_alarma(cf):
    assert cf.run("DESACTIVAR alarma1").ok and state(cf, "alarma1") == "INACTIVE"


def test_05_consultar(cf):
    r = cf.run("CONSULTAR led2")
    assert r.outputs[0].text == "led2 (LED): ENCENDIDO"


def test_06_listar(cf):
    r = cf.run("LISTAR DISPOSITIVOS")
    text = r.outputs[0].text
    for dev in ("led1", "led2", "alarma1", "doro1"):
        assert dev in text


def test_07_notificar(cf):
    r = cf.run('NOTIFICAR "Hola"')
    assert (r.outputs[0].kind, r.outputs[0].text, r.outputs[0].detail) == \
        ("notificacion", "Notificación registrada: Hola", "Hola")


def test_08_correo(cf, mail):
    r = cf.run('ENVIAR CORREO A "usuario@ejemplo.com" MENSAJE "Hola, esta es una prueba"')
    assert r.ok and mail.sent == [("usuario@ejemplo.com", "Hola, esta es una prueba")]


def test_09_condicional_se_cumple(cf):
    r = cf.run("SI led2 == ENCENDIDO ENTONCES APAGAR led2")
    assert r.ok and state(cf, "led2") == "OFF"


def test_10_condicional_no_se_cumple(cf):
    r = cf.run("SI led1 == ENCENDIDO ENTONCES ENCENDER led2\nSI led1 != ENCENDIDO ENTONCES BAILAR doro1")
    assert state(cf, "led2") == "ON" and state(cf, "doro1") == "DANCING"
    assert r.ok


def test_11_secuencia_multilinea(cf):
    cf.run("ENCENDER led1\nBAILAR doro1\nDESACTIVAR alarma1\nAPAGAR led2")
    assert [state(cf, d) for d in ("led1", "doro1", "alarma1", "led2")] == ["ON", "DANCING", "INACTIVE", "OFF"]


def test_12_error_lexico(cf):
    r = cf.run("ENCENDER led1 $")
    assert not r.ok and r.errors[0].kind == "léxico"


def test_13_error_sintactico(cf):
    r = cf.run("ENCENDER")
    assert not r.ok and r.errors[0].kind == "sintáctico"


def test_14_error_semantico(cf):
    r = cf.run("ENCENDER led99")
    assert not r.ok and r.errors[0].kind == "semántico"


def test_15_incompatibilidad(cf):
    r = cf.run("ENCENDER alarma1")
    assert not r.ok and "ACTIVAR" in r.errors[0].message


def test_programa_invalido_no_ejecuta_nada(cf, mail):
    before = cf.table.snapshot()
    r = cf.run('ENCENDER led1\nNOTIFICAR "x"\nENCENDER led99\nENVIAR CORREO A "a@b.com" MENSAJE "m"')
    assert not r.ok and cf.table.snapshot() == before and mail.sent == []


def test_sin_cambios_mensaje(cf):
    assert "Sin cambios" in cf.run("APAGAR led1").message


def test_programa_vacio(cf):
    assert cf.run("# nada").message == "Nada que ejecutar."


def test_estado_persiste_entre_ejecuciones(cf):
    cf.run("ENCENDER led1")
    assert cf.run("CONSULTAR led1").outputs[0].text.endswith("ENCENDIDO")


def test_snapshot_restore():
    cf1 = CommandFlow()
    cf1.run("ENCENDER led1\nBAILAR doro1")
    cf2 = CommandFlow(table=SymbolTable())
    cf2.table.restore(cf1.table.snapshot())
    assert cf2.table.snapshot() == cf1.table.snapshot()


def test_fallo_de_correo_se_reporta():
    class Broken:
        def send(self, to, message):
            raise ExecutionError("SMTP caído")
    cf = CommandFlow(email_service=Broken())
    r = cf.run('ENCENDER led1\nENVIAR CORREO A "a@b.com" MENSAJE "x"')
    assert not r.ok and r.errors[0].kind == "de ejecución"
    assert [str(e) for e in r.events] == ["led1: APAGADO → ENCENDIDO"]  # efecto previo informado


def test_vm_limite_de_pasos():
    vm = VirtualMachine(SymbolTable.default(), None, max_steps=5)
    with pytest.raises(ExecutionError):
        vm.run([Instr("NOTIFY", ("x",))] * 10)
