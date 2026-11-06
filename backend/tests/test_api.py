"""Pruebas de la API (SQLite temporal + correo en memoria; en Docker se usa PostgreSQL + Mailpit)."""
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from commandflow import InMemoryEmailService
from commandflow.errors import ExecutionError


@pytest.fixture
def mail():
    return InMemoryEmailService()


@pytest.fixture
def db_url(tmp_path):
    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture
def client(db_url, mail):
    app = create_app(Settings(database_url=db_url), email_service=mail)
    with TestClient(app) as c:
        yield c


def run(client, source, **kw):
    r = client.post("/api/commands", json={"source": source, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def states(client):
    return {d["id"]: d["state"] for d in client.get("/api/devices").json()}


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "database": "ok"}


def test_dispositivos_iniciales(client):
    assert states(client) == {"led1": "OFF", "led2": "ON", "alarma1": "ACTIVE", "ventilador1": "OFF"}


def test_ejecutar_cambia_estado_y_persiste(client):
    body = run(client, "ENCENDER led1")
    assert body["ok"] and body["events"][0]["text"] == "led1: APAGADO → ENCENDIDO"
    assert states(client)["led1"] == "ON"
    assert next(d for d in body["devices"] if d["id"] == "led1")["state_es"] == "ENCENDIDO"


def test_estado_sobrevive_a_reinicio_de_la_app(db_url, mail):
    with TestClient(create_app(Settings(database_url=db_url), mail)) as c1:
        run(c1, "ENCENDER ventilador1\nDESACTIVAR alarma1")
    with TestClient(create_app(Settings(database_url=db_url), mail)) as c2:
        assert states(c2)["ventilador1"] == "ON" and states(c2)["alarma1"] == "INACTIVE"


def test_consultas_y_condicional(client):
    body = run(client, "CONSULTAR led2\nSI led2 == ENCENDIDO ENTONCES APAGAR led2")
    assert body["outputs"][0]["text"] == "led2 (LED): ENCENDIDO"
    assert states(client)["led2"] == "OFF"


def test_compilacion_incluye_tokens_ast_ir_y_optimizaciones(client):
    c = run(client, "ENCENDER led1\nENCENDER led1")["compilation"]
    assert c["tokens"][0] == {"line": 1, "col": 1, "type": "ENCENDER", "lexeme": "ENCENDER"}
    assert c["ast"]["nodo"] == "Program"
    assert len(c["ir"]) == 3 and len(c["optimized_ir"]) == 2
    assert c["optimizations"][0]["name"] == "instrucción redundante"


def test_optimize_false(client):
    c = run(client, "ENCENDER led1\nENCENDER led1", optimize=False)["compilation"]
    assert c["ir"] == c["optimized_ir"] and c["optimizations"] == []


@pytest.mark.parametrize("src,kind", [("ENCENDER led1 @", "léxico"), ("ENCENDER", "sintáctico"),
                                      ("ENCENDER led99", "semántico"), ("ENCENDER alarma1", "semántico")])
def test_errores_del_lenguaje(client, src, kind):
    body = run(client, src)
    assert not body["ok"] and body["errors"][0]["tipo"] == kind and body["errors"][0]["linea"] == 1


def test_programa_con_error_no_modifica_dispositivos_pero_queda_en_historial(client, mail):
    before = states(client)
    body = run(client, 'ENCENDER led1\nENVIAR CORREO A "a@b.com" MENSAJE "x"\nENCENDER led99')
    assert not body["ok"] and states(client) == before and mail.sent == []
    assert client.get("/api/history").json()[0]["ok"] is False


def test_correo_se_envia_y_se_registra(client, mail):
    run(client, 'ENVIAR CORREO A "usuario@ejemplo.com" MENSAJE "Hola, esta es una prueba"')
    assert mail.sent == [("usuario@ejemplo.com", "Hola, esta es una prueba")]
    (item,) = client.get("/api/emails").json()
    assert item["recipient"] == "usuario@ejemplo.com"


def test_fallo_smtp_reporta_error_y_conserva_efectos_previos(db_url):
    class Broken:
        def send(self, to, message):
            raise ExecutionError("SMTP caído")
    with TestClient(create_app(Settings(database_url=db_url), Broken())) as c:
        body = run(c, 'ENCENDER led1\nENVIAR CORREO A "a@b.com" MENSAJE "x"')
        assert not body["ok"] and body["errors"][0]["tipo"] == "de ejecución"
        assert states(c)["led1"] == "ON"
        assert c.get("/api/emails").json() == []


def test_historial_y_bitacora_de_eventos(client):
    run(client, "ENCENDER led1")
    run(client, "APAGAR led1")
    hist = client.get("/api/history").json()
    assert [h["source"] for h in hist] == ["APAGAR led1", "ENCENDER led1"]
    ev = client.get("/api/events").json()
    assert [(e["device_id"], e["old_state"], e["new_state"]) for e in ev] == \
        [("led1", "ON", "OFF"), ("led1", "OFF", "ON")]


def test_compile_no_ejecuta_ni_guarda(client):
    body = client.post("/api/compile", json={"source": "ENCENDER led1"}).json()
    assert body["ok"] and body["compilation"]["ir"]
    assert states(client)["led1"] == "OFF" and client.get("/api/history").json() == []


def test_compile_reporta_errores_semanticos(client):
    body = client.post("/api/compile", json={"source": "ENCENDER led99\nENCENDER alarma1"}).json()
    assert not body["ok"] and len(body["errors"]) == 2


def test_reset_y_borrado_de_historial(client):
    run(client, "ENCENDER led1\nAPAGAR led2")
    assert client.post("/api/devices/reset").status_code == 200
    assert states(client) == {"led1": "OFF", "led2": "ON", "alarma1": "ACTIVE", "ventilador1": "OFF"}
    assert client.delete("/api/history").status_code == 204
    assert client.get("/api/history").json() == [] and client.get("/api/events").json() == []


def test_programa_demasiado_largo_se_rechaza(client):
    r = client.post("/api/commands", json={"source": "A" * 6000})
    assert r.status_code == 422


def test_programa_vacio(client):
    assert run(client, "")["message"] == "Nada que ejecutar."


def test_config_y_docs(client):
    assert "mailpit_ui_url" in client.get("/api/config").json()
    assert client.get("/openapi.json").status_code == 200
