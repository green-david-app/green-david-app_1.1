# Green David App - Docker Image

FROM python:3.12-slim

# Metadata
LABEL maintainer="Green David s.r.o. <info@greendavid.cz>"
LABEL description="Green David App - Firemní systém"
LABEL version="1.0.0"

# Nastavení prostředí
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Pracovní adresář
WORKDIR /app

# Systémové závislosti (minimální)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        && \
    rm -rf /var/lib/apt/lists/*

# Kopírování requirements a instalace
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Kopírování aplikace
COPY . .

# Vytvoření adresářů
RUN mkdir -p \
    /app/data \
    /app/uploads \
    /app/logs && \
    chmod -R 755 /app

# Exposed port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=2)" || exit 1

# Výchozí command
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "main:app", "--timeout", "120", "--log-file", "-"]
