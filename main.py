
import os
import traceback
from flask import Flask, send_from_directory, jsonify

# Serve static from ./static; index.html is in project root
app = Flask(__name__, static_folder="static", static_url_path="")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}, 200

# Root index (index.html is in repository root)
@app.get("/")
def root_index():
    try:
        # Try ./static/index.html first, then repo root
        if os.path.exists(os.path.join(app.static_folder or "static", "index.html")):
            return send_from_directory(app.static_folder, "index.html")
        return send_from_directory(".", "index.html")
    except Exception as e:
        return f"Index error: {e}", 500

# Best-effort: mount addons blueprint if available
try:
    from addons.main_addons_calendar_vykazy import bp as addons_calendar_vykazy_bp  # type: ignore
    app.register_blueprint(addons_calendar_vykazy_bp)
    print("[INIT] addons.main_addons_calendar_vykazy: blueprint registered")
except Exception as e:
    print("[INIT] addons blueprint failed:", e)
    traceback.print_exc()
    # As a fallback, try legacy star import so existing routes remain available
    try:
        from addons.main_addons_calendar_vykazy import *  # type: ignore  # noqa: F401,F403
        print("[INIT] addons legacy import applied")
    except Exception as e2:
        print("[INIT] addons legacy import failed as well:", e2)
        traceback.print_exc()

# Explicit 404 handler to log path (helps debugging 502 vs 404)
@app.errorhandler(404)
def not_found(err):
    return "404: " + str(err), 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
