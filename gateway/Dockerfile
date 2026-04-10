FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash docker.io procps \
    && rm -rf /var/lib/apt/lists/*

COPY gateway/requirements.txt /tmp/gateway-requirements.txt
COPY client/requirements.txt /tmp/client-requirements.txt
RUN pip install -r /tmp/gateway-requirements.txt -r /tmp/client-requirements.txt

COPY gateway /app/gateway
COPY client /app/client
COPY dashboard/.env.example /app/dashboard/.env.example
COPY jarvisctl.py /app/jarvisctl.py
COPY skill_catalog.py /app/skill_catalog.py

RUN mkdir -p /data/gateway /workspace

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
