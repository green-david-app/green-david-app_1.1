
import os, re, sqlite3
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, session, g, send_from_directory, abort, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from openpyxl import Workbook
from io import BytesIO

DB_PATH = os.environ.get("DB_PATH", "app.db")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _normalize_date(v):
    if not v: return v
    s = str(v)
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y,M,d = map(int, m.groups()); return f"{y:04d}-{M:02d}-{d:02d}"
    digits = re.sub(r"\D+", "", s)
    if len(digits)==8:
        yFirst = int(digits[:4])
        if 1900 <= yFirst <= 2100:
            y,M,d = yFirst, int(digits[4:6]), int(digits[6:8])
        else:
            d,M,y = int(digits[:2]), int(digits[2:4]), int(digits[4:8])
        return f"{y:04d}-{M:02d}-{d:02d}"
    m = re.match(r"^(\d{1,2})[.\s/_-](\d{1,2})[.\s/_-](\d{4})$", s)
    if m:
        d,M,y = map(int, m.groups()); return f"{y:04d}-{M:02d}-{d:02d}"
    return s

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(_=None):
    db = g.pop("db", None)
    if db: db.close()

def init_db():
    db = get_db(); c = db.cursor()
    # Defensive migration: ensure users.created_at exists with a default
    try:
        cols = [r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()]
        if 'created_at' not in cols:
            c.execute("ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))")
            db.commit()
    except Exception:
        pass
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT UNIQUE NOT NULL,name TEXT NOT NULL,role TEXT NOT NULL,password_hash TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL DEFAULT (datetime('now')))")
    c.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,role TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,client TEXT NOT NULL,status TEXT NOT NULL,city TEXT NOT NULL,code TEXT NOT NULL,date TEXT NOT NULL,note TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,description TEXT,due_date TEXT,employee_id INTEGER,job_id INTEGER,status TEXT NOT NULL DEFAULT 'nový')")
    c.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT,job_id INTEGER,task_id INTEGER,content TEXT NOT NULL,created_at TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT,site TEXT NOT NULL,category TEXT NOT NULL,name TEXT NOT NULL,qty REAL NOT NULL,unit TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS job_materials (id INTEGER PRIMARY KEY AUTOINCREMENT,job_id INTEGER NOT NULL,name TEXT NOT NULL,qty REAL NOT NULL,unit TEXT NOT NULL,created_at TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS job_assignments (job_id INTEGER NOT NULL,employee_id INTEGER NOT NULL,PRIMARY KEY (job_id, employee_id))")
    c.execute("CREATE TABLE IF NOT EXISTS calendar_events (id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,ref_id INTEGER,title TEXT NOT NULL,date TEXT NOT NULL,meta TEXT)")
    if not c.execute("SELECT 1 FROM users WHERE email=?", ("admin@greendavid.local",)).fetchone():
        c.execute("INSERT OR IGNORE INTO users(email,name,role,password_hash,active,created_at) VALUES (?,?,?,?,1)", ("admin@greendavid.local","Admin","admin", generate_password_hash("admin123"), 1, datetime.utcnow().isoformat(timespec="seconds")))
    db.commit()

@app.before_request
def ensure_init():
    init_db()

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/me")
def api_me():
    uid = session.get("uid")
    if not uid: return jsonify({"authenticated": False})
    db = get_db()
    u = db.execute("SELECT id,name,role FROM users WHERE id=?", (uid,)).fetchone()
    tasks_count = db.execute("SELECT COUNT(*) c FROM tasks WHERE status!='hotovo'").fetchone()["c"]
    return jsonify({"authenticated": True, "user": {"id":u["id"],"name":u["name"],"role":u["role"]}, "tasks_count": tasks_count})

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    db = get_db()
    u = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not u or not check_password_hash(u["password_hash"], password) or not u["active"]:
        return jsonify({"error":"invalid_credentials"}), 401
    session["uid"] = u["id"]
    return jsonify({"ok": True})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})

