import os
import io
import sqlite3
from datetime import datetime, date
from flask import (
    Flask, request, jsonify, g, send_from_directory, send_file,
    render_template, abort
)

# --------------------------------------------------------------------------------------
# Konfigurace aplikace
# --------------------------------------------------------------------------------------
DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --------------------------------------------------------------------------------------
# DB utilitky
# --------------------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        # zajistí meta tabulku a základní migrace
        ensure_meta(g.db)
        migrate(g.db)
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def ensure_meta(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS app_meta (
          id INTEGER PRIMARY KEY CHECK (id=1),
          version INTEGER NOT NULL
        )
    """)
    row = db.execute("SELECT version FROM app_meta WHERE id=1").fetchone()
    if row is None:
        db.execute("INSERT INTO app_meta(id,version) VALUES (1,0)")
        db.commit()

def get_version(db):
    row = db.execute("SELECT version FROM app_meta WHERE id=1").fetchone()
    return row["version"]

def set_version(db, v):
    db.execute("UPDATE app_meta SET version=? WHERE id=1", (v,))
    db.commit()

def migrate(db):
    """
    Jednoduchý migrační systém podle čísla verze:
    v1: users
    v2: calendar_events (+ color hned v DDL)
    v3: jobs, tasks
    v4: timesheets
    Pozn.: opatrně – produkční DB může tabulky mít; ALTER provádíme idempotentně.
    """
    v = get_version(db)

    if v < 1:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE,
              name TEXT,
              role TEXT,
              password_hash TEXT,
              active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL
            )
        """)
        # seed admina, ať /api/me může vracet něco smysluplného
        now = datetime.utcnow().isoformat(timespec="seconds")
        cur = db.execute("SELECT COUNT(*) AS c FROM users")
        if cur.fetchone()["c"] == 0:
            db.execute("""
                INSERT INTO users(email,name,role,password_hash,active,created_at)
                VALUES (?,?,?,?,1,?)
            """, (os.environ.get("ADMIN_EMAIL","admin@greendavid.local"),
                  os.environ.get("ADMIN_NAME","Admin"),
                  "admin","", now))
        db.commit()
        set_version(db, 1)
        v = 1

    if v < 2:
        # přidáme tabulku kalendáře – rovnou s color
        db.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              date TEXT NOT NULL,
              title TEXT,
              kind TEXT NOT NULL DEFAULT 'note',
              job_id INTEGER,
              start_time TEXT,
              end_time TEXT,
              note TEXT,
              color TEXT DEFAULT 'green'
            )
        """)
        db.commit()
        set_version(db, 2)
        v = 2

    if v < 3:
        # základní tabulky pro /api/jobs a /api/tasks
        db.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              code TEXT,
              customer TEXT,
              created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
        """)
        db.commit()
        set_version(db, 3)
        v = 3

    if v < 4:
        # jednoduché timesheets
        db.execute("""
            CREATE TABLE IF NOT EXISTS timesheets (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER,
              date TEXT NOT NULL,
              hours REAL NOT NULL DEFAULT 0,
              job_id INTEGER,
              note TEXT,
              created_at TEXT NOT NULL
            )
        """)
        db.commit()
        set_version(db, 4)
        v = 4

# --------------------------------------------------------------------------------------
# Pomocné funkce
# --------------------------------------------------------------------------------------
def _normalize_date(v):
    if not v:
        return None
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    # ošetřit yyyy-mm-dd
    try:
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            datetime.strptime(s, "%Y-%m-%d")
            return s
    except Exception:
        pass
    # pokus o auto-parse
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass
    return s

normalize_date = _normalize_date  # kompatibilita s původním kódem

def require_auth():
    """
    Minimalistický mock přihlášení:
    Vrací admin uživatele (id=1), aby frontend /api/me fungoval.
    """
    db = get_db()
    u = db.execute("SELECT id, email, name, role, active FROM users WHERE id=1").fetchone()
    if not u or not u["active"]:
        return None, (jsonify({"error":"unauthorized"}), 401)
    return u, None

def require_role(write=False):
    # stejné jako require_auth – v ostré verzi by se kontrolovala role/perm
    return require_auth()

