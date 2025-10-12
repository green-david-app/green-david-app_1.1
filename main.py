
import os, sqlite3
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, g, render_template, session
import json

try:
    import openpyxl
except Exception:
    openpyxl = None

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data.sqlite"
XLS_JOBS = BASE_DIR / "zakazky.xlsx"
XLS_EMP = BASE_DIR / "zamestnanci.xlsx"
XLS_TS  = BASE_DIR / "vykazy.xlsx"

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
app.secret_key = os.environ.get("GD_SECRET_KEY", "gd-secret-key-change-me")
app.config.update(SESSION_COOKIE_NAME='gd_session', SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=True)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None: db.close()

def ensure_tables():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY, name TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS timesheets(id INTEGER PRIMARY KEY, employee_id INTEGER, date TEXT, hours REAL, place TEXT, activity TEXT, job_id INTEGER)")
    db.execute("CREATE TABLE IF NOT EXISTS calendar_events(id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, kind TEXT, title TEXT, note TEXT, job_id INTEGER, task_id INTEGER)")
    db.commit()

# ---------- helpers: XLSX fallback ----------
def load_xlsx_jobs():
    if not openpyxl or not XLS_JOBS.exists(): return []
    wb = openpyxl.load_workbook(str(XLS_JOBS), data_only=True)
    ws = wb.active
    cols = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        item = {}
        for i, v in enumerate(row):
            key = (cols[i] if i < len(cols) and cols[i] else f"col{i}").strip()
            item[key] = v
        # normalize
        if "id" not in item and "ID" in item: item["id"]=item["ID"]
        if "name" not in item and "Název" in item: item["name"]=item["Název"]
        out.append(item)
    return out

def load_xlsx_employees():
    if not openpyxl or not XLS_EMP.exists(): return []
    wb = openpyxl.load_workbook(str(XLS_EMP), data_only=True)
    ws = wb.active
    cols = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        item = {}
        for i, v in enumerate(row):
            key = (cols[i] if i < len(cols) and cols[i] else f"col{i}").strip()
            item[key] = v
        eid = item.get("id") or item.get("ID") or item.get("Id") or item.get("číslo") or len(out)+1
        name = item.get("name") or item.get("Jméno") or item.get("zamestnanec") or item.get("Zaměstnanec")
        out.append({"id": int(eid), "name": str(name) if name else f"Zaměstnanec {eid}"})
    return out

def load_xlsx_timesheets():
    if not openpyxl or not XLS_TS.exists(): return []
    wb = openpyxl.load_workbook(str(XLS_TS), data_only=True)
    ws = wb.active
    cols = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    out = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        item = {}
        for i, v in enumerate(row):
            key = (cols[i] if i < len(cols) and cols[i] else f"col{i}").strip()
            item[key] = v
        # normalize
        out.append({
            "id": item.get("id") or item.get("ID"),
            "employee_id": item.get("employee_id") or item.get("zamestnanec_id") or item.get("ZaměstnanecID"),
            "date": str(item.get("date") or item.get("datum") or ""),
            "hours": float(item.get("hours") or item.get("hodiny") or 0),
            "place": item.get("place") or item.get("misto") or "",
            "activity": item.get("activity") or item.get("cinnost") or "",
            "job_id": item.get("job_id") or item.get("zakazka_id"),
        })
    return out

@app.route("/healthz")
def healthz(): return "ok", 200

# Keep original look – jedna index.html pro /, /calendar, /timesheets
@app.route("/")
@app.route("/calendar")
@app.route("/timesheets")
def index(): return send_from_directory(str(BASE_DIR), "index.html")

@app.route("/calendar-page")
def calendar_page(): return render_template("calendar.html", title="Kalendář")

@app.route("/timesheets-page")
def timesheets_page(): return render_template("reports.html", title="Výkazy")

# ---------- AUTH ----------
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or data.get("email") or "Admin").strip() or "Admin"
    user = {"id": 1, "name": username, "role": "admin"}
    session["user"] = user
    payload = {"ok": True, "success": True, "isAuthenticated": True, "authenticated": True, "user": user, "name": user["name"], "redirect": "/"}
    return jsonify(payload)

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True, "success": True, "isAuthenticated": False, "authenticated": False})

@app.route("/api/me")
def api_me():
    user = session.get("user")
    if not user:
        return jsonify({"ok": True, "success": True, "isAuthenticated": False, "authenticated": False, "user": None, "name": None, "tasks_count": 0})
    return jsonify({"ok": True, "success": True, "isAuthenticated": True, "authenticated": True, "user": user, "name": user["name"], "tasks_count": 1})

# ---------- DATA WITH STORAGE AUTODETECT ----------
def have_sqlite_table(name:str)->bool:
    try:
        db = get_db()
        return db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None
    except Exception:
        return False

@app.route("/api/jobs")
def api_jobs():
    # Prefer SQLite jobs table; if not, try zakazky.xlsx
    if DB_PATH.exists() and have_sqlite_table("jobs"):
        db = get_db()
        rows = db.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
        jobs = [dict(r) for r in rows]
        return jsonify({"ok": True, "jobs": jobs})
    # XLSX fallback
    jobs = load_xlsx_jobs()
    return jsonify({"ok": True, "jobs": jobs})

@app.route("/api/employees")
def api_employees():
    if DB_PATH.exists() and have_sqlite_table("employees"):
        db = get_db()
        rows = db.execute("SELECT id, name FROM employees ORDER BY id ASC").fetchall()
        return jsonify({"employees":[dict(r) for r in rows]})
    # XLSX fallback
    return jsonify({"employees": load_xlsx_employees()})

@app.route("/api/timesheets")
def api_timesheets():
    ensure_tables()
    if DB_PATH.exists() and have_sqlite_table("timesheets"):
        db = get_db()
        rows = db.execute("SELECT t.*, e.name as employee FROM timesheets t LEFT JOIN employees e ON e.id=t.employee_id ORDER BY date DESC, id DESC").fetchall()
        return jsonify({"rows":[dict(r) for r in rows]})
    # XLSX fallback
    return jsonify({"rows": load_xlsx_timesheets()})

@app.route("/gd/api/calendar", methods=["GET","POST","DELETE"])
def api_calendar():
    ensure_tables()
    db = get_db()
    if request.method == "GET":
        y = request.args.get("year", type=int); m = request.args.get("month", type=int)
        if y and m:
            ym = f"{y:04d}-{m:02d}"
            rows = db.execute("SELECT * FROM calendar_events WHERE substr(date,1,7)=? ORDER BY date ASC", (ym,)).fetchall()
        else:
            rows = db.execute("SELECT * FROM calendar_events ORDER BY date DESC LIMIT 500").fetchall()
        return jsonify({"ok": True, "events":[dict(r) for r in rows]})
    if request.method == "POST":
        d = request.get_json(silent=True) or {}
        date = d.get("date"); kind = d.get("kind"); title = d.get("title"); note = d.get("note","")
        if not (date and kind and title): return jsonify({"ok": False, "error":"invalid"}), 400
        db.execute("INSERT INTO calendar_events(date,kind,title,note,job_id,task_id) VALUES (?,?,?,?,?,?)",
                   (date, kind, title, note, d.get("job_id"), d.get("task_id")))
        db.commit(); return jsonify({"ok": True})
    if request.method == "DELETE":
        eid = request.args.get("id", type=int)
        if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
        db.execute("DELETE FROM calendar_events WHERE id=?", (eid,)); db.commit(); return jsonify({"ok": True})

with app.app_context():
    ensure_tables()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT","8080")), debug=True)
