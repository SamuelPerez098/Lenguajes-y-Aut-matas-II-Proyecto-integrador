@echo off
rem Arranque sin Docker (Windows): crea el entorno, instala dependencias y abre CommandFlow.
cd /d "%~dp0"
if not exist .env copy .env.example .env >nul
cd backend
if not exist .venv (
  py -3 -m venv .venv 2>nul || python -m venv .venv
)
call .venv\Scripts\activate
pip install -q -r requirements.txt
echo.
echo CommandFlow en  http://localhost:8000   (Ctrl+C para detener)
start "" http://localhost:8000
uvicorn app.main:app --host 127.0.0.1 --port 8000
