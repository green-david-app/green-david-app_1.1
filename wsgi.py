
# WSGI bootstrap with enforced template/static folders and UI/API routes
from main import app as _app

# Normalize Flask paths (works even if main set static_folder="." originally)
_app.template_folder = "app/templates"
_app.static_folder = "static"
_app.static_url_path = "/static"

# --- UI routes ---
from flask import render_template, send_from_directory

@_app.route("/calendar")
def _ui_calendar():
    # render new calendar UI under app/templates/calendar.html
    return render_template("calendar.html")

@_app.route("/timesheets")
def _ui_timesheets():
    try:
        return render_template("timesheets.html")
    except Exception:
        # optional legacy page
        return send_from_directory(".", "timesheets.html")

# --- Compatibility: serve root assets if links point to them ---
@_app.route("/style.css")
def _root_style():
    # prefer new app/static/css/app.css if present; else fall back to legacy style.css
    try:
        return send_from_directory("static/css", "app.css")
    except Exception:
        return send_from_directory(".", "style.css")

@_app.route("/logo.jpg")
def _root_logo_jpg():
    return send_from_directory("static", "logo.jpg")

@_app.route("/logo.svg")
def _root_logo_svg():
    return send_from_directory("static", "logo.svg")

# --- GD API aliases mapping to original endpoints ---
from flask import request, jsonify
def _wrap_items(obj):
    # ensure {items:[]} for GET responses
    try:
        data = obj.get_json()
    except Exception:
        data = None
    if isinstance(data, list):
        return jsonify({"items": data})
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list): return jsonify({"items": data["items"]})
        for k in ("rows","employees","events","data"):
            if k in data and isinstance(data[k], list): return jsonify({"items": data[k]})
    return obj

from main import api_calendar as _api_calendar, api_timesheets as _api_timesheets, api_employees as _api_employees

@_app.route("/gd/api/calendar", methods=["GET","POST","PATCH","DELETE"])
def _gd_api_calendar():
    resp = _api_calendar()
    return _wrap_items(resp) if request.method=="GET" else resp

@_app.route("/gd/api/timesheets", methods=["GET","POST","DELETE"])
def _gd_api_timesheets():
    resp = _api_timesheets()
    return _wrap_items(resp) if request.method=="GET" else resp

@_app.route("/gd/api/employees", methods=["GET"])
def _gd_api_employees():
    return _wrap_items(_api_employees())

# Expose as WSGI callable
app = _app
