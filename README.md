# CommandFlow — núcleo del lenguaje (Python)

Lexer → Parser → AST → Semántico → IR → Optimizador → Máquina virtual.

## Interfaz gráfica

```bash
set PYTHONPATH=src          # PowerShell: $env:PYTHONPATH = "src"
python -m commandflow.gui   # o: python -m commandflow --gui
```

En Linux, si falta Tkinter: `sudo apt install python3-tk`.

## Línea de comandos y pruebas

```bash
pip install pytest
python -m pytest                      # 83 pruebas
PYTHONPATH=src python -m commandflow  # consola interactiva
PYTHONPATH=src python -m commandflow examples/demo.cf --ir
PYTHONPATH=src python -m commandflow --smtp localhost:1025   # correo real vía Mailpit
```

Uso como biblioteca:

```python
from commandflow import CommandFlow
cf = CommandFlow()
r = cf.run('ENCENDER led1\nSI led1 == ENCENDIDO ENTONCES NOTIFICAR "listo"')
r.ok, r.outputs, r.events, r.compilation.optimized_ir
```

Documentación completa (gramática EBNF, tokens, AST, IR, optimizaciones): `docs/DOCUMENTACION_TECNICA.md`.
