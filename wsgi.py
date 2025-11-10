
# WSGI entrypoint kept minimal. Import app from main.py,
# then import search_fix so that the /search route is registered.
from main import app  # noqa: F401
import search_fix  # noqa: F401
