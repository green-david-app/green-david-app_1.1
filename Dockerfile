# Use official Python 3.12 slim image
FROM python:3.12-slim

# Avoid interactive prompts and set env
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# System deps (optional but useful for manylibs); keep minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app
COPY . /app

# Expose port
EXPOSE 8000

# Default command: run via Gunicorn on port 8000
# main:app expects 'app' object in main.py
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
