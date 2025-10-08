import os
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_from_directory

# ------------------------------------------------------------
# Konfigurace
# ------------------------------------------------------------
DB_PATH = os.environ.get("DB_PATH", "app.db")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Inicializace schématu + seed (bezpečné/idempotentní)
# ------------------------------------------------------------
def init_db():
    db = get_db()
    c = db.cursor()

    # Defenzivní migrace: pokud už tabulka users existuje bez created_at, přidej ho
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if cols and "created_at" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))")
            db.commit()
    except Exception:
        # OK, pokud tabulka ještě neexistuje, pokračujeme dál vytvořením
        pass

    # Schéma (pokud neexistuje)
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
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL
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
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
        CREATE TABLE IF NOT EXISTS job_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            qty REAL NOT NULL,
            unit TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS job_assignments (
            job_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            PRIMARY KEY (job_id, employee_id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,     -- např. 'job'
            ref_id INTEGER,         -- ID z jobs apod.
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            meta TEXT
        )
    """)

    # Seed admina – idempotentně, s created_at; 6 sloupců ↔ 6 hodnot
    c.execute("""
        INSERT OR IGNORE INTO users(email, name, role, password_hash, active, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "admin@greendavid.local",
        "Admin",
        "admin",
        generate_password_hash("admin123"),
        1,
        datetime.utcnow().isoformat(timespec="seconds")
    ))

    db.commit()

# ------------------------------------------------------------
# Inicializace jen jednou a ne při HEAD healthchecku
# ------------------------------------------------------------
@app.before_request
def ensure_init():
    # Render healthcheck často posílá HEAD – inicializaci přeskočíme
    if request.method == "HEAD":
        return
    if not app.config.get("DB_INITED"):
        init_db()
        app.config["DB_INITED"] = True

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.route("/")
def index():
    # Obslouží statický "index.html" v kořeni
    return app.send_static_file("index.html")

@app.route("/healthz")
def healthz():
    return jsonify({"ok": True, "time": datetime.utcnow().isoformat()})

# ---- Auth ----
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    db = get_db()
    row = db.execute("SELECT id, email, name, role, password_hash, active FROM users WHERE email=?", (email,)).fetchone()
    if not row or not row["active"] or not check_password_hash(row["password_hash"], password):
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401

    session["uid"] = row["id"]
    return jsonify({"ok": True, "user": {"id": row["id"], "email": row["email"], "name": row["name"], "role": row["role"]}})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("uid", None)
    return jsonify({"ok": True})

@app.route("/api/me")
def api_me():
    uid = session.get("uid")
    if not uid:
        return jsonify({"authenticated": False})
    db = get_db()
    u = db.execute("SELECT id, name, role, email FROM users WHERE id=?", (uid,)).fetchone()
    return jsonify({
        "authenticated": True,
        "user": {"id": u["id"], "name": u["name"], "role": u["role"], "email": u["email"]}
    })

# ---- Jobs (minimální skeleton, aby nepadalo na 404) ----
@app.route("/api/jobs", methods=["GET", "POST", "DELETE"])
def jobs():
    uid = session.get("uid")
    if not uid:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    db = get_db()

    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY date DESC, id DESC").fetchall()]
        return jsonify({"ok": True, "jobs": rows})

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        title = (data.get("title") or "").strip()
        code = (data.get("code") or "").strip()
        date_str = (data.get("date") or datetime.utcnow().date().isoformat())
        note = data.get("note")
        if not title or not code:
            return jsonify({"ok": False, "error": "missing_fields"}), 400
        db.execute("INSERT INTO jobs(title, code, date, note) VALUES (?,?,?,?)", (title, code, date_str, note))
        db.commit()
        return jsonify({"ok": True})

    if request.method == "DELETE":
        jid = int(request.args.get("id", 0)) or 0
        if not jid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        # kaskádové smazání provázaných záznamů
        db.execute("DELETE FROM job_materials WHERE job_id=?", (jid,))
        db.execute("DELETE FROM job_assignments WHERE job_id=?", (jid,))
        db.execute("DELETE FROM calendar_events WHERE kind='job' AND ref_id=?", (jid,))
        db.execute("DELETE FROM jobs WHERE id=?", (jid,))
        db.commit()
        return jsonify({"ok": True})

# ---- Statické (např. CSS, obrázky) – obvykle není nutné, Flask už obslouží přes static_folder ----
@app.route("/static/<path:path>")
def static_proxy(path):
    return send_from_directory("static", path)

# ------------------------------------------------------------
# Entrypoint pro Gunicorn: main:app
# ------------------------------------------------------------
if __name__ == "__main__":
    # Lokální běh (vývoj)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
