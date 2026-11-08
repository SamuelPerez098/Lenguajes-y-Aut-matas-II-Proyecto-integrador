# CommandFlow

Intérprete de un lenguaje de comandos propio para controlar dispositivos simulados y enviar correos:

```
ENCENDER led1
BAILAR doro1
SI led1 == ENCENDIDO ENTONCES NOTIFICAR "Led encendido"
ENVIAR CORREO A "usuario@ejemplo.com" MENSAJE "Hola, esta es una prueba"
```

Pipeline: **léxico → sintaxis (AST) → semántica → código intermedio → optimizador → máquina virtual**.
Stack: Python/FastAPI, PostgreSQL, React, Mailpit y Docker Compose.

## Cómo ejecutarlo

### Opción 1 — Sin Docker (la más fácil)

Solo necesitas **Python 3.10 o superior**. La interfaz web ya viene compilada dentro del proyecto.

| Sistema | Qué hacer |
|---|---|
| Windows | Doble clic en **`iniciar.bat`** |
| Linux / macOS | `./iniciar.sh` |

La primera vez crea el entorno e instala dependencias (1–2 minutos) y abre **http://localhost:8000**.
Usa una base SQLite local (`backend/commandflow.db`).

### Opción 2 — Con Docker (PostgreSQL + Mailpit incluidos)

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Interfaz web | http://localhost:8080 |
| API y Swagger | http://localhost:8000/docs |
| Bandeja de correos de prueba (Mailpit) | http://localhost:8025 |

Los datos viven en el volumen `pgdata`: `docker compose down` los conserva y `docker compose down -v` los borra
(necesario una vez si ya habías levantado una versión anterior: cambió el esquema).

## Correo: de pruebas o real

Por defecto los correos van a **Mailpit** (bandeja local, no salen a Internet). Para enviar **correos reales**
(por ejemplo con Gmail) copia `.env.example` como `.env`, descomenta el bloque de tu proveedor y comprueba la
configuración:

```bash
python scripts/probar_correo.py tu_otro_correo@ejemplo.com
```

Guía completa con Gmail paso a paso y solución de problemas: [`docs/CORREO_REAL.md`](docs/CORREO_REAL.md).
La barra superior de la interfaz indica si el correo está en modo **real** o de **pruebas**.

## Notificaciones

`NOTIFICAR "Prueba"` responde *Notificación registrada*, la guarda en la base de datos y muestra un **`alert()`**
del navegador con el mensaje (si un programa genera varias, se agrupan en un solo aviso). Quedan listadas en la
pestaña *Notificaciones*.

## Desarrollo

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
python -m pytest                                        # pruebas del núcleo, escenarios del enunciado, SMTP y API
uvicorn app.main:app --reload                           # http://localhost:8000

# Frontend (otra terminal; requiere Node 20+)
cd frontend
npm install
npm run dev                                             # http://localhost:5173 (proxy a :8000)
npm test                                                # pruebas de la lógica del aviso
npm run build:backend                                   # recompila la interfaz dentro de backend/static
```

Interfaces alternativas del núcleo (sin servidor), desde `backend/`: `python -m commandflow` (consola) y
`python -m commandflow.gui` (ventana Tkinter).

## Documentación

- [`docs/CORREO_REAL.md`](docs/CORREO_REAL.md): correo real con Gmail/Outlook, pruebas y seguridad.
- [`docs/DOCUMENTACION_TECNICA.md`](docs/DOCUMENTACION_TECNICA.md): gramática EBNF, tokens, AST, IR, optimizaciones y sección 5.2.
- [`docs/API_Y_BASE_DE_DATOS.md`](docs/API_Y_BASE_DE_DATOS.md): endpoints, modelo de datos y transacciones.
- [`docs/PLAN_DE_TRABAJO.md`](docs/PLAN_DE_TRABAJO.md): ramas, Kanban, roles, tarjetas y criterios de aceptación.

## Lenguaje en una tabla

| Instrucción | Ejemplo |
|---|---|
| Control | `ENCENDER led1` · `APAGAR led1` · `ACTIVAR alarma1` · `DESACTIVAR alarma1` |
| Doro (GIF) | `BAILAR doro1` (el GIF se anima) · `DETENER doro1` (imagen fija) |
| Consulta | `CONSULTAR led1` · `LISTAR DISPOSITIVOS` |
| Notificación | `NOTIFICAR "Prueba"` → *Notificación registrada* + `alert()` |
| Correo | `ENVIAR CORREO A "a@b.com" MENSAJE "Hola"` |
| Condicional | `SI led1 == ENCENDIDO ENTONCES APAGAR led1` |
| Repetición | `REPETIR 3 VECES NOTIFICAR "Hola"` |

## Equipo

Lenguajes y Autómatas II — Ruiz Durán Emiliano · Pérez Ramírez Samuel · Gómez Vasquez Fredy Azarel ·
Martínez González Ricardo · Hernández Velasco Sandra Marely.
Reparto de roles y tarjetas: [`docs/PLAN_DE_TRABAJO.md`](docs/PLAN_DE_TRABAJO.md).

GIF de Doro: © @musan_pro (según la marca de agua), usado con fines académicos.
