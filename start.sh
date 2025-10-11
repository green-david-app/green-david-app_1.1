#!/usr/bin/env bash
set -euo pipefail
cd "green-david-app_1.1_funkc╠îni╠ü"
exec gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:${PORT:-5000} app:app
