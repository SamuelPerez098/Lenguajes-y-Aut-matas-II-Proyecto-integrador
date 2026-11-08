"""Prueba aleatoria: el IR optimizado debe producir el mismo comportamiento observable
(estados finales + salidas + correos enviados) que el IR sin optimizar."""
import random

from commandflow import CommandFlow, InMemoryEmailService

DEVICES = {"led1": ("ENCENDER", "APAGAR", ("ENCENDIDO", "APAGADO")),
           "led2": ("ENCENDER", "APAGAR", ("ENCENDIDO", "APAGADO")),
           "doro1": ("BAILAR", "DETENER", ("BAILANDO", "DETENIDO")),
           "alarma1": ("ACTIVAR", "DESACTIVAR", ("ACTIVADA", "DESACTIVADA"))}


def simple(rng):
    dev = rng.choice(list(DEVICES))
    on, off, states = DEVICES[dev]
    kind = rng.choice(["set", "set", "set", "set", "query", "list", "notify", "mail"])
    if kind == "set":
        return f"{rng.choice([on, off])} {dev}"
    if kind == "query":
        return f"CONSULTAR {dev}"
    if kind == "list":
        return "LISTAR DISPOSITIVOS"
    if kind == "notify":
        return f'NOTIFICAR "n{rng.randint(0, 9)}"'
    return f'ENVIAR CORREO A "u{rng.randint(0, 3)}@x.com" MENSAJE "m"'


def statement(rng):
    r = rng.random()
    if r < 0.6:
        return simple(rng)
    if r < 0.85:
        dev = rng.choice(list(DEVICES))
        st = rng.choice(DEVICES[dev][2])
        return f"SI {dev} {rng.choice(['==', '!='])} {st} ENTONCES {simple(rng)}"
    return f"REPETIR {rng.randint(1, 4)} VECES {simple(rng)}"


def observe(source, optimize):
    mail = InMemoryEmailService()
    cf = CommandFlow(email_service=mail, optimize=optimize)
    res = cf.run(source)
    assert res.ok, res.message
    return cf.table.snapshot(), [(o.kind, o.text) for o in res.outputs], mail.sent


def test_optimizacion_preserva_comportamiento():
    rng = random.Random(2026)
    reduced = 0
    for _ in range(600):
        src = "\n".join(statement(rng) for _ in range(rng.randint(1, 14)))
        assert observe(src, True) == observe(src, False), src
        comp = CommandFlow().compile(src)
        reduced += len(comp.optimized_ir) < len(comp.ir)
    assert reduced > 100   # la prueba realmente ejercita las optimizaciones


def test_secuencias_ejecutadas_dos_veces_siguen_equivalentes():
    """Con estado inicial distinto (segunda ejecución sobre el mismo motor)."""
    rng = random.Random(7)
    for _ in range(200):
        a = "\n".join(statement(rng) for _ in range(6))
        b = "\n".join(statement(rng) for _ in range(6))
        results = []
        for opt in (True, False):
            mail = InMemoryEmailService()
            cf = CommandFlow(email_service=mail, optimize=opt)
            outs = [[(o.kind, o.text) for o in cf.run(s).outputs] for s in (a, b)]
            results.append((cf.table.snapshot(), outs, mail.sent))
        assert results[0] == results[1]
