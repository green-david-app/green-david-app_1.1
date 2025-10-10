# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import Flask, send_from_directory, jsonify, request

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, static_folder=None)

# -------------------------------
# Root & static file routes
# -------------------------------
@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.get("/style.css")
def static_css():
    return send_from_directory(BASE_DIR, "style.css", mimetype="text/css")

@app.get("/logo.svg")
def static_logo_svg():
    return send_from_directory(BASE_DIR, "logo.svg")

@app.get("/logo.jpg")
def static_logo_jpg():
    return send_from_directory(BASE_DIR, "logo.jpg")

# -------------------------------
# Optional blueprints
# -------------------------------
def _try_register_blueprint(import_path, attr_name="bp"):
    try:
        module = __import__(import_path, fromlist=[attr_name])
        bp = getattr(module, attr_name)
        app.register_blueprint(bp)
        print(f"[INIT] registered blueprint: {import_path}")
        return True
    except Exception as e:
        print(f"[INIT] skipped blueprint {import_path}: {e}")
        return False

_try_register_blueprint("addons.main_addons_calendar_vykazy")

# -------------------------------
# Minimal API fallbacks
# -------------------------------
_employees = [
    {"id": 1, "name": "Adam"},
    {"id": 2, "name": "David"},
]
_jobs = [
    {
        "id": 2,
        "title": "zahrada Pavlíkova",
        "name": "zahrada Pavlíkova",
        "client": "Mackrle",
        "city": "Brno",
        "code": "09-2025",
        "status": "Probíhá",
        "date": "2025-09-22",
        "owner_id": 1,
        "created_at": "2025-10-09 20:38:37",
        "note": None,
    },
    {
        "id": 3,
        "title": "závlaha Lovosice",
        "name": "závlaha Lovosice",
        "client": "OK Garden",
        "city": "Lovosice",
        "code": "11_2025",
        "status": "Plán",
        "date": "2025-11-10",
        "owner_id": 1,
        "created_at": "2025-10-10 12:00:00",
        "note": None,
    },
    {
        "id": 1,
        "title": "zahrada Třeboňice",
        "name": "zahrada Třeboňice",
        "client": "Adam",
        "city": "Praha",
        "code": "09-2025",
        "status": "Probíhá",
        "date": "2025-09-10",
        "owner_id": 1,
        "created_at": "2025-10-01 08:00:00",
        "note": None,
    },
]
_timesheets = []

def _ensure_iso_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
    except Exception:
        return None

@app.get("/api/me")
def api_me():
    return jsonify({
        "ok": True,
        "user": {"id": 1, "name": "Admin", "email": "admin@greendavid.local"}
    })

@app.get("/api/employees")
def api_employees():
    return jsonify({"ok": True, "data": _employees})

@app.get("/api/jobs")
def api_jobs():
    return jsonify({"ok": True, "data": _jobs})

@app.get("/api/timesheets")
def api_timesheets_list():
    return jsonify({"ok": True, "data": _timesheets})

@app.post("/api/timesheets")
def api_timesheets_create():
    try:
        payload = request.get_json(force=True, silent=True) or {}
        employee_id = int(payload.get("employee_id", 0))
        job_id = int(payload.get("job_id", 0))
        date = payload.get("date")
        hours = float(payload.get("hours", 0))
        note = (payload.get("note") or "").strip()

        if not employee_id or not any(e["id"] == employee_id for e in _employees):
            return jsonify({"ok": False, "error": "Neplatný zaměstnanec."}), 400
        if not job_id or not any(j["id"] == job_id for j in _jobs):
            return jsonify({"ok": False, "error": "Neplatná zakázka."}), 400
        if not _ensure_iso_date(date):
            return jsonify({"ok": False, "error": "Datum musí být ve formátu YYYY-MM-DD."}), 400
        if hours <= 0:
            return jsonify({"ok": False, "error": "Hodiny musí být větší než 0."}), 400

        new_item = {
            "id": (max([t["id"] for t in _timesheets]) + 1) if _timesheets else 1,
            "employee_id": employee_id,
            "job_id": job_id,
            "date": _ensure_iso_date(date),
            "hours": round(hours, 2),
            "note": note or None,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        }
        _timesheets.append(new_item)
        return jsonify({"ok": True, "data": new_item}), 201
    except Exception as e:
        return jsonify({"ok": False, "error": f"Nepodařilo se uložit: {e}"}), 400

@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")), debug=False)
