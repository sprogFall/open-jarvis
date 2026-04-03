FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash docker.io procps \
    && rm -rf /var/lib/apt/lists/*

COPY client/requirements.txt /tmp/client-requirements.txt
RUN pip install -r /tmp/client-requirements.txt

COPY client /app/client
COPY skill_catalog.py /app/skill_catalog.py

RUN mkdir -p /data/client /workspace

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD pgrep -f "python -m client.service" >/dev/null || exit 1

CMD ["python", "-m", "client.service"]
