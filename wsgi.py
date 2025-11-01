
# wsgi.py
# Ensure hotfix import registers routes exactly once.
from main import app  # existing app instance
import gd_calendar_hotfix  # safe registration (guarded)
# Gunicorn: wsgi:app
