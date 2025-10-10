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
    db.execute(
        "CREATE TABLE IF NOT EXISTS users("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "email TEXT UNIQUE NOT NULL,"
        "name TEXT NOT NULL,"
        "role TEXT NOT NULL,"
        "password_hash TEXT NOT NULL,"
        "active INTEGER NOT NULL DEFAULT 1,"
        "created_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )
    cols = {r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()}
    if "created_at" not in cols:
        db.execute("ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))")

def ensure_jobs_schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS jobs("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "title TEXT,"
        "name TEXT,"
        "client TEXT NOT NULL DEFAULT '',"
        "status TEXT NOT NULL DEFAULT 'Plán',"
        "city TEXT NOT NULL DEFAULT '',"
        "code TEXT NOT NULL DEFAULT '',"
        "date TEXT NOT NULL DEFAULT '',"
        "note TEXT"
        ")"
    )
    cols = {r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
    if "title" not in cols:
        db.execute("ALTER TABLE jobs ADD COLUMN title TEXT")
    try:
        db.execute("UPDATE jobs SET title = COALESCE(title, name) WHERE (title IS NULL OR title='') AND name IS NOT NULL")
    except Exception:
        pass
    cols = {r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
    if "owner_id" not in cols:
        admin_id = get_admin_id(db)
        db.execute(f"ALTER TABLE jobs ADD COLUMN owner_id INTEGER NOT NULL DEFAULT {admin_id}")
    else:
        admin_id = get_admin_id(db)
        try:
            db.execute("UPDATE jobs SET owner_id=? WHERE owner_id IS NULL OR owner_id=0", (admin_id,))
        except Exception:
            pass
    cols = {r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
    if "created_at" not in cols:
        db.execute("ALTER TABLE jobs ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))")
    else:
        try:
            db.execute("UPDATE jobs SET created_at = COALESCE(created_at, datetime('now')) WHERE created_at IS NULL OR created_at=''")
        except Exception:
            pass
    db.execute("UPDATE jobs SET title = '' WHERE title IS NULL")

def ensure_tasks_schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS tasks("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "title TEXT NOT NULL,"
        "job_id INTEGER,"
        "due_date TEXT NOT NULL,"
        "status TEXT NOT NULL DEFAULT 'Plán',"
        "note TEXT,"
        "owner_id INTEGER NOT NULL,"
        "created_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )

def ensure_notes_schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS notes("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "title TEXT NOT NULL,"
        "content TEXT,"
        "note_date TEXT NOT NULL,"
        "owner_id INTEGER NOT NULL,"
        "created_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )

def ensure_worklogs_schema(db):
    db.execute(
        "CREATE TABLE IF NOT EXISTS work_logs("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "user_id INTEGER NOT NULL,"
        "employee_name TEXT NOT NULL,"
        "job_id INTEGER,"
        "job_title TEXT,"
        "hours REAL NOT NULL,"
        "work_date TEXT NOT NULL,"
        "note TEXT,"
        "created_at TEXT NOT NULL DEFAULT (datetime('now'))"
        ")"
    )

@app.before_request
def ensure_db():
    if app.config.get("DB_INITED"):
        return
    if request.method == "HEAD":
        return
    db = get_db()
    ensure_users_schema(db)
    ensure_jobs_schema(db)
    ensure_tasks_schema(db)
    ensure_notes_schema(db)
    ensure_worklogs_schema(db)
    db.execute(
        "INSERT OR IGNORE INTO users(email,name,role,password_hash,active,created_at) VALUES (?,?,?,?,?,?)",
        ("admin@greendavid.local","Admin","admin", generate_password_hash("admin123"), 1,
         datetime.utcnow().isoformat(timespec="seconds"))
    )
    db.commit()
    app.config["DB_INITED"] = True

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/static/<path:p>")
def static_proxy(p):
    return send_from_directory("static", p)

@app.route("/health")
def health():
    return jsonify({"ok": True, "time": datetime.utcnow().isoformat()})

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
    return jsonify({"authenticated": True, "user": dict(u)})

@app.route("/api/jobs", methods=["GET","POST"])
def api_jobs():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY date(date) DESC, id DESC").fetchall()]
        return jsonify({"ok": True, "jobs": rows})
    data = request.get_json(silent=True) or {}
    for k in ("title","city","code","date"):
        if not (data.get(k) and str(data.get(k)).strip()):
            return jsonify({"ok": False, "error": "missing_fields", "field": k}), 400
    title = str(data["title"]).strip()
    city  = str(data["city"]).strip()
    code  = str(data["code"]).strip()
    datev = _normalize_date(str(data["date"]).strip())
    status = (data.get("status") or "Plán").strip()
    client = (data.get("client") or "").strip()
    note = (data.get("note") or None)
    uid = session.get("uid") or get_admin_id(db)

    cols = {r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
    need_name = ("name" in cols)
    has_created_at = ("created_at" in cols)
    if need_name and has_created_at:
        db.execute("INSERT INTO jobs(title, name, client, status, city, code, date, note, owner_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))",
                   (title, title, client, status, city, code, datev, note, uid))
    elif need_name and not has_created_at:
        db.execute("INSERT INTO jobs(title, name, client, status, city, code, date, note, owner_id) VALUES (?,?,?,?,?,?,?,?,?)",
                   (title, title, client, status, city, code, datev, note, uid))
    elif (not need_name) and has_created_at:
        db.execute("INSERT INTO jobs(title, client, status, city, code, date, note, owner_id, created_at) VALUES (?,?,?,?,?,?,?,?,datetime('now'))",
                   (title, client, status, city, code, datev, note, uid))
    else:
        db.execute("INSERT INTO jobs(title, client, status, city, code, date, note, owner_id) VALUES (?,?,?,?,?,?,?,?)",
                   (title, client, status, city, code, datev, note, uid))
    db.commit()
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
