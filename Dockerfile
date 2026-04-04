FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml README.md alembic.ini migration.sql ./
COPY app ./app
COPY alembic ./alembic

RUN pip install --upgrade pip && \
    pip install .

EXPOSE 5001

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 5001"]
