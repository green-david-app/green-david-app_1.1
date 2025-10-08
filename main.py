import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, session, g, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DB_PATH", "app.db")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_=None):
    db = g.pop("db", None)
    if db:
        db.close()

def init_db():
    db = get_db()
    c = db.cursor()

    # Defensive migration: ensure users.created_at exists when table already exists
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if cols and "created_at" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))")
            db.commit()
    except Exception:
        pass

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            note TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assigned_to INTEGER,
            job_id INTEGER,
            status TEXT NOT NULL DEFAULT 'nový'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            qty REAL NOT NULL,
            unit TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            ref_id INTEGER,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            meta TEXT
        )
    """)

    # Seed admin (idempotent) – 6 columns, 6 placeholders
    c.execute(
        "INSERT OR IGNORE INTO users(email, name, role, password_hash, active, created_at) VALUES (?,?,?,?,?,?)",
        ("admin@greendavid.local", "Admin", "admin", generate_password_hash("admin123"), 1, datetime.utcnow().isoformat(timespec="seconds"))
    )

    db.commit()

@app.before_request
def ensure_init():
    if request.method == "HEAD":
        return
    if not app.config.get("DB_INITED"):
        init_db()
        app.config["DB_INITED"] = True

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/static/<path:p>")
def static_proxy(p):
    return send_from_directory("static", p)

# -------- API --------
@app.route("/api/me")
def api_me():
    uid = session.get("uid")
    if not uid:
        return jsonify({"authenticated": False})
    db = get_db()
    u = db.execute("SELECT id,name,role,email FROM users WHERE id=?", (uid,)).fetchone()
    if not u:
        session.pop("uid", None)
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "user": {"id": u["id"], "name": u["name"], "role": u["role"], "email": u["email"]}})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    db = get_db()
    u = db.execute("SELECT id,email,name,role,password_hash,active FROM users WHERE email=?", (email,)).fetchone()
    if not u or not u["active"] or not check_password_hash(u["password_hash"], password):
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    session["uid"] = u["id"]
    return jsonify({"ok": True})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("uid", None)
    return jsonify({"ok": True})

@app.route("/api/jobs", methods=["GET"])
def api_jobs():
    db = get_db()
    rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY date DESC, id DESC").fetchall()]
    return jsonify({"jobs": rows})

@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    db = get_db()
    rows = [dict(r) for r in db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()]
    return jsonify({"tasks": rows})

@app.route("/api/items", methods=["GET"])
def api_items():
    db = get_db()
    rows = [dict(r) for r in db.execute("SELECT * FROM items ORDER BY name").fetchall()]
    return jsonify({"items": rows})

@app.route("/api/calendar", methods=["GET"])
def api_calendar():
    db = get_db()
    start = request.args.get("from")
    end = request.args.get("to")
    rows = [dict(r) for r in db.execute("SELECT * FROM calendar_events WHERE date BETWEEN ? AND ? ORDER BY date, id", (start, end)).fetchall()]
    return jsonify({"events": rows})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)