FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY commandflow ./commandflow
COPY app ./app

RUN useradd --create-home appuser
USER appuser
EXPOSE 8000

# Un solo worker: la serialización de ejecuciones usa un lock de proceso + SELECT ... FOR UPDATE.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
