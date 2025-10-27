
from flask import jsonify, send_from_directory, render_template, request
import importlib

# We import the already-loaded main module to reuse its view functions and DB.
# main is already imported by wsgi.py before calling attach().
main = importlib.import_module("main")

def _wrap_items(resp):
    """Normalize different API shapes to {items: [...]} expected by new frontends."""
    try:
        data = resp.get_json()
    except Exception:
        data = None
    # If original returns a list -> wrap into {items: list}
    if isinstance(data, list):
        return jsonify({"items": data})
    # If original returns a dict, try to find the list under common keys
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return jsonify({"items": data["items"]})
        for key in ("rows", "employees"):
            if key in data and isinstance(data[key], list):
                return jsonify({"items": data[key]})
    return resp

def attach(app):
    # Serve proper /static/* even if main app used static_url_path=""
    @app.route("/static/<path:filename>")
    def _gd_static(filename):
        return send_from_directory("static", filename)

    # UI routes
    @app.route("/calendar")
    def _gd_ui_calendar():
        try:
            return render_template("calendar.html")
        except Exception:
            # Fallback to serving plain file if Jinja templates are elsewhere
            return send_from_directory("templates", "calendar.html")

    @app.route("/timesheets")
    def _gd_ui_timesheets():
        try:
            return render_template("timesheets.html")
        except Exception:
            return send_from_directory("templates", "timesheets.html")

    # Aliases that map /gd/api/* -> /api/* and normalize payloads for the frontend
    @app.route("/gd/api/calendar", methods=["GET","POST","PATCH","DELETE"])
    def _gd_api_calendar():
        # Reuse the original function implemented in main.py
        resp = main.api_calendar()
        # Normalize GET responses to {items:[...]}
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
