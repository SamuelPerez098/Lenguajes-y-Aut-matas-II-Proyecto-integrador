"""Consola interactiva:  python -m commandflow [archivo.cf] [--smtp host:puerto] [--no-opt] [--ir]"""
import argparse
import sys

from . import CommandFlow, InMemoryEmailService, SmtpEmailService
from .ir import format_program


def render(res, show_ir: bool) -> None:
    for out in res.outputs:
        print(out.text)
    for ev in res.events:
        print(f"  ↳ {ev}")
    if res.errors or (not res.outputs and not res.events) or res.message != "OK":
        print(res.message)
    if show_ir and res.compilation.ir:
        print("--- IR ---\n" + format_program(res.compilation.ir))
        print("--- IR optimizado ---\n" + format_program(res.compilation.optimized_ir))
        for n in res.compilation.optimizations:
            print(f"  [opt] {n.name}: {n.removed} ({n.reason})")


def main() -> None:
    ap = argparse.ArgumentParser(prog="commandflow")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--smtp", help="host:puerto (p. ej. localhost:1025 para Mailpit)")
    ap.add_argument("--no-opt", action="store_true")
    ap.add_argument("--ir", action="store_true", help="mostrar el IR")
    ap.add_argument("--gui", action="store_true", help="abrir la interfaz gráfica")
    args = ap.parse_args()
    if args.gui:
        from .gui import main as gui_main
        gui_main()
        return

    if args.smtp:
        host, _, port = args.smtp.partition(":")
        email = SmtpEmailService(host, int(port or 1025))
    else:
        email = InMemoryEmailService()
    cf = CommandFlow(email_service=email, optimize=not args.no_opt)

    if args.file:
        render(cf.run(open(args.file, encoding="utf-8").read()), args.ir)
        return
    print("CommandFlow — escribe instrucciones (salir: 'exit').")
    while True:
        try:
            line = input("cf> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line.strip().lower() in ("exit", "salir"):
            break
        render(cf.run(line), args.ir)


if __name__ == "__main__":
    sys.exit(main())
