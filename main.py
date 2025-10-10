
# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import Flask, jsonify, request, session, send_from_directory

# ---------------- App setup ----------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-prod")
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@greendavid.local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DEFAULT_USER = {
    "id": 1,
    "name": "Admin",
    "email": ADMIN_EMAIL,
    "role": "admin",
}

# ------------- Optional addon -------------
try:
    from addons.main_addons_calendar_vykazy import bp as addons_calendar_vykazy_bp  # type: ignore
    app.register_blueprint(addons_calendar_vykazy_bp)
    print("[INIT] addons blueprint registered")
except Exception as e:
    print("[INIT] addons blueprint skipped:", e)

# ------------- Static/root ----------------
@app.route("/", methods=["GET"])
def root():
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

# ------------- Data (fallback) ------------
JOBS = [
    {"id": 2, "title": "zahrada Pavlíkova", "name": "zahrada Pavlíkova",
     "client": "Mackrle", "city": "Brno", "code": "09-2025",
     "date": "2025-09-22", "status": "Probíhá", "owner_id": 1,
     "created_at": "2025-10-09 20:38:37"},
    {"id": 3, "title": "závlaha Lovosice", "name": "závlaha Lovosice",
     "client": "OK Garden", "city": "Lovosice", "code": "11_2025",
     "date": "2025-11-10", "status": "Plán", "owner_id": 1,
     "created_at": "2025-10-10 12:00:00"},
]
EMPLOYEES = [
    {"id": 1, "name": "Adam"},
    {"id": 2, "name": "David"},
]
TIMESHEETS = []

# ------------- Helpers --------------------
def _read_cred_payload():
    """Accept JSON, form, or querystring; tolerate keys: email/username/e, password/pass/p"""
    data = request.get_json(silent=True) or {}
    if not data:
        if request.form:
            data = request.form.to_dict()
        elif request.args:
            data = request.args.to_dict()
        else:
            data = {}
    # unify keys
    email = (data.get("email") or data.get("username") or data.get("e") or "").strip().lower()
    password = data.get("password") or data.get("pass") or data.get("p") or ""
    return email, password

def _do_login(email: str, password: str):
    valid_emails = {ADMIN_EMAIL.lower(), "admin@greendavid.cz"}
    if email in valid_emails and password == ADMIN_PASSWORD:
        session["user"] = DEFAULT_USER
        session.permanent = True
        return True
    return False

# ------------- Auth -----------------------
@app.route("/api/login", methods=["POST", "GET"])
def api_login():
    email, password = _read_cred_payload()
    if _do_login(email, password):
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

# ------------- Business APIs --------------
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

    data = request.get_json(silent=True) or request.form or {}
    try:
        job_id = int(data.get("job_id"))
        hours = float(str(data.get("hours")).replace(",", "."))
        date_str = (data.get("date") or "").strip()
        if not date_str:
            raise ValueError("missing date")
        try:
            date_norm = datetime.fromisoformat(date_str).date().isoformat()
        except Exception:
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
        "hours": round(hours, 2),
        "note": note,
        "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    TIMESHEETS.append(entry)
    return jsonify({"ok": True, "entry": entry}), 201

# ------------- Health ---------------------
@app.route("/healthz")
def healthz():
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
