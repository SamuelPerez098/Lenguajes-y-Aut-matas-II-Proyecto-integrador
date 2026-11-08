#!/usr/bin/env python3
"""Crea etiquetas e issues de GitHub a partir de docs/kanban_tarjetas.csv usando la CLI `gh`.

    python scripts/import_cards.py            # prueba: muestra lo que haría
    python scripts/import_cards.py --apply    # ejecuta (requiere `gh auth login` y estar en el repo)
"""
import argparse
import csv
import subprocess
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "docs" / "kanban_tarjetas.csv"


def run(cmd: list[str], apply: bool) -> None:
    print("$", " ".join(f'"{c}"' if " " in c or "\n" in c else c for c in cmd)[:200])
    if apply:
        subprocess.run(cmd, check=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="ejecutar de verdad (por defecto solo muestra)")
    args = ap.parse_args()

    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    labels = {"tarjeta", "bug", "bloqueado"}
    labels |= {f"rol:{r['Rol']}" for r in rows} | {f"sprint:{r['Sprint']}" for r in rows}
    labels |= {f"tam:{r['Tamano']}" for r in rows}
    for lab in sorted(labels):
        run(["gh", "label", "create", lab, "--force"], args.apply)

    for r in rows:
        checklist = "\n".join(f"- [ ] {c}" for c in r["Criterios"].splitlines())
        body = (f"**ID:** `{r['ID']}`  ·  **Rol:** {r['Rol']}  ·  **Tamaño:** {r['Tamano']}  ·  "
                f"**Sprint:** {r['Sprint']}\n**Responsable:** {r['Responsable']}  ·  **Revisor:** {r['Revisor']}\n"
                f"**Estado inicial:** {r['Estado']}\n"
                f"**Depende de:** {r['Depende']}\n**Entregable:** {r['Entregable']}\n\n"
                f"## Criterios de aceptación\n{checklist}\n")
        run(["gh", "issue", "create", "--title", f"[{r['ID']}] {r['Titulo']}", "--body", body,
             "--label", ",".join(["tarjeta", f"rol:{r['Rol']}", f"sprint:{r['Sprint']}", f"tam:{r['Tamano']}"])],
            args.apply)
    print(f"\n{len(rows)} tarjetas {'creadas' if args.apply else '(modo prueba, use --apply)'}")


if __name__ == "__main__":
    main()
