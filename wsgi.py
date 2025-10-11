# Render/Gunicorn WSGI entrypoint
# Exports `app` so `gunicorn ... wsgi:app` works.
from main import app  # noqa: F401
