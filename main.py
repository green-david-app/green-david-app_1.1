
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, jsonify, send_file, session, make_response
from werkzeug.middleware.proxy_fix import ProxyFix

APP_ROOT = Path(__file__).resolve().parent
DATA_DIR = APP_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- Helpers -----------------------------------------------------------------
def _json_load(path: Path, default):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default

def _json_save(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)

def _to_float_hours(v):
    if v is None:
        raise ValueError("hodiny (hours) chybí")
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")
    return float(s)

def _to_int(v, field_name):
    if v is None or str(v).strip() == "":
        raise ValueError(f"{field_name} chybí")
    return int(str(v).strip())

def _parse_date(v):
    if isinstance(v, (datetime, )):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    # Podporuj i DD.MM.YYYY
    try:
        if "." in s:
            return datetime.strptime(s, "%d.%m.%Y").strftime("%Y-%m-%d")
        return datetime.strptime(s, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        raise ValueError("datum má být ve formátu YYYY-MM-DD nebo DD.MM.YYYY")

# --- Flask app ---------------------------------------------------------------
app = Flask(__name__)

# Bezpečné session cookies + reverzní proxy fix (Render)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

app.config.update(
    SESSION_COOKIE_NAME="gd_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None",   # funguje v Safari přes HTTPS
    SESSION_COOKIE_SECURE=True,       # Render je HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)

# --- Static files ------------------------------------------------------------
@app.get("/")
def index():
    index_html = APP_ROOT / "index.html"
    if index_html.exists():
        return send_file(index_html)
    # fallback minimalistický login (když chybí index.html)
    return """
    <html><body style="font-family: system-ui;">
      <h3>green david app</h3>
      <form onsubmit="login(event)">
        <input id="email" value="admin@greendavid.cz">
        <input id="password" type="password" value="admin123">
        <button>Login</button>
      </form>
      <script>
        async function login(e){
          e.preventDefault();
          const r = await fetch('/api/login', {
            method:'POST', headers:{'Content-Type':'application/json'},
            credentials:'include',
            body: JSON.stringify({
              email: document.getElementById('email').value,
              password: document.getElementById('password').value
            })
          });
          const j = await r.json();
          if(j.ok){ location.href='/' } else { alert(j.error || 'Login failed'); }
        }
      </script>
    </body></html>
    """, 200, {"Content-Type":"text/html; charset=utf-8"}

@app.get("/style.css")
def style():
    css = APP_ROOT / "style.css"
    if css.exists():
        return send_file(css)
    return "", 200, {"Content-Type": "text/css"}

@app.get("/logo.jpg")
def logo_jpg():
    p = APP_ROOT / "logo.jpg"
    if p.exists():
        return send_file(p)
    return "", 200

@app.get("/logo.svg")
def logo_svg():
    p = APP_ROOT / "logo.svg"
    if p.exists():
        return send_file(p)
    return "", 200

# --- Auth --------------------------------------------------------------------
USERS_FILE = DATA_DIR / "users.json"

def _ensure_admin_user():
    users = _json_load(USERS_FILE, [])
    if not users:
        users = [{
            "id": 1,
            "name": "Admin",
            "email": "admin@greendavid.cz",
            "role": "admin",
            "password": os.environ.get("ADMIN_PASSWORD", "admin123"),
        }]
        _json_save(USERS_FILE, users)
    return users

@app.post("/api/login")
def api_login():
    payload = request.get_json(silent=True) or request.form
    email = (payload.get("email") or "").strip().lower()
    password = (payload.get("password") or "").strip()

    users = _ensure_admin_user()
    user = next((u for u in users if u["email"].lower() == email), None)
    if not user or user.get("password") != password:
        return jsonify({"ok": False, "error": "Špatný e-mail nebo heslo"}), 401

    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]

    res = jsonify({"ok": True, "id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]})
    return res

@app.post("/api/logout")
def api_logout():
    session.clear()
    return jsonify({"ok": True})

@app.get("/api/me")
def api_me():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"ok": False})
    users = _ensure_admin_user()
    user = next((u for u in users if u["id"] == uid), None)
    if not user:
        session.clear()
        return jsonify({"ok": False})
    return jsonify({
        "ok": True,
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]}
    })

