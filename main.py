import os, re, io, sqlite3
from datetime import datetime, date, timedelta
from flask import Flask, send_from_directory, request, jsonify, session, g, send_file, abort, render_template
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------- utils -----------------
def _normalize_date(v):
    if not v:
        return v
    s = str(v).strip()
    import re as _re
    m = _re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, M, d = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    m = _re.match(r"^(\d{1,2})[\.\s-](\d{1,2})[\.\s-](\d{4})$", s)
    if m:
        d, M, y = m.groups()
        return f"{int(y):04d}-{int(M):02d}-{int(d):02d}"
    return s

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    db = get_db()
    row = db.execute("SELECT id,email,name,role,active FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None

def require_auth():
    u = current_user()
    if not u or not u.get("active"):
        return None, (jsonify({"ok": False, "error": "unauthorized"}), 401)
    return u, None

def require_role(write=False):
    u, err = require_auth()
    if err:
        return None, err
    if write and u["role"] not in ("admin","manager"):
        return None, (jsonify({"ok": False, "error": "forbidden"}), 403)
    return u, None

# ----------------- bootstrap (subset) -----------------
def ensure_schema():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','manager','worker')),
        password_hash TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'worker'
    );
    -- prefer new schema; legacy DBs may still have jobs.name (possibly NOT NULL)
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        name TEXT,
        client TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Plán',
        city TEXT NOT NULL DEFAULT '',
        code TEXT NOT NULL DEFAULT '',
        date TEXT,
        note TEXT
    );
    CREATE TABLE IF NOT EXISTS timesheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        hours REAL NOT NULL DEFAULT 0,
        place TEXT DEFAULT '',
        activity TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT NOT NULL,
        kind TEXT NOT NULL DEFAULT 'note',
        job_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        note TEXT DEFAULT '',
        color TEXT DEFAULT '#2e7d32'
    );
    """)
    db.commit()

def seed_admin():
    db = get_db()
    cur = db.execute("SELECT COUNT(*) c FROM users")
    if cur.fetchone()["c"] == 0:
        db.execute(
            "INSERT INTO users(email,name,role,password_hash,active,created_at) VALUES (?,?,?,?,1,?)",
            (
                os.environ.get("ADMIN_EMAIL","admin@greendavid.local"),
                os.environ.get("ADMIN_NAME","Admin"),
                "admin",
                generate_password_hash(os.environ.get("ADMIN_PASSWORD","admin123")),
                datetime.utcnow().isoformat()
            )
        )
        db.commit()

@app.before_request
def _ensure():
    ensure_schema()
    seed_admin()

# ----------------- helpers for jobs schema compat -----------------
def _jobs_info():
    rows = get_db().execute("PRAGMA table_info(jobs)").fetchall()
    # rows: cid, name, type, notnull, dflt_value, pk
    return {r[1]: {"notnull": int(r[3])} for r in rows}

def _job_title_col():
    info = _jobs_info()
    if "title" in info:
        return "title"
    return "name" if "name" in info else "title"

def _job_select_all():
    info = _jobs_info()
    if "title" in info:
        return "SELECT id, title, client, status, city, code, date, note FROM jobs"
    if "name" in info:
        return "SELECT id, name AS title, client, status, city, code, date, note FROM jobs"
    return "SELECT id, '' AS title, client, status, city, code, date, note FROM jobs"

def _job_insert_cols_and_vals(title, client, status, city, code, dt, note, owner_id=None):
    info = _jobs_info()
    cols = []
    vals = []
    # Keep legacy 'name' in sync if present
    if "title" in info:
        cols.append("title"); vals.append(title)
    if "name" in info:
        cols.append("name"); vals.append(title)
    cols += ["client","status","city","code","date","note"]
    vals += [client, status, city, code, dt, note]
    # legacy NOT NULL columns without defaults
    now = datetime.utcnow().isoformat()
    if "created_at" in info:
        cols.append("created_at"); vals.append(now)
    if "updated_at" in info:
        cols.append("updated_at"); vals.append(now)
    # legacy owner_id
    if "owner_id" in info:
        if owner_id is None:
            cu = current_user()
            owner_id = cu["id"] if cu else None
        cols.append("owner_id"); vals.append(int(owner_id) if owner_id is not None else None)
    return cols, vals

def _job_title_update_set(params_list, title_value):
    info = _jobs_info()
    sets = []
    if "title" in info:
        sets.append("title=?"); params_list.append(title_value)
    if "name" in info:
        sets.append("name=?"); params_list.append(title_value)
    return sets

# ----------------- static -----------------
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/uploads/<path:name>")
def uploaded_file(name):
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    path = os.path.join(UPLOAD_DIR, safe)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(UPLOAD_DIR, safe)

@app.route("/health")
def health():
    return {"status": "ok"}

# ----------------- APIs -----------------
@app.route("/api/me")
def api_me():
    u = current_user()
    return jsonify({"ok": True, "authenticated": bool(u), "user": u, "tasks_count": 0})

# auth
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(force=True, silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    db = get_db()
    row = db.execute("SELECT id,email,name,role,password_hash,active FROM users WHERE email=?", (email,)).fetchone()
    if not row or not check_password_hash(row["password_hash"], password) or not row["active"]:
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401
    session["uid"] = row["id"]
    return jsonify({"ok": True})

@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("uid", None)
    return jsonify({"ok": True})

# employees
@app.route("/api/employees", methods=["GET","POST","DELETE"])
def api_employees():
    u, err = require_role(write=(request.method!="GET"))
    if err: return err
    db = get_db()
        if request.method == "GET":
        role = request.args.get("role")
        if role:
            rows = db.execute("SELECT * FROM employees WHERE role=? ORDER BY id DESC", (role,)).fetchall()
        else:
            rows = db.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
        return jsonify({"ok": True, "employees":[dict(r) for r in rows]})
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        name = data.get("name"); role = data.get("role") or "worker"
        if not name: return jsonify({"ok": False, "error":"invalid_input"}), 400
        db.execute("INSERT INTO employees(name,role) VALUES (?,?)", (name, role))
        db.commit()
        return jsonify({"ok": True})
    if request.method == "DELETE":
        eid = request.args.get("id", type=int)
        if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
        db.execute("DELETE FROM employees WHERE id=?", (eid,))
        db.commit()
        return jsonify({"ok": True})

# ✅ jobs with legacy schema compatibility
@app.route("/api/jobs", methods=["GET","POST","PATCH","DELETE"])
def api_jobs():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute(_job_select_all() + " ORDER BY date(date) DESC, id DESC").fetchall()]
        for r in rows:
            if "date" in r and r["date"]:
                r["date"] = _normalize_date(r["date"])
        return jsonify({"ok": True, "jobs": rows})

    # write operations require manager/admin
    u, err = require_role(write=True)
    if err: return err

    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    client = (data.get("client") or "").strip()
    status = (data.get("status") or "Plán").strip()
    city   = (data.get("city")   or "").strip()
    code   = (data.get("code")   or "").strip()
    note   = data.get("note") or ""
    dt     = _normalize_date(data.get("date"))

    if request.method == "POST":
        req = [title, city, code, dt]
        if not all((v is not None and str(v).strip()!='') for v in req):
            return jsonify({"ok": False, "error":"missing_fields"}), 400
        cols, vals = _job_insert_cols_and_vals(title, client, status, city, code, dt, note, owner_id=u["id"])
        sql = "INSERT INTO jobs(" + ",".join(cols) + ") VALUES (" + ",".join(["?"]*len(vals)) + ")"
        db.execute(sql, vals)
        db.commit()
        return jsonify({"ok": True})

    if request.method == "PATCH":
        jid = data.get("id")
        if not jid: return jsonify({"ok": False, "error":"missing_id"}), 400
        updates = []; params = []
        if "title" in data and data["title"] is not None:
            updates += _job_title_update_set(params, title)
        for f in ("client","status","city","code","date","note"):
            if f in data:
                v = _normalize_date(data[f]) if f=="date" else data[f]
                updates.append(f"{f}=?"); params.append(v)
        # Touch legacy updated_at if present
        info = _jobs_info()
        if "updated_at" in info:
            updates.append("updated_at=?"); params.append(datetime.utcnow().isoformat())
        # Optional owner change if present
        if "owner_id" in info and data.get("owner_id") is not None:
            updates.append("owner_id=?"); params.append(int(data.get("owner_id")))
        if not updates: return jsonify({"ok": False, "error":"nothing_to_update"}), 400
        params.append(int(jid))
        db.execute("UPDATE jobs SET " + ", ".join(updates) + " WHERE id=?", params)
        db.commit()
        return jsonify({"ok": True})

    # DELETE
    jid = request.args.get("id", type=int)
    if not jid: return jsonify({"ok": False, "error":"missing_id"}), 400
    db.execute("DELETE FROM jobs WHERE id=?", (jid,))
    db.commit()
    return jsonify({"ok": True})

# timesheets CRUD + export
@app.route("/api/timesheets", methods=["GET","POST","PATCH","DELETE"])
def api_timesheets():
    u, err = require_role(write=(request.method!="GET"))
    if err: return err
    db = get_db()

    if request.method == "GET":
        emp = request.args.get("employee_id", type=int)
        jid = request.args.get("job_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to   = _normalize_date(request.args.get("to"))
        title_col = _job_title_col()
        q = f"""SELECT t.id,t.employee_id,t.job_id,t.date,t.hours,t.place,t.activity,
                      e.name AS employee_name, j.{title_col} AS job_title, j.code AS job_code
               FROM timesheets t
               LEFT JOIN employees e ON e.id=t.employee_id
               LEFT JOIN jobs j ON j.id=t.job_id"""
        conds=[]; params=[]
        if emp: conds.append("t.employee_id=?"); params.append(emp)
        if jid: conds.append("t.job_id=?"); params.append(jid)
        if d_from and d_to:
            conds.append("date(t.date) BETWEEN date(?) AND date(?)"); params.extend([d_from, d_to])
        elif d_from:
            conds.append("date(t.date) >= date(?)"); params.append(d_from)
        elif d_to:
            conds.append("date(t.date) <= date(?)"); params.append(d_to)
        if conds: q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY t.date ASC, t.id ASC"
        rows = db.execute(q, params).fetchall()
        return jsonify({"ok": True, "rows":[dict(r) for r in rows]})

    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        emp = data.get("employee_id"); job = data.get("job_id"); dt=data.get("date"); hours = data.get("hours")
        place = data.get("place") or ""; activity = data.get("activity") or ""
        if not all([emp,job,dt,(hours is not None)]): return jsonify({"ok": False, "error":"invalid_input"}), 400
        db.execute("INSERT INTO timesheets(employee_id,job_id,date,hours,place,activity) VALUES (?,?,?,?,?,?)",
                   (int(emp), int(job), _normalize_date(dt), float(hours), place, activity))
        db.commit()
        return jsonify({"ok": True})

    if request.method == "PATCH":
        data = request.get_json(force=True, silent=True) or {}
        tid = data.get("id")
        if not tid: return jsonify({"ok": False, "error":"missing_id"}), 400
        allowed = ["employee_id","job_id","date","hours","place","activity"]
        sets, vals = [], []
        for k in allowed:
            if k in data:
                v = _normalize_date(data[k]) if k=="date" else data[k]
                if k in ("employee_id","job_id"):
                    v = int(v)
                if k == "hours":
                    v = float(v)
                sets.append(f"{k}=?"); vals.append(v)
        if not sets:
            return jsonify({"ok": False, "error":"no_fields"}), 400
        vals.append(int(tid))
        db.execute("UPDATE timesheets SET "+",".join(sets)+" WHERE id=?", vals)
        db.commit()
        return jsonify({"ok": True})

    # DELETE
    tid = request.args.get("id", type=int)
    if not tid: return jsonify({"ok": False, "error":"missing_id"}), 400
    db.execute("DELETE FROM timesheets WHERE id=?", (tid,))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/timesheets/export")
def api_timesheets_export():
    u, err = require_role(write=False)
    if err: return err
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    jid = request.args.get("job_id", type=int)
    d_from = _normalize_date(request.args.get("from"))
    d_to   = _normalize_date(request.args.get("to"))
    title_col = _job_title_col()
    q = f"""SELECT t.id,t.date,t.hours,t.place,t.activity,
                  e.name AS employee_name, e.id AS employee_id,
                  j.{title_col} AS job_title, j.code AS job_code, j.id AS job_id
           FROM timesheets t
           LEFT JOIN employees e ON e.id=t.employee_id
           LEFT JOIN jobs j ON j.id=t.job_id"""
    conds=[]; params=[]
    if emp: conds.append("t.employee_id=?"); params.append(emp)
    if jid: conds.append("t.job_id=?"); params.append(jid)
    if d_from and d_to:
        conds.append("date(t.date) BETWEEN date(?) AND date(?)"); params.extend([d_from, d_to])
    elif d_from:
        conds.append("date(t.date) >= date(?)"); params.append(d_from)
    elif d_to:
        conds.append("date(t.date) <= date(?)"); params.append(d_to)
    if conds: q += " WHERE " + " AND ".join(conds)
    q += " ORDER BY t.date ASC, t.id ASC"
    rows = get_db().execute(q, params).fetchall()

    output = io.StringIO()
    import csv as _csv
    writer = _csv.writer(output)
    writer.writerow(["id","date","employee_id","employee_name","job_id","job_title","job_code","hours","place","activity"])
    for r in rows:
        writer.writerow([r["id"], r["date"], r["employee_id"], r["employee_name"] or "", r["job_id"], r["job_title"] or "", r["job_code"] or "", r["hours"], r["place"] or "", r["activity"] or ""])
    mem = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    mem.seek(0)
    fname = "timesheets.csv"
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=fname)

# ----------------- Template route -----------------
@app.route("/timesheets.html")
def page_timesheets():
    return render_template("timesheets.html")

# ----------------- run -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
