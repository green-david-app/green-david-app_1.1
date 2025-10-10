
import os
from datetime import datetime
from flask import Flask, jsonify, request, session, send_from_directory

# --- App setup ---------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-prod")

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

# Allow overriding admin via env
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@greendavid.local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DEFAULT_USER = {
    "id": 1,
    "name": "Admin",
    "email": ADMIN_EMAIL,
    "role": "admin",
}

# --- Optional addon (calendar & timesheets via blueprint) --------------------
try:
    # If your repo has addons/main_addons_calendar_vykazy.py with `bp` blueprint
    # this will be used; otherwise we continue without crashing.
    from addons.main_addons_calendar_vykazy import bp as addons_calendar_vykazy_bp  # type: ignore
    app.register_blueprint(addons_calendar_vykazy_bp)
    print("[INIT] addons blueprint registered")
except Exception as e:
    print("[INIT] addons blueprint skipped:", e)

# --- Static / root routes ----------------------------------------------------
@app.route("/", methods=["GET"])
def root():
    # Serve index.html directly from the repo root (same place as main.py)
    # to match your existing project layout.
    return send_from_directory(ROOT_DIR, "index.html")

@app.route("/style.css")
def style_css():
    return send_from_directory(ROOT_DIR, "style.css")

@app.route("/logo.svg")
def logo_svg():
    return send_from_directory(ROOT_DIR, "logo.svg")

@app.route("/logo.jpg")
def logo_jpg():
    return send_from_directory(ROOT_DIR, "logo.jpg")

# --- Lightweight in-memory data (fallback for UI to work) --------------------
JOBS = [
    {
        "id": 2,
        "title": "zahrada Pavlíkova",
        "name": "zahrada Pavlíkova",
        "client": "Mackrle",
        "city": "Brno",
        "code": "09-2025",
        "date": "2025-09-22",
        "status": "Probíhá",
        "owner_id": 1,
        "created_at": "2025-10-09 20:38:37",
    },
    {
        "id": 3,
        "title": "závlaha Lovosice",
        "name": "závlaha Lovosice",
        "client": "OK Garden",
        "city": "Lovosice",
        "code": "11_2025",
        "date": "2025-11-10",
        "status": "Plán",
        "owner_id": 1,
        "created_at": "2025-10-10 12:00:00",
    },
]

EMPLOYEES = [
    {"id": 1, "name": "Adam"},
    {"id": 2, "name": "David"},
]

TIMESHEETS = []  # simple in-memory store so UI má kam zapisovat

# --- Auth-like endpoints (very simple session) -------------------------------
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or request.form or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    valid_emails = {ADMIN_EMAIL.lower(), "admin@greendavid.cz"}
    if email in valid_emails and password == ADMIN_PASSWORD:
        session["user"] = DEFAULT_USER
        return jsonify({"ok": True, "user": DEFAULT_USER})

    return jsonify({"ok": False, "error": "invalid_credentials"}), 401

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user", None)
    return jsonify({"ok": True})

@app.route("/api/me")
def api_me():
    user = session.get("user")
    return jsonify({"ok": True, "user": user})

# --- Business endpoints used by the UI --------------------------------------
@app.route("/api/jobs")
def api_jobs():
    return jsonify({"ok": True, "jobs": JOBS})

@app.route("/api/employees")
def api_employees():
    return jsonify({"ok": True, "employees": EMPLOYEES})

@app.route("/api/timesheets", methods=["GET", "POST"])
def api_timesheets():
    if request.method == "GET":
        return jsonify({"ok": True, "work_logs": TIMESHEETS})

    # POST create
    data = request.get_json(silent=True) or request.form or {}
    try:
        job_id = int(data.get("job_id"))
        hours = float(data.get("hours"))
        date_str = (data.get("date") or "").strip()
        if not date_str:
            raise ValueError("missing date")
        # normalize date to YYYY-MM-DD if possible
        try:
            date_norm = datetime.fromisoformat(date_str).date().isoformat()
        except Exception:
            # try dd.mm.yyyy
            try:
                d, m, y = date_str.split(".")
                date_norm = datetime(int(y), int(m), int(d)).date().isoformat()
            except Exception:
                date_norm = date_str
        employee_id = int(data.get("employee_id") or 1)
        note = data.get("note") or ""
    except Exception as e:
        return jsonify({"ok": False, "error": f"bad_payload: {e}"}), 400

    entry = {
        "id": len(TIMESHEETS) + 1,
        "job_id": job_id,
        "employee_id": employee_id,
        "date": date_norm,
        "hours": hours,
        "note": note,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    TIMESHEETS.append(entry)
    return jsonify({"ok": True, "entry": entry}), 201

# --- Health ------------------------------------------------------------------
@app.route("/healthz")
def healthz():
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
