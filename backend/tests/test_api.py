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
    assert states(client) == {"led1": "OFF", "led2": "ON", "alarma1": "ACTIVE", "doro1": "STOPPED"}


def test_ejecutar_cambia_estado_y_persiste(client):
    body = run(client, "ENCENDER led1")
    assert body["ok"] and body["events"][0]["text"] == "led1: APAGADO → ENCENDIDO"
    assert states(client)["led1"] == "ON"
    assert next(d for d in body["devices"] if d["id"] == "led1")["state_es"] == "ENCENDIDO"


def test_estado_sobrevive_a_reinicio_de_la_app(db_url, mail):
    with TestClient(create_app(Settings(database_url=db_url), mail)) as c1:
        run(c1, "BAILAR doro1\nDESACTIVAR alarma1")
    with TestClient(create_app(Settings(database_url=db_url), mail)) as c2:
        assert states(c2)["doro1"] == "DANCING" and states(c2)["alarma1"] == "INACTIVE"


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
    assert item["recipient"] == "usuario@ejemplo.com" and item["status"] == "sent"


def test_fallo_smtp_reporta_error_y_conserva_efectos_previos(db_url):
    class Broken:
        def send(self, to, message):
            raise ExecutionError("SMTP caído")
    with TestClient(create_app(Settings(database_url=db_url), Broken())) as c:
        body = run(c, 'ENCENDER led1\nENVIAR CORREO A "a@b.com" MENSAJE "x"')
        assert not body["ok"] and body["errors"][0]["tipo"] == "de ejecución"
        assert states(c)["led1"] == "ON"
        (attempt,) = c.get("/api/emails").json()
        assert attempt["status"] == "failed" and "SMTP caído" in attempt["error"]


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
    assert states(client) == {"led1": "OFF", "led2": "ON", "alarma1": "ACTIVE", "doro1": "STOPPED"}
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


def test_notificar_se_registra_y_se_informa(client):
    body = run(client, 'NOTIFICAR "Prueba"')
    out = body["outputs"][0]
    assert out["kind"] == "notificacion" and out["text"] == "Notificación registrada: Prueba" and out["detail"] == "Prueba"
    (n,) = client.get("/api/notifications").json()
    assert n["message"] == "Prueba"
    client.delete("/api/history")
    assert client.get("/api/notifications").json() == []


def test_doro_baila_y_se_detiene(client):
    body = run(client, "BAILAR doro1")
    d = next(x for x in body["devices"] if x["id"] == "doro1")
    assert (d["state"], d["state_es"]) == ("DANCING", "BAILANDO")
    run(client, "DETENER doro1")
    assert states(client)["doro1"] == "STOPPED"


def test_por_defecto_se_conserva_la_bitacora_completa(client):
    body = run(client, "ENCENDER led1\nAPAGAR led1")           # preserve_events=True (por defecto)
    assert len(body["compilation"]["optimized_ir"]) == len(body["compilation"]["ir"])
    assert [(e["old_state"], e["new_state"]) for e in client.get("/api/events").json()] == [("ON", "OFF"), ("OFF", "ON")]


def test_se_puede_activar_la_optimizacion_2_explicitamente(client):
    body = run(client, "ENCENDER led1\nAPAGAR led1", preserve_events=False)
    assert len(body["compilation"]["optimized_ir"]) == len(body["compilation"]["ir"]) - 1
    assert body["compilation"]["optimizations"][0]["name"] == "asignación sobrescrita"


def test_base_de_datos_antigua_con_ventilador_se_reconcilia(db_url, mail):
    from sqlalchemy import text
    from app.db import make_engine
    with TestClient(create_app(Settings(database_url=db_url), mail)):
        pass
    engine = make_engine(db_url)
    with engine.begin() as c:
        c.execute(text("DELETE FROM devices WHERE id = 'doro1'"))
        c.execute(text("INSERT INTO devices (id, type, state, ordinal, updated_at) VALUES ('ventilador1', 'VENTILADOR', 'ON', 3, CURRENT_TIMESTAMP)"))
    engine.dispose()
    with TestClient(create_app(Settings(database_url=db_url), mail)) as c:
        assert set(states(c)) == {"led1", "led2", "alarma1", "doro1"}


def test_config_describe_el_correo_sin_exponer_credenciales(db_url):
    from commandflow import SmtpEmailService
    svc = SmtpEmailService("smtp.gmail.com", 587, user="yo@gmail.com", password="secreto", starttls=True)
    with TestClient(create_app(Settings(database_url=db_url), svc)) as c:
        cfg = c.get("/api/config").json()
        assert cfg["email"] == {"host": "smtp.gmail.com", "port": 587, "real": True,
                                "authenticated": True, "encrypted": True}
        assert "secreto" not in c.get("/api/config").text and "yo@gmail.com" not in c.get("/api/config").text
    with TestClient(create_app(Settings(database_url=db_url), SmtpEmailService("mailpit", 1025))) as c:
        assert c.get("/api/config").json()["email"]["real"] is False


def test_la_api_sirve_la_interfaz_compilada_si_existe(db_url, mail, tmp_path):
    (tmp_path / "index.html").write_text("<html><title>CommandFlow</title></html>", encoding="utf-8")
    settings = Settings(database_url=db_url, static_dir=str(tmp_path))
    with TestClient(create_app(settings, mail)) as c:
        assert "CommandFlow" in c.get("/").text
        assert c.get("/api/health").json()["status"] == "ok"     # la API sigue teniendo prioridad


def test_sin_carpeta_de_interfaz_no_hay_raiz(db_url, mail, tmp_path):
    with TestClient(create_app(Settings(database_url=db_url, static_dir=str(tmp_path / "no")), mail)) as c:
        assert c.get("/").status_code == 404


def test_dotenv_carga_variables_sin_pisar_las_del_entorno(tmp_path, monkeypatch):
    import os

    from app.config import load_dotenv
    # Entorno aislado: todo lo que cargue load_dotenv desaparece al terminar la prueba.
    monkeypatch.setattr(os, "environ", {"SMTP_PORT": "2525"})
    env = tmp_path / ".env"
    env.write_text('# comentario\nSMTP_HOST=smtp.gmail.com\nSMTP_USER="yo@gmail.com"\nSMTP_FROM=a@b.com # nota\n\nSMTP_PORT=587\n',
                   encoding="utf-8")
    assert load_dotenv([env, env]) == [env]                    # sin duplicados
    assert (os.environ["SMTP_HOST"], os.environ["SMTP_USER"], os.environ["SMTP_FROM"], os.environ["SMTP_PORT"]) == \
        ("smtp.gmail.com", "yo@gmail.com", "a@b.com", "2525")  # ya definida: gana el entorno
