
import os, re, io, base64, sqlite3
from datetime import datetime, date
from flask import Flask, request, jsonify, session, g, send_file, send_from_directory, abort
from werkzeug.security import generate_password_hash, check_password_hash
from openpyxl import Workbook

DB_PATH = os.environ.get("DB_PATH", "app.db")
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _normalize_date(v):
    if not v: return v
    import re
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
    db = get_db()
    c = db.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS app_meta (k TEXT PRIMARY KEY, v TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, role TEXT NOT NULL, password_hash TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1)")
    c.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, client TEXT NOT NULL, status TEXT NOT NULL, city TEXT NOT NULL, code TEXT NOT NULL, date TEXT NOT NULL, note TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, due_date TEXT, employee_id INTEGER, job_id INTEGER, status TEXT NOT NULL DEFAULT 'nový')")
    c.execute("CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS timesheets (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id INTEGER, job_id INTEGER, date TEXT NOT NULL, hours REAL NOT NULL, place TEXT, activity TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY AUTOINCREMENT, site TEXT NOT NULL, category TEXT NOT NULL, name TEXT NOT NULL, qty REAL NOT NULL, unit TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS job_materials (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL, name TEXT NOT NULL, qty REAL NOT NULL, unit TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS job_tools (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL, name TEXT NOT NULL, qty REAL NOT NULL, unit TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS job_photos (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL, filename TEXT NOT NULL, created_at TEXT NOT NULL)")
    c.execute("CREATE TABLE IF NOT EXISTS job_assignments (job_id INTEGER NOT NULL, employee_id INTEGER NOT NULL, PRIMARY KEY (job_id, employee_id))")
    if not c.execute("SELECT 1 FROM users WHERE email=?", ("admin@greendavid.local",)).fetchone():
        c.execute("INSERT INTO users(email,name,role,password_hash,active) VALUES (?,?,?,?,1)", ("admin@greendavid.local","Admin","admin", generate_password_hash("admin123")))
    db.commit()

@app.before_request
def ensure_init():
    init_db()

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/uploads/<path:fn>")
def uploads(fn):
    return send_from_directory(UPLOAD_DIR, fn)

@app.route("/api/me")
def api_me():
    uid = session.get("uid")
    if not uid:
        return jsonify({"authenticated": False})
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

@app.route("/api/jobs")
def jobs_list():
    require_auth()
    db = get_db()
    rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY date DESC, id DESC").fetchall()]
    return jsonify({"jobs": rows})

@app.route("/api/jobs", methods=["POST","DELETE"])
def jobs_mut():
    require_auth()
    db = get_db()
    if request.method=="DELETE":
        jid = int(request.args.get("id", 0)) or 0
        db.execute("DELETE FROM jobs WHERE id=?", (jid,))
        db.execute("DELETE FROM job_materials WHERE job_id=?", (jid,))
        db.execute("DELETE FROM job_tools WHERE job_id=?", (jid,))
        db.execute("DELETE FROM job_photos WHERE job_id=?", (jid,))
        db.execute("DELETE FROM job_assignments WHERE job_id=?", (jid,))
        db.commit()
        return jsonify({"ok": True})
    data = request.get_json(force=True, silent=True) or {}
    for k in ["title","client","status","city","code","date"]:
        if not data.get(k): return jsonify({"error":"invalid_input","field":k}), 400
    data["date"] = _normalize_date(data.get("date"))
    db.execute("INSERT INTO jobs(title,client,status,city,code,date,note) VALUES (?,?,?,?,?,?,?)", (data["title"], data["client"], data["status"], data["city"], data["code"], data["date"], data.get("note") or ""))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/jobs/<int:jid>")
def job_detail(jid):
    require_auth()
    db = get_db()
    j = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    if not j: return jsonify({"error":"not_found"}), 404
    mats = [dict(r) for r in db.execute("SELECT * FROM job_materials WHERE job_id=? ORDER BY id DESC",(jid,)).fetchall()]
    tools = [dict(r) for r in db.execute("SELECT * FROM job_tools WHERE job_id=? ORDER BY id DESC",(jid,)).fetchall()]
    photos = [dict(r) for r in db.execute("SELECT * FROM job_photos WHERE job_id=? ORDER BY id DESC",(jid,)).fetchall()]
    assigns = [r["employee_id"] for r in db.execute("SELECT employee_id FROM job_assignments WHERE job_id=?",(jid,)).fetchall()]
    return jsonify({"job": dict(j), "materials": mats, "tools": tools, "photos": photos, "assignments": assigns})

