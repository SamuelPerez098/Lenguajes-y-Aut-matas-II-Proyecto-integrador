"""Prueba del cliente SMTP real contra un servidor SMTP falso local (equivale a Mailpit)."""
import socketserver
import threading

import pytest

from commandflow import CommandFlow, SmtpEmailService
from commandflow.errors import ExecutionError


class _Handler(socketserver.StreamRequestHandler):
    def handle(self):
        w = lambda line: self.wfile.write((line + "\r\n").encode())
        w("220 fake ESMTP")
        data_mode, body = False, []
        for raw in self.rfile:
            line = raw.decode(errors="replace").rstrip("\r\n")
            if data_mode:
                if line == ".":
                    data_mode = False
                    self.server.messages.append("\n".join(body))
                    w("250 OK queued")
                else:
                    body.append(line)
                continue
            cmd = line.upper()
            if cmd.startswith(("EHLO", "HELO")):
                w("250 fake")
            elif cmd.startswith(("MAIL FROM", "RCPT TO")):
                w("250 OK")
            elif cmd == "DATA":
                data_mode = True
                w("354 go ahead")
            elif cmd == "QUIT":
                w("221 bye")
                return
            else:
                w("250 OK")


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _Handler)
        self.messages: list[str] = []


@pytest.fixture
def smtp_server():
    srv = _Server()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


def test_envia_correo_por_smtp_real(smtp_server):
    svc = SmtpEmailService("127.0.0.1", smtp_server.server_address[1])
    svc.send("usuario@ejemplo.com", "Hola, esta es una prueba")
    (raw,) = smtp_server.messages
    assert "To: usuario@ejemplo.com" in raw and "Hola, esta es una prueba" in raw


def test_instruccion_enviar_correo_de_extremo_a_extremo(smtp_server):
    cf = CommandFlow(email_service=SmtpEmailService("127.0.0.1", smtp_server.server_address[1]))
    r = cf.run('ENVIAR CORREO A "ana@ejemplo.com" MENSAJE "Todo bien"')
    assert r.ok and r.outputs[0].text == "Correo enviado a ana@ejemplo.com"
    assert "Todo bien" in smtp_server.messages[0]


def test_servidor_caido_da_error_de_ejecucion():
    svc = SmtpEmailService("127.0.0.1", 1, timeout=1)   # puerto sin servicio
    with pytest.raises(ExecutionError, match="No se pudo enviar"):
        svc.send("a@b.com", "x")


def test_configuracion_de_proveedor_externo_por_entorno(monkeypatch):
    monkeypatch.setenv("SMTP_USER", "u")
    monkeypatch.setenv("SMTP_PASSWORD", "p")
    monkeypatch.setenv("SMTP_STARTTLS", "true")
    monkeypatch.setenv("SMTP_FROM", "app@midominio.com")
    svc = SmtpEmailService("smtp.proveedor.com", 587)
    assert (svc.user, svc.password, svc.starttls, svc.ssl, svc.sender) == ("u", "p", True, False, "app@midominio.com")


# ---------------------------------------------------------------------------
# Servidor SMTP falso con STARTTLS + AUTH (lo que exigen Gmail, Outlook, etc.)
# ---------------------------------------------------------------------------
import base64
import shutil
import socket
import ssl
import subprocess


class _TlsAuthServer:
    def __init__(self, certfile, keyfile, user="yo@gmail.com", password="clave-de-app"):
        self.user, self.password = user, password
        self.messages, self.logins = [], []
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ctx.load_cert_chain(certfile, keyfile)
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(5)
        self.port = self.sock.getsockname()[1]
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn):
        f = conn.makefile("rwb")

        def w(text):
            f.write((text + "\r\n").encode())
            f.flush()

        w("220 fake ESMTP")
        tls, data, body = False, False, []
        try:
            while True:
                line = f.readline()
                if not line:
                    return
                text = line.decode(errors="replace").rstrip("\r\n")
                if data:
                    if text == ".":
                        data = False
                        self.messages.append("\n".join(body))
                        w("250 queued")
                    else:
                        body.append(text)
                    continue
                cmd = text.upper()
                if cmd.startswith("EHLO"):
                    w("250-fake")
                    w("250 AUTH PLAIN" if tls else "250 STARTTLS")
                elif cmd == "STARTTLS":
                    w("220 ready")
                    conn = self.ctx.wrap_socket(conn, server_side=True)
                    f = conn.makefile("rwb")
                    tls = True
                elif cmd.startswith("AUTH PLAIN"):
                    _, user, pwd = base64.b64decode(text.split()[2]).decode().split("\0")
                    self.logins.append((user, tls))
                    ok = tls and user == self.user and pwd == self.password
                    w("235 2.7.0 accepted" if ok else "535 5.7.8 credenciales invalidas")
                elif cmd.startswith(("MAIL FROM", "RCPT TO")):
                    w("250 OK")
                elif cmd == "DATA":
                    data = True
                    w("354 go")
                elif cmd == "QUIT":
                    w("221 bye")
                    return
                else:
                    w("250 OK")
        except (OSError, ssl.SSLError):
            return

    def close(self):
        self.sock.close()


@pytest.fixture
def tls_server(tmp_path):
    if not shutil.which("openssl"):
        pytest.skip("openssl no disponible")
    key, cert = tmp_path / "k.pem", tmp_path / "c.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(key),
                    "-out", str(cert), "-days", "1", "-subj", "/CN=localhost"],
                   check=True, capture_output=True)
    srv = _TlsAuthServer(str(cert), str(key))
    yield srv
    srv.close()


def _client(srv, **kw):
    return SmtpEmailService("127.0.0.1", srv.port, user="yo@gmail.com", password="clave-de-app",
                            starttls=True, tls_verify=False, timeout=5, **kw)


def test_starttls_y_login_funcionan_como_con_gmail(tls_server):
    _client(tls_server).send("destino@ejemplo.com", "Mensaje real")
    assert tls_server.logins == [("yo@gmail.com", True)]       # el login ocurrió DESPUÉS de cifrar
    assert "Mensaje real" in tls_server.messages[0] and "To: destino@ejemplo.com" in tls_server.messages[0]


def test_contrasena_incorrecta_da_mensaje_claro(tls_server):
    bad = SmtpEmailService("127.0.0.1", tls_server.port, user="yo@gmail.com", password="mala",
                           starttls=True, tls_verify=False, timeout=5)
    with pytest.raises(ExecutionError, match="contraseña de aplicación"):
        bad.send("a@b.com", "x")


def test_certificado_no_confiable_se_rechaza_por_defecto(tls_server):
    strict = SmtpEmailService("127.0.0.1", tls_server.port, user="yo@gmail.com", password="clave-de-app",
                              starttls=True, timeout=5)          # tls_verify=True por defecto
    with pytest.raises(ExecutionError, match="TLS"):
        strict.send("a@b.com", "x")
    assert tls_server.messages == []


def test_instruccion_completa_por_smtp_autenticado(tls_server):
    cf = CommandFlow(email_service=_client(tls_server))
    r = cf.run('ENVIAR CORREO A "ana@ejemplo.com" MENSAJE "Hola desde CommandFlow"')
    assert r.ok and r.outputs[0].text == "Correo enviado a ana@ejemplo.com"
    assert "Hola desde CommandFlow" in tls_server.messages[0]
