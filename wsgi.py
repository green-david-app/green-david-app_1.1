
from main import app as app
try:
    from gd_ext import GD_BP, ensure_gd_db
    ensure_gd_db()
    app.register_blueprint(GD_BP)
    print("gd_ext blueprint registered")
except Exception as e:
    print("gd_ext init error:", e)