@app.route("/api/jobs/<int:jid>/materials", methods=["POST","DELETE"])
def job_materials(jid):
    require_auth()
    db = get_db()
    if request.method=="DELETE":
        rid = int(request.args.get("id",0))
        db.execute("DELETE FROM job_materials WHERE id=? AND job_id=?", (rid,jid)); db.commit()
        return jsonify({"ok": True})
    data = request.get_json(force=True, silent=True) or {}
    db.execute("INSERT INTO job_materials(job_id,name,qty,unit) VALUES (?,?,?,?)", (jid, data.get("name",""), float(data.get("qty",0)), data.get("unit","ks")))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/jobs/<int:jid>/tools", methods=["POST","DELETE"])
def job_tools(jid):
    require_auth()
    db = get_db()
    if request.method=="DELETE":
        rid = int(request.args.get("id",0))
        db.execute("DELETE FROM job_tools WHERE id=? AND job_id=?", (rid,jid)); db.commit()
        return jsonify({"ok": True})
    data = request.get_json(force=True, silent=True) or {}
    db.execute("INSERT INTO job_tools(job_id,name,qty,unit) VALUES (?,?,?,?)", (jid, data.get("name",""), float(data.get("qty",0)), data.get("unit","ks")))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/jobs/<int:jid>/assignments", methods=["POST"])
def job_assignments(jid):
    require_auth()
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    ids = list({int(x) for x in (data.get("employee_ids") or [])})
    db.execute("DELETE FROM job_assignments WHERE job_id=?", (jid,))
    for eid in ids:
        db.execute("INSERT OR IGNORE INTO job_assignments(job_id,employee_id) VALUES (?,?)", (jid, eid))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/jobs/<int:jid>/photos", methods=["POST"])
def job_photos(jid):
    require_auth()
    db = get_db()
    data = request.get_json(force=True, silent=True) or {}
    data_url = data.get("data_url") or ""
    m = re.match(r"^data:image/(png|jpeg);base64,(.+)$", data_url)
    if not m: return jsonify({"error":"invalid_image"}), 400
    ext = "jpg" if m.group(1)=="jpeg" else "png"
    raw = base64.b64decode(m.group(2))
    fn = f"job-{jid}-{int(datetime.now().timestamp())}.{ext}"
    with open(os.path.join(UPLOAD_DIR, fn), "wb") as f: f.write(raw)
    db.execute("INSERT INTO job_photos(job_id,filename,created_at) VALUES (?,?,?)", (jid, fn, datetime.now().isoformat()))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/employees", methods=["GET","POST","DELETE"])
def employees():
    require_auth()
    db = get_db()
    if request.method=="GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()]
        return jsonify({"employees": rows})
    if request.method=="DELETE":
        rid = int(request.args.get("id",0)); db.execute("DELETE FROM employees WHERE id=?", (rid,)); db.commit(); return jsonify({"ok":True})
    data = request.get_json(force=True, silent=True) or {}
    db.execute("INSERT INTO employees(name,role) VALUES (?,?)", (data.get("name",""), data.get("role","Zahradník"))); db.commit(); return jsonify({"ok":True})

@app.route("/api/tasks", methods=["GET","POST","PATCH","DELETE"])
def tasks():
    require_auth()
    db = get_db()
    if request.method=="GET":
        job_id = request.args.get("job_id")
        if job_id:
            rows = [dict(r) for r in db.execute("SELECT * FROM tasks WHERE job_id=? ORDER BY id DESC", (job_id,)).fetchall()]
        else:
            rows = [dict(r) for r in db.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()]
        return jsonify({"tasks": rows})
    if request.method=="DELETE":
        rid = int(request.args.get("id",0)); db.execute("DELETE FROM tasks WHERE id=?", (rid,)); db.commit(); return jsonify({"ok":True})
    if request.method=="PATCH":
        data = request.get_json(force=True, silent=True) or {}
        db.execute("UPDATE tasks SET status=? WHERE id=?", (data.get("status","nový"), int(data.get("id",0)))); db.commit(); return jsonify({"ok":True})
    data = request.get_json(force=True, silent=True) or {}
    due = _normalize_date(data.get("due_date"))
    db.execute("INSERT INTO tasks(title,description,due_date,employee_id,job_id,status) VALUES (?,?,?,?,?,?)", (data.get("title",""), data.get("description",""), due, data.get("employee_id"), data.get("job_id"), data.get("status") or "nový"))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/timesheets", methods=["GET","POST","DELETE"])
