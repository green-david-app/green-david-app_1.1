
import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, session

app = Flask(__name__, static_folder=None)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,
)

ROOT_DIR = os.path.abspath(os.getcwd())
DATA_DIR = os.path.join(ROOT_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

JOBS_FILE = os.path.join(DATA_DIR, "jobs.json")
EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")
TIMESHEETS_FILE = os.path.join(DATA_DIR, "timesheets.json")

def _load_json(path, fallback):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return fallback

def _save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

if not os.path.exists(JOBS_FILE):
    _save_json(JOBS_FILE, [
        {"id": 2, "title": "zahrada Pavlíková", "name": "zahrada Pavlíková", "client": "Mackrle", "city": "Brno", "code": "09-2025", "status": "Probíhá", "date": "2025-09-22"}
    ])

if not os.path.exists(EMPLOYEES_FILE):
    _save_json(EMPLOYEES_FILE, [
        {"id": 1, "name": "Adam"},
        {"id": 2, "name": "David"}
    ])

if not os.path.exists(TIMESHEETS_FILE):
    _save_json(TIMESHEETS_FILE, [])

@app.get("/")
def index():
    return send_from_directory(ROOT_DIR, "index.html")

@app.get("/style.css")
def style_css():
    return send_from_directory(ROOT_DIR, "style.css")

@app.get("/logo.jpg")
def logo_jpg():
    return send_from_directory(ROOT_DIR, "logo.jpg")

@app.get("/logo.svg")
def logo_svg():
    return send_from_directory(ROOT_DIR, "logo.svg")

DEFAULT_ADMIN_EMAILS = {
    "admin@greendavid.local",
    "admin@greendavid.cz",
}
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

def _user_payload():
    if "user" in session:
        u = session["user"]
        return {"ok": True, "id": u["id"], "name": u["name"], "email": u["email"], "role": u["role"], "user": u}
    return {"ok": True, "user": None}

@app.get("/api/me")
def api_me():
    return jsonify(_user_payload())

@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or request.form.to_dict()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if (email in DEFAULT_ADMIN_EMAILS) and (password == DEFAULT_ADMIN_PASSWORD):
        user = {"id": 1, "name": "Admin", "email": email, "role": "admin"}
        session["user"] = user
        return jsonify({"ok": True, "user": user})
    return jsonify({"ok": False, "error": "invalid_credentials"}), 401

@app.post("/api/logout")
def api_logout():
    session.pop("user", None)
    return jsonify({"ok": True})

@app.get("/api/jobs")
def api_jobs_get():
    return jsonify(_load_json(JOBS_FILE, []))

@app.get("/api/employees")
def api_employees_get():
    return jsonify(_load_json(EMPLOYEES_FILE, []))

@app.get("/api/timesheets")
def api_timesheets_get():
    return jsonify(_load_json(TIMESHEETS_FILE, []))

def _pick(mapping, keys, default=None):
    for k in keys:
        if k in mapping and mapping[k] not in (None, ""):
            return mapping[k]
    return default

def _to_int(value, field_name):
    if value is None:
        raise ValueError(f"{field_name} is required")
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    if s == "":
        raise ValueError(f"{field_name} is required")
    s = s.replace(",", ".")
    try:
        return int(float(s))
    except Exception:
        raise ValueError(f"{field_name} must be a number")

@app.post("/api/timesheets")
def api_timesheets_post():
    payload = request.get_json(silent=True) or request.form.to_dict()

    date_raw = _pick(payload, ["date", "datum"])
    employee_raw = _pick(payload, ["employee_id", "employee", "zamestnanec_id", "zamestnanec"])
    job_raw = _pick(payload, ["job_id", "job", "zakazka_id", "zakazka"])
    hours_raw = _pick(payload, ["hours", "hodiny", "h"])
    note = _pick(payload, ["note", "poznámka", "poznamka"], "")

    try:
        if date_raw:
            try:
                date_obj = datetime.strptime(str(date_raw), "%Y-%m-%d")
            except ValueError:
                date_obj = datetime.strptime(str(date_raw), "%d.%m.%Y")
            date = date_obj.strftime("%Y-%m-%d")
        else:
            date = datetime.utcnow().strftime("%Y-%m-%d")

        employee_id = _to_int(employee_raw, "employee_id")
        job_id = _to_int(job_raw, "job_id")
        hours = _to_int(hours_raw, "hours")
    except ValueError as e:
        return jsonify({"ok": False, "error": "bad_payload", "message": str(e)}), 400

    ts = _load_json(TIMESHEETS_FILE, [])
    item = {
        "id": (ts[-1]["id"] + 1) if ts else 1,
        "date": date,
        "employee_id": employee_id,
        "job_id": job_id,
        "hours": hours,
        "note": note,
    }
    ts.append(item)
    _save_json(TIMESHEETS_FILE, ts)
    return jsonify({"ok": True, "item": item})

@app.post("/api/jobs")
def api_jobs_post():
    data = request.get_json(silent=True) or request.form.to_dict()
    jobs = _load_json(JOBS_FILE, [])
    item = {
        "id": (jobs[-1]["id"] + 1) if jobs else 1,
        "title": data.get("title") or data.get("name") or "Nová zakázka",
        "name": data.get("name") or data.get("title") or "Nová zakázka",
        "client": data.get("client") or "",
        "city": data.get("city") or "",
        "code": data.get("code") or "",
        "status": data.get("status") or "Plán",
        "date": data.get("date") or datetime.utcnow().strftime("%Y-%m-%d"),
    }
    jobs.append(item)
    _save_json(JOBS_FILE, jobs)
    return jsonify({"ok": True, "item": item})

@app.post("/api/employees")
def api_employees_post():
    data = request.get_json(silent=True) or request.form.to_dict()
    emps = _load_json(EMPLOYEES_FILE, [])
    item = {
        "id": (emps[-1]["id"] + 1) if emps else 1,
        "name": data.get("name") or "Nový zaměstnanec",
    }
    emps.append(item)
    _save_json(EMPLOYEES_FILE, emps)
    return jsonify({"ok": True, "item": item})

@app.get("/healthz")
def healthz():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