def require_auth():
    if not session.get("uid"):
        abort(401)

@app.route("/api/jobs", methods=["GET","POST","DELETE"])
def jobs():
    require_auth()
    db = get_db()
    if request.method=="GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY date DESC, id DESC").fetchall()]
        return jsonify({"jobs": rows})
    if request.method=="DELETE":
        jid = int(request.args.get("id", 0)) or 0
        for t in ["job_materials","job_assignments"]:
            db.execute(f"DELETE FROM {t} WHERE job_id=?", (jid,))
        db.execute("DELETE FROM jobs WHERE id=?", (jid,))
        db.execute("DELETE FROM calendar_events WHERE kind='job' AND ref_id=?", (jid,))
        db.commit(); return jsonify({"ok": True})
    data = request.get_json(force=True, silent=True) or {}
    for k in ["title","client","status","city","code","date"]:
        if not data.get(k): return jsonify({"error":"invalid_input","field":k}), 400
    data["date"] = _normalize_date(data.get("date"))
    db.execute("INSERT INTO jobs(title,client,status,city,code,date,note) VALUES (?,?,?,?,?,?,?)",
               (data["title"], data["client"], data["status"], data["city"], data["code"], data["date"], data.get("note") or ""))
    jid = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.execute("INSERT INTO calendar_events(kind,ref_id,title,date,meta) VALUES (?,?,?,?,NULL)",
               ("job", jid, f"Zakázka: {data['title']}", data["date"]))
    db.commit()
    return jsonify({"ok": True, "id": jid})

@app.route("/api/jobs/<int:jid>/deduct", methods=["POST"])
def job_deduct(jid):
    require_auth()
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    items = data.get("items") or []
    today = datetime.now().strftime("%Y-%m-%d")
    for it in items:
        iid = int(it.get("item_id")); qty = float(it.get("qty") or 0)
        row = db.execute("SELECT name,unit,qty FROM items WHERE id=?", (iid,)).fetchone()
        if not row: continue
        new_qty = float(row["qty"]) - qty
        if new_qty < 0: new_qty = 0.0
        db.execute("UPDATE items SET qty=? WHERE id=?", (new_qty, iid))
        db.execute("INSERT INTO job_materials(job_id,name,qty,unit,created_at) VALUES (?,?,?,?,?)",
                   (jid, row["name"], qty, row["unit"], today))
    db.execute("INSERT INTO calendar_events(kind,ref_id,title,date,meta) VALUES (?,?,?,?,NULL)",
               ("move", jid, f"Přesun materiálu na zakázku #{jid}", today))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/tasks", methods=["GET","POST","PATCH","DELETE"])
def tasks():
    require_auth()
    db = get_db()
    if request.method=="GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()]
        return jsonify({"tasks": rows})
    if request.method=="DELETE":
        rid = int(request.args.get("id",0))
        db.execute("DELETE FROM tasks WHERE id=?", (rid,))
        db.execute("DELETE FROM calendar_events WHERE kind='task' AND ref_id=?", (rid,))
        db.commit(); return jsonify({"ok":True})
    if request.method=="PATCH":
        data = request.get_json(force=True, silent=True) or {}
        db.execute("UPDATE tasks SET status=? WHERE id=?", (data.get("status","nový"), int(data.get("id",0))))
        db.commit(); return jsonify({"ok":True})
    data = request.get_json(force=True, silent=True) or {}
    due = _normalize_date(data.get("due_date"))
    db.execute("INSERT INTO tasks(title,description,due_date,employee_id,job_id,status) VALUES (?,?,?,?,?,?)",
               (data.get("title",""), data.get("description",""), due, data.get("employee_id"), data.get("job_id"), data.get("status") or "nový"))
    tid = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    if due:
        db.execute("INSERT INTO calendar_events(kind,ref_id,title,date,meta) VALUES (?,?,?,?,NULL)",
                   ("task", tid, f"Úkol: {data.get('title','')}", due))
    db.commit()
    return jsonify({"ok": True, "id": tid})

