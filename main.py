
import os, sqlite3, json
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template, g

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data.sqlite"

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")
app.secret_key = 'gd-secret-key-change-me'
app.config.update(SESSION_COOKIE_NAME='gd_session', SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=True)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def ensure_tables():
    db = get_db()
    # původní tabulky (pokud už ve tvé 1.1 jsou, CREATE IF NOT EXISTS je idempotentní)
    db.execute("CREATE TABLE IF NOT EXISTS employees(id INTEGER PRIMARY KEY, name TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS timesheets(id INTEGER PRIMARY KEY, employee_id INTEGER, date TEXT, hours REAL, place TEXT, activity TEXT, job_id INTEGER)")
    db.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('zakazka','ukol','poznamka')),
            title TEXT NOT NULL,
            note  TEXT,
            job_id INTEGER,
            task_id INTEGER
        )
    """)
    db.commit()

def require_auth():
    # kompatibilní se stávající logikou: pro teď vždy povolit (1.1 měla "admin" mock)
    return {"id":1,"name":"Admin"}, None

# --------- HEALTH ---------
@app.route("/healthz")
def healthz():
    return "ok", 200

# --------- ROOT & STATIC ---------
@app.route("/")
def root():
    # vždy vrať index.html z kořene (stejný layout jako původní)
    return send_from_directory(str(BASE_DIR), "index.html")

# aliasy, aby hlavička zůstala stejná (SPA)
@app.route("/calendar")
@app.route("/timesheets")
def spa_pages():
    return send_from_directory(str(BASE_DIR), "index.html")

# --------- API: zaměstnanci & výkazy (minimální, kompatibilní) ---------
@app.route("/api/employees")
def api_employees():
    u, err = require_auth()
    if err: return err
    db = get_db()
    rows = db.execute("SELECT id, name FROM employees ORDER BY id ASC").fetchall()
    return jsonify({"employees":[dict(r) for r in rows]})

@app.route("/api/timesheets")
def api_timesheets():
    u, err = require_auth()
    if err: return err
    db = get_db()
    rows = db.execute("SELECT t.*, e.name as employee FROM timesheets t LEFT JOIN employees e ON e.id=t.employee_id ORDER BY date DESC, id DESC").fetchall()
    return jsonify({"rows":[dict(r) for r in rows]})

# --------- API: kalendář ---------
@app.route("/gd/api/calendar", methods=["GET","POST","DELETE"])
def gd_calendar():
    u, err = require_auth()
    if err: return err
    db = get_db()
    if request.method == "GET":
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        if year and month:
            ym = f"{year:04d}-{month:02d}"
            rows = db.execute("SELECT * FROM calendar_events WHERE substr(date,1,7)=? ORDER BY date ASC, id DESC", (ym,)).fetchall()
        else:
            rows = db.execute("SELECT * FROM calendar_events ORDER BY date DESC, id DESC LIMIT 500").fetchall()
        return jsonify({"ok": True, "events":[dict(r) for r in rows]})
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        date_s = data.get("date"); kind = data.get("kind"); title = data.get("title"); note = data.get("note","")
        job_id = data.get("job_id"); task_id = data.get("task_id")
        if not (date_s and kind in ("zakazka","ukol","poznamka") and title):
            return jsonify({"ok": False, "error":"invalid_input"}), 400
        db.execute("INSERT INTO calendar_events(date,kind,title,note,job_id,task_id) VALUES (?,?,?,?,?,?)",
                   (date_s, kind, title, note, job_id, task_id))
        db.commit()
        return jsonify({"ok": True})
    if request.method == "DELETE":
        eid = request.args.get("id", type=int)
        if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
        db.execute("DELETE FROM calendar_events WHERE id=?", (eid,))
        db.commit()
        return jsonify({"ok": True})

# --------- server-render fallback stránky ---------
from flask import render_template_string

LAYOUT_HEAD = """
<link rel="stylesheet" href="/style.css">
<div class="tabs">
  <a href="/calendar" class="tab">Kalendář</a>
  <a href="/timesheets" class="tab">Výkazy</a>
  <a href="/" class="tab">Zakázky</a>
</div>
"""

@app.route("/calendar-page")
def calendar_page():
    u, err = require_auth()
    if err: return err
    ensure_tables()
    # zobrazení přes jednoduchou šablonu; SPA verze je na /calendar
    return render_template("calendar.html", title="Kalendář")

@app.route("/timesheets-page")
def timesheets_page():
    u, err = require_auth()
    if err: return err
    ensure_tables()
    return render_template("reports.html", title="Výkazy")

# --------- init ---------
with app.app_context():
    ensure_tables()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)


# --------- API: /api/me (compat) ---------
@app.route("/api/me")
def api_me():
    from flask import session
    user = session.get("user")
    if not user:
        # unauthenticated, but keep legacy shape
        payload = {"ok": True, "isAuthenticated": False, "user": None, "name": None, "tasks_count": 0}
        return jsonify(payload)
    payload = {
        "ok": True,
        "success": True,
        "isAuthenticated": True,
        "user": user,
        "name": user.get("name"),
        "tasks_count": 1
    }
    return jsonify(payload)


# --------- API: /api/jobs (best-effort) ---------
@app.route("/api/jobs")
def api_jobs():
    u, err = require_auth()
    if err: return err
    db = get_db()
    exists = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'").fetchone()
    jobs = []
    if exists:
        rows = db.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
        jobs = [dict(r) for r in rows]
    return jsonify({"ok": True, "jobs": jobs})


# --------- Auth compatibility ---------
@app.route("/api/login", methods=["POST"])
def api_login():
    from flask import session
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or data.get("email") or "Admin").strip() or "Admin"
    user = {"id": 1, "name": username, "role": "admin"}
    session["user"] = user
    payload = {
        "ok": True,
        "success": True,
        "isAuthenticated": True,
        "user": user,
        "name": user["name"],
        "redirect": "/"
    }
    return jsonify(payload)

@app.route("/logout")
def logout():
    from flask import session, redirect
    session.clear()
    return redirect("/")


@app.route("/api/logout", methods=["POST"])
def api_logout():
    from flask import session, jsonify
    session.clear()
    return jsonify({"ok": True, "success": True, "isAuthenticated": False})
