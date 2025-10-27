
from main import app as _app
from extra_routes import attach
app = attach(_app)
# For gunicorn: wsgi:app
