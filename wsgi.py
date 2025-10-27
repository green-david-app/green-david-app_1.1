
# Robust WSGI wrapper that preserves original app but adds UI/assets routes and GD API aliases
from main import app as _app
from extra_routes import attach
app = attach(_app)
