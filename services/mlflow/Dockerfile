FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip tooling first
RUN python -m pip install --upgrade pip setuptools wheel

# Install MLflow server pinned to your local client version
RUN pip install "mlflow[extras]==3.1.4" boto3 psycopg2-binary==2.9.9

# Ensure a modern 'packaging' version (fixes ImportError for Version)
RUN pip install --upgrade "packaging>=24.1"

EXPOSE 5000