def timesheets():
    require_auth()
    db = get_db()
    if request.method=="GET":
        job_id = request.args.get("job_id")
        emp_id = request.args.get("employee_id")
        sql = "SELECT t.*, e.name as employee_name, j.title as job_title FROM timesheets t LEFT JOIN employees e ON e.id=t.employee_id LEFT JOIN jobs j ON j.id=t.job_id"
        cond=[]; args=[]
        if job_id: cond.append("t.job_id=?"); args.append(job_id)
        if emp_id: cond.append("t.employee_id=?"); args.append(emp_id)
        if cond: sql += " WHERE " + " AND ".join(cond)
        sql += " ORDER BY t.date DESC, t.id DESC"
        rows = [dict(r) for r in db.execute(sql, args).fetchall()]
        return jsonify({"rows": rows})
    if request.method=="DELETE":
        rid=int(request.args.get("id",0)); db.execute("DELETE FROM timesheets WHERE id=?", (rid,)); db.commit(); return jsonify({"ok":True})
    data = request.get_json(force=True, silent=True) or {}
    db.execute("INSERT INTO timesheets(employee_id,job_id,date,hours,place,activity) VALUES (?,?,?,?,?,?)", (data.get("employee_id"), data.get("job_id"), _normalize_date(data.get("date")), float(data.get("hours",0)), data.get("place"), data.get("activity")))
    db.commit(); return jsonify({"ok":True})

@app.route("/api/items", methods=["GET","POST","DELETE"])
def items():
    require_auth()
    db = get_db()
    if request.method=="GET":
        site = request.args.get("site") or "lipnik"
        rows = [dict(r) for r in db.execute("SELECT * FROM items WHERE site=? ORDER BY id DESC", (site,)).fetchall()]
        return jsonify({"items": rows})
    if request.method=="DELETE":
        rid = int(request.args.get("id",0)); db.execute("DELETE FROM items WHERE id=?", (rid,)); db.commit(); return jsonify({"ok":True})
    data = request.get_json(force=True, silent=True) or {}
    db.execute("INSERT INTO items(site,category,name,qty,unit) VALUES (?,?,?,?,?)", (data.get("site","lipnik"), data.get("category","materiál zahrada"), data.get("name",""), float(data.get("qty",0)), data.get("unit","ks"))); db.commit(); return jsonify({"ok":True})

@app.route("/export/job_materials.xlsx")
def export_job_materials():
    require_auth()
    jid = int(request.args.get("job_id",0))
    db = get_db()
    mats = db.execute("SELECT name,qty,unit FROM job_materials WHERE job_id=? ORDER BY id",(jid,)).fetchall()
    wb = Workbook(); ws = wb.active; ws.title="Materiál"; ws.append(["Název","Množství","Jedn."])
    for r in mats: ws.append([r["name"], r["qty"], r["unit"]])
    path = os.path.join(UPLOAD_DIR, f"job_{jid}_materials.xlsx"); wb.save(path)
    return send_file(path, as_attachment=True)

@app.route("/export/employee_hours.xlsx")
def export_employee_hours():
    require_auth()
    eid = int(request.args.get("employee_id",0))
    db = get_db()
    rows = db.execute("SELECT date,hours,place,activity FROM timesheets WHERE employee_id=? ORDER BY date DESC",(eid,)).fetchall()
    wb = Workbook(); ws=wb.active; ws.title="Hodiny"; ws.append(["Datum","Hodiny","Místo","Popis"])
    for r in rows: ws.append([r["date"], r["hours"], r["place"], r["activity"]])
    path = os.path.join(UPLOAD_DIR, f"employee_{eid}_hours.xlsx"); wb.save(path)
    return send_file(path, as_attachment=True)

@app.route("/export/warehouse.xlsx")
def export_warehouse():
    require_auth()
    db = get_db()
    wb = Workbook()
    for site in ["lipnik","praha"]:
        ws = wb.create_sheet(title=site)
        ws.append(["Kategorie","Název","Množství","Jedn."])
        for r in db.execute("SELECT category,name,qty,unit FROM items WHERE site=? ORDER BY id DESC",(site,)).fetchall():
            ws.append([r["category"],r["name"],r["qty"],r["unit"]])
    if "Sheet" in wb.sheetnames and wb["Sheet"].max_row==1:
        wb.remove(wb["Sheet"])
    path = os.path.join(UPLOAD_DIR, "warehouse.xlsx"); wb.save(path)
    return send_file(path, as_attachment=True)

from flask import jsonify, request
@app.route("/api/health")
def api_health():
    try:
        db = get_db()
        db.execute("SELECT 1")
        return jsonify({"ok": True, "db": "ok"})
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500

@app.errorhandler(Exception)
def json_error(e):
    p = request.path or ""
    if p.startswith("/api/") or p.startswith("/export/"):
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500
    raise e

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
