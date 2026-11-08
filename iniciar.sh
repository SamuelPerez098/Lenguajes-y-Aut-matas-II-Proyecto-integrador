#!/usr/bin/env bash
# Arranque sin Docker (Linux / macOS): crea el entorno, instala dependencias y abre CommandFlow.
set -e
cd "$(dirname "$0")"
[ -f .env ] || cp .env.example .env
cd backend
[ -d .venv ] || python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
echo
echo "CommandFlow en  http://localhost:8000   (Ctrl+C para detener)"
( sleep 2; command -v xdg-open >/dev/null && xdg-open http://localhost:8000 \
  || command -v open >/dev/null && open http://localhost:8000 ) >/dev/null 2>&1 &
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
