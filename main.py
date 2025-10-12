
from flask import Flask, send_from_directory, request, jsonify, session, g, send_file, abort, render_template
import sqlite3, os, json, datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","dev")

DB_PATH = os.path.join(os.path.dirname(__file__), "db.sqlite3")

def get_db():
    if not hasattr(g, "_db"):
        g._db = sqlite3.connect(DB_PATH)
        g._db.row_factory = sqlite3.Row
    return g._db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

def migrate(db):
    # no-op placeholder for existing migrations
    pass

def ensure_columns(db):
    # no-op placeholder for existing ensure_columns
    pass

def ensure_calendar_schema(db):
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

# ---- minimal mock auth (replace with your existing require_auth) ----
def require_auth():
    # If original app has auth, swap this for the original import/func.
    return {"name":"Admin","role":"admin"}, None

# ---- app init ----
with app.app_context():
    db = get_db()
    migrate(db)
    ensure_columns(db)
    ensure_calendar_schema(db)
    db.commit()

# ------------------ STATIC/ROOT ------------------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

# ------------------ CALENDAR API -----------------
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

# ------------------ PAGES ------------------------
@app.route("/calendar")
def calendar_page():
    u, err = require_auth()
    if err: return err
    return render_template("calendar.html", title="Kalendář")

@app.route("/timesheets")
def timesheets_page():
    u, err = require_auth()
    if err: return err
    return render_template("reports.html", title="Výkazy")
