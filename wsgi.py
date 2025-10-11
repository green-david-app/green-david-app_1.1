# wsgi.py - idempotent registration of gd_ext blueprint
from main import app as app

try:
    if 'gd' not in getattr(app, 'blueprints', {}):
        from gd_ext import GD_BP, ensure_gd_db
        ensure_gd_db()
        app.register_blueprint(GD_BP)
        print('gd_ext blueprint registered (wsgi.py)')
    else:
        print('gd_ext already registered (wsgi.py) - skipping')
except Exception as e:
    print('gd_ext init error (wsgi.py):', e)