# --------------------------------------------------------------------------------------
# Calendar: tabulka a migrace sloupců (idempotentně)
# --------------------------------------------------------------------------------------
def ensure_calendar_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          date TEXT NOT NULL,
          title TEXT,
          kind TEXT NOT NULL DEFAULT 'note',
          job_id INTEGER,
          start_time TEXT,
          end_time TEXT,
          note TEXT,
          color TEXT DEFAULT 'green'
        )
    """)
    db.commit()

def migrate_calendar_columns():
    db = get_db()
    cols = [r[1] for r in db.execute("PRAGMA table_info(calendar_events)").fetchall()]
    def add_col(name, ddl):
        if name not in cols:
            db.execute(f"ALTER TABLE calendar_events ADD COLUMN {ddl}")
    # držíme kompatibilitu, kdyby DB vznikla dávno
    add_col("kind", "TEXT NOT NULL DEFAULT 'note'")
    add_col("job_id", "INTEGER")
    add_col("start_time", "TEXT")
    add_col("end_time", "TEXT")
    add_col("note", "TEXT DEFAULT ''")
    add_col("color", "TEXT DEFAULT 'green'")
    db.commit()

# --------------------------------------------------------------------------------------
# API endpoints
# --------------------------------------------------------------------------------------
@app.route("/api/me")
def api_me():
    u, err = require_auth()
    if err: return err
    return jsonify({
        "id": u["id"], "email": u["email"], "name": u["name"],
        "role": u["role"], "active": bool(u["active"])
    })

@app.route("/api/jobs")
def api_jobs():
    # jednoduchý výpis, ať se homepage/hlavičky nezaseknou
    db = get_db()
    rows = db.execute("SELECT id, title, code, customer, created_at FROM jobs ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/tasks")
def api_tasks():
    db = get_db()
    rows = db.execute("SELECT id, title, created_at FROM tasks ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/gd/api/calendar", methods=["GET","POST","PATCH","DELETE"])
def api_calendar():
    u, err = require_role(write=(request.method != "GET"))
    if err: return err
    db = get_db()
    ensure_calendar_table()

    if request.method == "GET":
        d_from = request.args.get("from")
        d_to = request.args.get("to")
        migrate_calendar_columns()
        if d_from and d_to:
            rows = db.execute("""
                SELECT * FROM calendar_events
                 WHERE date BETWEEN ? AND ?
                 ORDER BY date ASC, COALESCE(start_time,'') ASC
            """, (d_from, d_to)).fetchall()
        else:
            rows = db.execute("""
                SELECT * FROM calendar_events
                 ORDER BY date DESC, COALESCE(start_time,'') ASC
                 LIMIT 1000
            """).fetchall()
        return jsonify([dict(r) for r in rows])

    data = request.get_json(force=True, silent=True) or {}

    if request.method == "POST":
        date_s = normalize_date(data.get("date"))
        title = (data.get("title") or "").strip() or None
        kind = (data.get("kind") or "note").strip()
        job_id = data.get("job_id")
        start_time = (data.get("start_time") or None)
        end_time = (data.get("end_time") or None)
        note = (data.get("note") or "").strip()
        color = (data.get("color") or "green").strip()
        if not date_s:
            return jsonify({"error": "Missing date or title"}), 400
        cur = db.execute("""
            INSERT INTO calendar_events(date,title,kind,job_id,start_time,end_time,note,color)
            VALUES (?,?,?,?,?,?,?,?)
        """, (date_s, title, kind, job_id, start_time, end_time, note, color))
        db.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})

    if request.method == "PATCH":
        eid = data.get("id")
        if not eid:
            return jsonify({"error": "Missing id"}), 400
        fields = ["date","title","kind","job_id","start_time","end_time","note","color"]
        sets, vals = [], []
        for f in fields:
            if f in data:
                v = normalize_date(data[f]) if f == "date" else data[f]
                sets.append(f"{f}=?")
                vals.append(v)
        if not sets:
            return jsonify({"error": "No changes"}), 400
        vals.append(eid)
        db.execute("UPDATE calendar_events SET " + ",".join(sets) + " WHERE id=?", vals)
        db.commit()
        return jsonify({"ok": True})

    if request.method == "DELETE":
        eid = request.args.get("id") or data.get("id")
        if not eid:
            return jsonify({"error": "Missing id"}), 400
        db.execute("DELETE FROM calendar_events WHERE id=?", (eid,))
        db.commit()
        return jsonify({"ok": True})

# Jednoduché timesheets API (kompatibilita se starým frontem)
@app.route("/gd/api/timesheets", methods=["GET","POST","DELETE"])
def api_timesheets():
    u, err = require_role(write=(request.method != "GET"))
    if err: return err
    db = get_db()

    if request.method == "GET":
        rows = db.execute("""
            SELECT * FROM timesheets ORDER BY date DESC, id DESC LIMIT 500
        """).fetchall()
        return jsonify([dict(r) for r in rows])

    data = request.get_json(force=True, silent=True) or {}

    if request.method == "POST":
        date_s = normalize_date(data.get("date"))
        hours = float(data.get("hours") or 0)
        job_id = data.get("job_id")
        note = (data.get("note") or "").strip()
        if not date_s:
            return jsonify({"error":"missing_date"}), 400
        now = datetime.utcnow().isoformat(timespec="seconds")
        db.execute("""
            INSERT INTO timesheets(user_id,date,hours,job_id,note,created_at)
            VALUES (?,?,?,?,?,?)
        """, (1, date_s, hours, job_id, note, now))
        db.commit()
        return jsonify({"ok": True})

    if request.method == "DELETE":
        tid = request.args.get("id") or data.get("id")
        if not tid:
            return jsonify({"error":"missing_id"}), 400
        db.execute("DELETE FROM timesheets WHERE id=?", (tid,))
        db.commit()
        return jsonify({"ok": True})

# --------------------------------------------------------------------------------------
# UI stránky
# --------------------------------------------------------------------------------------
@app.route("/")
def index():
    # pokud existuje index.html v templates, renderujeme, jinak aspoň něco
    try:
        return render_template("index.html", title="green david app")
    except Exception:
        return "<!doctype html><title>green david app</title><h1>green david app</h1>", 200

@app.route("/calendar")
def page_calendar():
    return render_template("calendar.html", title="Kalendář")

@app.route("/timesheets")
def page_timesheets():
    return render_template("timesheets.html", title="Výkazy")

# --------------------------------------------------------------------------------------
# Statické soubory (zůstávají přes static_folder=".")
# --------------------------------------------------------------------------------------
@app.route("/uploads/<path:fn>")
def uploads(fn):
    return send_from_directory(UPLOAD_DIR, fn)

# --------------------------------------------------------------------------------------
# Spuštění (pro lokální debug)
# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
