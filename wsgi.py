
# wsgi.py
# Load the main Flask app and ensure hotfix routes are imported.
from main import app  # existing app
import gd_calendar_hotfix  # registers /gd/api/calendar routes
# Gunicorn: wsgi:app
