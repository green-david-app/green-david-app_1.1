
import os, sqlite3
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, g, render_template

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data.sqlite"
app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

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

@app.route("/healthz")
def healthz(): return "ok", 200

@app.route("/")
@app.route("/calendar")
@app.route("/timesheets")
def index(): return send_from_directory(str(BASE_DIR), "index.html")

@app.route("/calendar-page")
def calendar_page(): return render_template("calendar.html", title="Kalendář")

@app.route("/timesheets-page")
def timesheets_page(): return render_template("reports.html", title="Výkazy")

@app.route("/api/me")
def api_me():
    # Vždy přihlásit (aby UI neviselo na loginu)
    user = {"id":1,"name":"Admin","role":"admin"}
    return jsonify({"ok": True, "success": True, "isAuthenticated": True, "user": user, "name": user["name"], "tasks_count": 1})

@app.route("/api/login", methods=["POST"])
def api_login():
    user = {"id":1,"name":(request.json or {}).get("username","Admin"),"role":"admin"}
    return jsonify({"ok": True, "success": True, "isAuthenticated": True, "user": user, "name": user["name"], "redirect": "/"})

@app.route("/api/logout", methods=["POST"])
def api_logout(): return jsonify({"ok": True, "success": True, "isAuthenticated": False})

@app.route("/api/jobs")
def api_jobs():
    db = get_db()
    ok = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'").fetchone() is not None
    items = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()] if ok else []
    return jsonify({"ok": True, "jobs": items})

@app.route("/api/timesheets")
def api_timesheets():
    ensure_tables()
    db = get_db()
    rows = db.execute("SELECT t.*, e.name as employee FROM timesheets t LEFT JOIN employees e ON e.id=t.employee_id ORDER BY date DESC, id DESC").fetchall()
    return jsonify({"rows":[dict(r) for r in rows]})

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