# --- Data endpoints ----------------------------------------------------------
JOBS_FILE = DATA_DIR / "jobs.json"
EMP_FILE  = DATA_DIR / "employees.json"
TS_FILE   = DATA_DIR / "timesheets.json"

def _require_login():
    if not session.get("user_id"):
        return False, (jsonify({"ok": False, "error": "Unauthenticated"}), 401)
    return True, None

@app.get("/api/jobs")
def api_jobs_list():
    ok, resp = _require_login()
    if not ok: return resp
    jobs = _json_load(JOBS_FILE, [{
        "id": 2,
        "name": "zahrada Pavlíkova",
        "title": "zahrada Pavlíkova",
        "client": "Mackrle",
        "city": "Brno",
        "code": "09-2025",
        "date": "2025-09-22",
        "status": "Probíhá"
    }])
    return jsonify(jobs)

@app.post("/api/jobs")
def api_jobs_add():
    ok, resp = _require_login()
    if not ok: return resp
    payload = request.get_json(silent=True) or request.form

    jobs = _json_load(JOBS_FILE, [])
    new_id = (max([j.get("id", 0) for j in jobs]) + 1) if jobs else 1
    job = {
        "id": new_id,
        "name": payload.get("name") or payload.get("title") or "Nová zakázka",
        "title": payload.get("title") or payload.get("name") or "Nová zakázka",
        "client": payload.get("client") or "",
        "city": payload.get("city") or "",
        "code": payload.get("code") or "",
        "date": _parse_date(payload.get("date") or datetime.utcnow().strftime("%Y-%m-%d")),
        "status": payload.get("status") or "Plán"
    }
    jobs.append(job)
    _json_save(JOBS_FILE, jobs)
    return jsonify({"ok": True, "job": job})

@app.get("/api/employees")
def api_employees():
    ok, resp = _require_login()
    if not ok: return resp
    employees = _json_load(EMP_FILE, [{"id": 1, "name": "Adam"}])
    return jsonify(employees)

@app.post("/api/employees")
def api_employees_add():
    ok, resp = _require_login()
    if not ok: return resp
    payload = request.get_json(silent=True) or request.form
    employees = _json_load(EMP_FILE, [])
    new_id = (max([e.get("id", 0) for e in employees]) + 1) if employees else 1
    emp = {"id": new_id, "name": payload.get("name") or "Nový zaměstnanec"}
    employees.append(emp)
    _json_save(EMP_FILE, employees)
    return jsonify({"ok": True, "employee": emp})

@app.get("/api/timesheets")
def api_timesheets_list():
    ok, resp = _require_login()
    if not ok: return resp
    ts = _json_load(TS_FILE, [])
    return jsonify(ts)

@app.post("/api/timesheets")
def api_timesheets_add():
    ok, resp = _require_login()
    if not ok: return resp

    p = request.get_json(silent=True) or request.form

    try:
        date_in   = p.get("date") or p.get("datum")
        employee  = p.get("employee_id") or p.get("employee") or p.get("zamestnanec") or p.get("zaměstnanec")
        job       = p.get("job_id") or p.get("job") or p.get("zakazka") or p.get("zakázka")
        hours_in  = p.get("hours") or p.get("hodiny") or p.get("h")
        note      = (p.get("note") or p.get("poznamka") or p.get("poznámka") or "").strip()

        rec = {
            "id": int(datetime.utcnow().timestamp() * 1000),
            "date": _parse_date(date_in),
            "employee_id": _to_int(employee, "zaměstnanec"),
            "job_id": _to_int(job, "zakázka"),
            "hours": _to_float_hours(hours_in),
            "note": note,
        }
    except ValueError as e:
        return jsonify({"ok": False, "error": f"bad_payload: {e}"}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": "bad_payload: " + str(e)}), 400

    ts = _json_load(TS_FILE, [])
    ts.append(rec)
    _json_save(TS_FILE, ts)
    return jsonify({"ok": True, "timesheet": rec})

# --- Misc --------------------------------------------------------------------
@app.after_request
def _no_cache(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
