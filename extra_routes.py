
import os
from flask import jsonify, send_from_directory, render_template, request, current_app, abort
import importlib

main = importlib.import_module("main")

# Helper: find a readable, non-empty file across multiple typical locations
SEARCH_DIRS = ["", "templates", "static", "app", os.path.join("app","templates"), os.path.join("app","static")]
def _locate(fname):
    for d in SEARCH_DIRS:
        p = os.path.join(d, fname) if d else fname
        try:
            if os.path.isfile(p) and os.path.getsize(p) > 0:
                return os.path.dirname(p) or ".", os.path.basename(p)
        except Exception:
            continue
    return None, None

def _send_first(*candidates):
    for c in candidates:
        d,f = _locate(c)
        if d and f:
            return send_from_directory(d, f)
    # last resort: if file exists but empty, serve even empty to avoid 404
    for c in candidates:
        if os.path.exists(c):
            return send_from_directory(".", c)
    abort(404)

def _wrap_items(resp):
    try:
        data = resp.get_json()
    except Exception:
        data = None
    if isinstance(data, list):
        return jsonify({"items": data})
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return jsonify({"items": data["items"]})
        for key in ("rows","employees","events","data"):
            if key in data and isinstance(data[key], list):
                return jsonify({"items": data[key]})
    return resp

def attach(app):
    # UI routes
    @app.route("/calendar")
    def _ui_calendar():
        # Prefer app/templates/calendar.html, then ./calendar.html
        return _send_first(os.path.join("calendar.html"), os.path.join("calendar", "index.html"))

    @app.route("/timesheets")
    def _ui_timesheets():
        return _send_first("timesheets.html", os.path.join("timesheets","index.html"))

    # Static: ensure most common asset names work even if static_url_path is misconfigured
    @app.route("/style.css")
    def _style_css():
        return _send_first("style.css", os.path.join("static","style.css"), os.path.join("app","static","style.css"))

    @app.route("/logo.jpg")
    def _logo():
        return _send_first("logo.jpg", os.path.join("static","logo.jpg"), os.path.join("app","static","logo.jpg"))

    # Common JS entrypoints used by calendar page
    @app.route("/calendar.js")
    def _calendar_js():
        return _send_first("calendar.js", os.path.join("static","calendar.js"), os.path.join("app","static","calendar.js"), os.path.join("js","calendar.js"))

    @app.route("/script.js")
    def _script_js():
        return _send_first("script.js", os.path.join("static","script.js"), os.path.join("app","static","script.js"), os.path.join("js","script.js"))

    @app.route("/app.js")
    def _app_js():
        return _send_first("app.js", os.path.join("static","app.js"), os.path.join("app","static","app.js"), os.path.join("js","app.js"))

    # GD API aliases
    @app.route("/gd/api/calendar", methods=["GET","POST","PATCH","DELETE"])
    def _gd_api_calendar():
        resp = main.api_calendar()
        if request.method == "GET":
            return _wrap_items(resp)
        return resp

    @app.route("/gd/api/timesheets", methods=["GET","POST","DELETE"])
    def _gd_api_timesheets():
        resp = main.api_timesheets()
        if request.method == "GET":
            return _wrap_items(resp)
        return resp

    @app.route("/gd/api/employees", methods=["GET"])
    def _gd_api_employees():
        resp = main.api_employees()
        return _wrap_items(resp)

    return app
