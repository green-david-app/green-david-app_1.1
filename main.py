
import os, traceback
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="static", static_url_path="")

# SECRET_KEY for sessions (login)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}, 200

@app.get("/")
def root_index():
    try:
        sf = app.static_folder or "static"
        if os.path.exists(os.path.join(sf, "index.html")):
            return send_from_directory(sf, "index.html")
        return send_from_directory(".", "index.html")
    except Exception as e:
        return f"Index error: {e}", 500

# Try blueprint first (new addon style)
try:
    from addons.main_addons_calendar_vykazy import bp as addons_calendar_vykazy_bp  # type: ignore
    app.register_blueprint(addons_calendar_vykazy_bp)
    print("[INIT] addons blueprint registered")
except Exception as e:
    print("[INIT] addons blueprint failed:", e)
    traceback.print_exc()
    try:
        # Legacy import (routes register at import time)
        from addons.main_addons_calendar_vykazy import *  # type: ignore  # noqa
        print("[INIT] addons legacy import OK")
    except Exception as e2:
        print("[INIT] addons legacy import failed:", e2)
        traceback.print_exc()

@app.errorhandler(404)
def nf(err):
    return "404: " + str(err), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), debug=True)
