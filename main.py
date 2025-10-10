
# -*- coding: utf-8 -*-
import os
from datetime import datetime
from flask import Flask, jsonify, request, session, send_from_directory, redirect, url_for

app = Flask(__name__)

# ---- Session / cookies ----
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-prod")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,
)

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@greendavid.local")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

DEFAULT_USER = {
    "id": 1,
    "name": "Admin",
    "email": ADMIN_EMAIL,
    "role": "admin",
}

# ---- Optional addon: calendar & timesheets blueprint ----
try:
    from addons.main_addons_calendar_vykazy import bp as addons_calendar_vykazy_bp  # type: ignore
    app.register_blueprint(addons_calendar_vykazy_bp)
    print("[INIT] addons blueprint registered")
except Exception as e:
    print("[INIT] addons blueprint skipped:", e)

# ---- Static files ----
@app.get("/")
def root():
    index = os.path.join(ROOT_DIR, "index.html")
    if os.path.exists(index):
        return send_from_directory(ROOT_DIR, "index.html")
    return (
        "<!doctype html><meta charset='utf-8'><title>Green David</title>"
        "<h1>Green David</h1><p>index.html nebyl nalezen v kořenu.</p>",
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )

@app.get("/style.css")
def style_css():
    path = os.path.join(ROOT_DIR, "style.css")
    if os.path.exists(path):
        return send_from_directory(ROOT_DIR, "style.css")
    return "", 200, {"Content-Type": "text/css"}

@app.get("/logo.svg")
def logo_svg():
    path = os.path.join(ROOT_DIR, "logo.svg")
    if os.path.exists(path):
        return send_from_directory(ROOT_DIR, "logo.svg")
    return "", 200, {"Content-Type": "image/svg+xml"}

@app.get("/logo.jpg")
def logo_jpg():
    path = os.path.join(ROOT_DIR, "logo.jpg")
    if os.path.exists(path):
        return send_from_directory(ROOT_DIR, "logo.jpg")
    return "", 200, {"Content-Type": "image/jpeg"}

# ---- In-memory fallback data ----
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

# ---- Helpers ----
def _read_cred_payload():
    data = request.get_json(silent=True) or {}
    if not data:
        if request.form:
            data = request.form.to_dict()
        elif request.args:
            data = request.args.to_dict()
        else:
            data = {}
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

# ---- No-cache for API responses ----
@app.after_request
def add_no_cache_headers(resp):
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
    return resp

# ---- Auth APIs ----
@app.route("/api/login", methods=["POST", "GET"])
def api_login():
    email, password = _read_cred_payload()
    if _do_login(email, password):
        return jsonify({"ok": True, "user": DEFAULT_USER})
    return jsonify({"ok": False, "error": "invalid_credentials"}), 401

@app.get("/dev-login")
def dev_login():
    session["user"] = DEFAULT_USER
    session.permanent = True
    return redirect(url_for("root"))

@app.post("/api/logout")
def api_logout():
    session.pop("user", None)
    return jsonify({"ok": True})

@app.get("/api/me")
def api_me():
    user = session.get("user")
    if user:
        payload = {"ok": True, "user": user}
        payload.update(user)  # flatten id/name/email/role for older UI
        return jsonify(payload)
    return jsonify({"ok": True, "user": None})

# ---- Business APIs ----
@app.get("/api/jobs")
def api_jobs():
    return jsonify({"ok": True, "jobs": JOBS})

@app.get("/api/employees")
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

# ---- Health ----
@app.get("/healthz")
def healthz():
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port, debug=False)