@app.route("/api/notes", methods=["GET","POST","DELETE"])
def notes():
    require_auth()
    db = get_db()
    if request.method=="GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()]
        return jsonify({"notes": rows})
    if request.method=="DELETE":
        rid = int(request.args.get("id",0))
        db.execute("DELETE FROM notes WHERE id=?", (rid,)); db.commit(); return jsonify({"ok":True})
    data = request.get_json(force=True, silent=True) or {}
    db.execute("INSERT INTO notes(job_id,task_id,content,created_at) VALUES (?,?,?,?)",
               (data.get("job_id"), data.get("task_id"), data.get("content",""), datetime.now().strftime("%Y-%m-%d")))
    db.commit(); return jsonify({"ok":True})

@app.route("/api/employees", methods=["GET","POST","DELETE"])
def employees():
    require_auth()
    db = get_db()
    if request.method=="GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()]
        return jsonify({"employees": rows})
    if request.method=="DELETE":
        rid = int(request.args.get("id",0))
        db.execute("DELETE FROM employees WHERE id=?", (rid,)); db.commit(); return jsonify({"ok":True})
    data = request.get_json(force=True, silent=True) or {}
    db.execute("INSERT INTO employees(name,role) VALUES (?,?)",
               (data.get("name",""), data.get("role","Zahradník"))); db.commit(); return jsonify({"ok":True})

@app.route("/api/items", methods=["GET","POST","DELETE"])
def items():
    require_auth()
    db = get_db()
    if request.method=="GET":
        site = request.args.get("site") or "lipnik"
        rows = [dict(r) for r in db.execute("SELECT * FROM items WHERE site=? ORDER BY id DESC", (site,)).fetchall()]
        return jsonify({"items": rows})
    if request.method=="DELETE":
        rid = int(request.args.get("id",0))
        db.execute("DELETE FROM items WHERE id=?", (rid,)); db.commit(); return jsonify({"ok":True})
    data = request.get_json(force=True, silent=True) or {}
    db.execute("INSERT INTO items(site,category,name,qty,unit) VALUES (?,?,?,?,?)",
               (data.get("site","lipnik"), data.get("category","materiál zahrada"), data.get("name",""), float(data.get("qty",0)), data.get("unit","ks")))
    db.commit(); return jsonify({"ok":True})

@app.route("/export/warehouse.xlsx")
def export_warehouse():
    require_auth()
    db = get_db()
    rows = db.execute("SELECT site,category,name,qty,unit FROM items ORDER BY site,category,name").fetchall()
    wb = Workbook(); ws = wb.active; ws.title = "Sklad"
    ws.append(["Pobočka","Kategorie","Název","Množství","Jednotka"])
    for r in rows: ws.append([r["site"], r["category"], r["name"], float(r["qty"]), r["unit"]])
    out = BytesIO(); wb.save(out); out.seek(0)
    return send_file(out, as_attachment=True, download_name="warehouse.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/api/calendar")
def calendar():
    require_auth()
    def norm(x): return _normalize_date(x) if x else x
    qfrom = norm(request.args.get("from"))
    qto = norm(request.args.get("to"))
    if not qfrom or not qto:
        today = date.today()
        start = date(today.year, today.month, 1) - timedelta(days=7)
        end = (date(today.year + (today.month//12), ((today.month%12)+1), 1) + timedelta(days=7))
        qfrom = start.isoformat(); qto = end.isoformat()
    db = get_db()
    rows = [dict(r) for r in db.execute("SELECT * FROM calendar_events WHERE date>=? AND date<? ORDER BY date", (qfrom, qto)).fetchall()]
    return jsonify({"events": rows})

@app.route("/api/health")
def api_health():
    try:
        db = get_db(); db.execute("SELECT 1")
        return jsonify({"ok": True, "db": "ok"})
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
