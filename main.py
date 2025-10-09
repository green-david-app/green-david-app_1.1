import os, sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, session, g, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY

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

def _normalize_date(v: str):
    if not v:
        return v
    s = str(v).strip()
    import re
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
    if m:
        d, M, y = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    return s

def get_admin_id(db):
    row = db.execute("SELECT id FROM users WHERE email=?", ("admin@greendavid.local",)).fetchone()
    return int(row["id"]) if row else 1

def ensure_users_schema(db):
    db.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    ''')

def ensure_jobs_schema(db):
    db.execute('''
        CREATE TABLE IF NOT EXISTS jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            name TEXT,
            client TEXT,
            status TEXT,
            city TEXT,
            code TEXT,
            date TEXT,
            note TEXT,
            owner_id INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

@app.before_request
def ensure_db():
    if app.config.get("DB_INITED"):
        return
    db = get_db()
    ensure_users_schema(db)
    ensure_jobs_schema(db)
    db.execute(
        "INSERT OR IGNORE INTO users(email,name,role,password_hash,active) VALUES (?,?,?,?,?)",
        ("admin@greendavid.local", "Admin", "admin", generate_password_hash("admin123"), 1)
    )
    db.commit()
    app.config["DB_INITED"] = True

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/jobs", methods=["GET", "POST"])
def api_jobs():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY date(date) DESC, id DESC").fetchall()]
        return jsonify({"ok": True, "jobs": rows})
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    city = data.get("city", "").strip()
    code = data.get("code", "").strip()
    datev = _normalize_date(data.get("date", "").strip())
    if not all([title, city, code, datev]):
        return jsonify({"ok": False, "error": "missing_fields"}), 400
    db.execute(
        "INSERT INTO jobs(title, name, client, status, city, code, date, note, owner_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))",
        (title, title, data.get("client",""), data.get("status","Plán"), city, code, datev, data.get("note",""), 1)
    )
    db.commit()
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)