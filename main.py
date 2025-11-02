import os, re, io, sqlite3
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify, session, g, send_file, abort, render_template, make_response
from jinja2 import TemplateNotFound

DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---- compatibility shim for older modules (e.g., gd_calendar_hotfix) ----
from functools import wraps
def require_role(*roles):
    """No-op role decorator to keep legacy imports working.
    Keeps API otevřená (bez přihlášení), ale umožní importy z gd_calendar_hotfix.py.
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # TODO: add real checks if/when auth is enabled
            return fn(*args, **kwargs)
        return wrapper
    return deco

TEMPLATE_MARKER = "<!-- GD_V2 -->"

def _no_store(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp

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

# ----------------- bootstrap (subset) -----------------
def ensure_schema():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        name TEXT,
        role TEXT DEFAULT 'admin',
        password_hash TEXT,
        active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'worker'
    );
    -- jobs table may be legacy; do not enforce new columns strictly
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
    """ )
    db.commit()

def migrate_legacy_defaults():
    """Backfill values if legacy columns exist, to avoid NOT NULL errors."""
    db = get_db()
    info = {r[1]: r for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
    now = datetime.utcnow().isoformat()
    if "created_at" in info:
        db.execute("UPDATE jobs SET created_at=? WHERE created_at IS NULL OR created_at=''", (now,))
    if "updated_at" in info:
        db.execute("UPDATE jobs SET updated_at=? WHERE updated_at IS NULL OR updated_at=''", (now,))
    if "owner_id" in info:
        admin = db.execute("SELECT id FROM users WHERE active=1 ORDER BY id ASC").fetchone()
        owner = admin["id"] if admin else 1
        db.execute("UPDATE jobs SET owner_id=? WHERE owner_id IS NULL OR CAST(owner_id AS TEXT)=''", (owner,))
    db.commit()

@app.before_request
def _ensure():
    ensure_schema()
    migrate_legacy_defaults()

# ----------------- static & pages -----------------
@app.route("/")
def index():
    # prefer repo's index.html if exists, otherwise ship fallback
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    html = """<!doctype html><html lang='cs'><head>
<meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>green david app</title>
<link rel='stylesheet' href='/style.css'>
</head><body>
<div class='page-pad'>
  <div class='tabs sticky'>
    <a class='active' href='/'>Domů</a>
    <a href='/calendar'>Kalendář</a>
    <a href='/timesheets.html'>Výkazy hodin</a>
    <a href='/jobs'>Zakázky</a>
    <a href='/employees'>Zaměstnanci</a>
    <a href='/brigadnici.html'>Brigádníci</a>
  </div>
  <div class='card card-dark'><div class='card-h'><strong>green david app</strong></div>
  <div class='card-c'>Nasazeno. Pokračuj přes navigaci výše.</div></div>
</div>
</body></html>"""
    return _no_store(make_response(html))

@app.route("/calendar")
def page_calendar():
    if os.path.exists("calendar.html"):
        return send_from_directory(".", "calendar.html")
    return index()

@app.route("/calendar.html")
def page_calendar_html():
    if os.path.exists("calendar.html"):
        return send_from_directory(".", "calendar.html")
    return index()

@app.route("/uploads/<path:name>")
def uploaded_file(name):
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    path = os.path.join(UPLOAD_DIR, safe)
    if not os.path.isfile(path):
        abort(404)
    return send_from_directory(UPLOAD_DIR, safe)

# ----- Fallback renderers (plain strings – no f-strings) -----
_EMPLOYEES_FALLBACK = """<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>green david app — Zaměstnanci</title>
<link rel="stylesheet" href="/style.css">
<meta name="viewport" content="width=device-width, initial-scale=1"><!-- GD_V2 -->
</head>
<body>
<div class="page-pad">
  <div class="tabs sticky">
    <a href="/calendar">Kalendář</a>
    <a href="/timesheets.html">Výkazy hodin</a>
    <a href="/jobs">Zakázky</a>
    <a href="/tasks">Úkoly</a>
    <a class="active" href="/employees">Zaměstnanci</a>
    <a href="/brigadnici.html">Brigádníci</a>
    <a href="/stock">Sklad</a>
    <a href="/users">Uživatelé</a>
  </div>

  <div class="card card-dark">
    <div class="card-h"><strong>Nový zaměstnanec</strong></div>
    <div class="card-c">
      <div class="row">
        <input id="newName" type="text" placeholder="Jméno" class="inp" />
        <select id="newRole" class="inp sel">
          <option value="zahradník">Zahradník</option>
          <option value="svářeč">Svářeč</option>
          <option value="brigádník">Brigádník</option>
          <option value="jiné">Jiné</option>
        </select>
        <button id="btnAdd" class="btn btn-primary">Přidat</button>
      </div>
    </div>
  </div>

  <div class="card card-dark">
    <div class="card-h">
      <strong>Seznam</strong>
      <div class="chips" style="margin-top:8px;">
        <button data-scope="all" class="chip chip-on">Všichni</button>
        <button data-scope="employees" class="chip">Zaměstnanci</button>
        <button data-scope="brig" class="chip">Brigádníci</button>
      </div>
    </div>
    <div class="card-c">
      <table class="tbl">
        <thead>
          <tr><th>Č.</th><th>Jméno</th><th>Role</th><th style="width:220px"></th></tr>
        </thead>
        <tbody id="listBody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
(async function(){
  const listBody = document.getElementById('listBody');
  const newName = document.getElementById('newName');
  const newRole = document.getElementById('newRole');
  const btnAdd = document.getElementById('btnAdd');
  const chips = Array.from(document.querySelectorAll('.chips .chip'));
  let scope = 'all';

  async function fetchJSON(url){ const r = await fetch(url); if(!r.ok) throw new Error(await r.text()); return r.json(); }
  async function apiJSON(url, options){
    const r = await fetch(url, Object.assign({headers:{'Content-Type':'application/json'}}, options||{}));
    if(!r.ok) throw new Error(await r.text());
    return r.json();
  }

  btnAdd.addEventListener('click', async ()=>{
    const name = newName.value.trim();
    const role = newRole.value;
    if(!name) return;
    await apiJSON('/api/employees', { method:'POST', body: JSON.stringify({ name, role }) });
    newName.value=''; await render();
  });

  chips.forEach(chip => chip.addEventListener('click', ()=>{
    chips.forEach(c=>c.classList.remove('chip-on'));
    chip.classList.add('chip-on');
    scope = chip.getAttribute('data-scope');
    render();
  }));

  async function render(){
    listBody.innerHTML = '<tr><td colspan="4" class="muted">Načítám…</td></tr>';
    const data = await fetchJSON('/api/employees' + (scope!=='all' ? ('?scope='+encodeURIComponent(scope)) : ''));
    const rows = data.employees || [];
    if(rows.length===0){
      listBody.innerHTML = '<tr><td colspan="4" class="muted">Žádné položky</td></tr>';
      return;
    }
    listBody.innerHTML = '';
    let i = 0;
    for(const e of rows){
      i += 1;
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${i}</td><td>${e.name}</td><td>${e.role||''}</td>
                      <td><a class="btn btn-small">Detail</a> <a class="btn btn-small btn-danger">Smazat</a></td>`;
      listBody.appendChild(tr);
    }
  }
  await render();
})();
</script>
</body>
</html>"""

_BRIGADNICI_FALLBACK = """<!doctype html>
<html lang="cs">
<head>
<meta charset="utf-8">
<title>green david app — Brigádníci</title>
<link rel="stylesheet" href="/style.css">
<meta name="viewport" content="width=device-width, initial-scale=1"><!-- GD_V2 -->
</head>
<body>
<div class="page-pad">
  <div class="tabs sticky">
    <a href="/calendar">Kalendář</a>
    <a href="/timesheets.html">Výkazy hodin</a>
    <a href="/jobs">Zakázky</a>
    <a href="/tasks">Úkoly</a>
    <a href="/employees">Zaměstnanci</a>
    <a class="active" href="/brigadnici.html">Brigádníci</a>
    <a href="/stock">Sklad</a>
    <a href="/users">Uživatelé</a>
  </div>

  <div class="card card-dark">
    <div class="card-h"><strong>Nový brigádník</strong></div>
    <div class="card-c">
      <div class="row">
        <input id="newName" type="text" placeholder="Jméno" class="inp"/>
        <button id="btnAdd" class="btn btn-primary">Přidat</button>
      </div>
    </div>
  </div>

  <div class="card card-dark">
    <div class="card-h"><strong>Seznam</strong></div>
    <div class="card-c">
      <table class="tbl">
        <thead><tr><th>Č.</th><th>Jméno</th><th>Role</th></tr></thead>
        <tbody id="listBody"></tbody>
      </table>
    </div>
  </div>
</div>

<script>
(async function(){
  const listBody = document.getElementById('listBody');
  const newName = document.getElementById('newName');
  const btnAdd = document.getElementById('btnAdd');

  async function fetchJSON(url){ const r = await fetch(url); if(!r.ok) throw new Error(await r.text()); return r.json(); }
  async function apiJSON(url, options){
    const r = await fetch(url, Object.assign({headers:{'Content-Type':'application/json'}}, options||{}));
    if(!r.ok) throw new Error(await r.text());
    return r.json();
  }

  btnAdd.addEventListener('click', async ()=>{
    const name = newName.value.trim();
    if(!name) return;
    await apiJSON('/api/employees', { method:'POST', body: JSON.stringify({ name, role: 'brigádník' }) });
    newName.value=''; await render();
  });

  async function render(){
    listBody.innerHTML = '<tr><td colspan="3" class="muted">Načítám…</td></tr>';
    const data = await fetchJSON('/api/employees?scope=brig');
    const rows = data.employees || [];
    if(rows.length===0){
      listBody.innerHTML = '<tr><td colspan="3" class="muted">Žádní brigádníci</td></tr>';
      return;
    }
    listBody.innerHTML = '';
    let i = 0;
    for(const e of rows){
      i += 1;
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${i}</td><td>${e.name}</td><td>${e.role||'brigádník'}</td>`;
      listBody.appendChild(tr);
    }
  }
  await render();
})();
</script>
</body>
</html>"""

def _render_or_fallback(tpl_name, fallback_html):
    try:
        html = render_template(tpl_name)
        if TEMPLATE_MARKER in html:
            return _no_store(make_response(html))
        # template rendered but without marker -> it's old; return fallback
    except TemplateNotFound:
        pass
    return _no_store(make_response(fallback_html))

@app.route("/employees")
def page_employees():
    return _render_or_fallback("employees.html", _EMPLOYEES_FALLBACK)

@app.route("/brigadnici.html")
def page_brigadnici():
    return _render_or_fallback("brigadnici.html", _BRIGADNICI_FALLBACK)

@app.route("/timesheets.html")
def page_timesheets():
    try:
        return render_template("timesheets.html")
    except TemplateNotFound:
        return index()

# ----------------- APIs -----------------
@app.route("/api/me")
def api_me():
    return jsonify({"ok": True, "authenticated": False, "user": None, "tasks_count": 0})

# employees (OPEN – no auth to match legacy behavior)
@app.route("/api/employees", methods=["GET","POST","DELETE"])
def api_employees():
    db = get_db()
    if request.method == "GET":
        scope = (request.args.get("scope") or "").lower().strip()
        rows = db.execute("SELECT * FROM employees ORDER BY id DESC").fetchall()
        items = [dict(r) for r in rows]
        if scope == "brig":
            items = [e for e in items if "brig" in str(e.get("role","")).lower()]
        elif scope == "employees":
            items = [e for e in items if "brig" not in str(e.get("role","")).lower()]
        return jsonify({"ok": True, "employees": items})
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        name = (data.get("name") or "").strip()
        role = (data.get("role") or "worker").strip()
        if not name:
            return jsonify({"ok": False, "error":"invalid_input"}), 400
        db.execute("INSERT INTO employees(name,role) VALUES (?,?)", (name, role))
        db.commit()
        return jsonify({"ok": True})
    # DELETE
    eid = request.args.get("id", type=int)
    if not eid: return jsonify({"ok": False, "error":"missing_id"}), 400
    db.execute("DELETE FROM employees WHERE id=?", (eid,))
    db.commit()
    return jsonify({"ok": True})

# jobs (OPEN – legacy-compatible + default owner)
@app.route("/api/jobs", methods=["GET","POST","PATCH","DELETE"])
def api_jobs():
    db = get_db()

    def _jobs_info():
        rows = db.execute("PRAGMA table_info(jobs)").fetchall()
        return {r[1]: {"notnull": int(r[3])} for r in rows}

    def _job_title_col(info=None):
        info = info or _jobs_info()
        if "title" in info:
            return "title"
        return "name" if "name" in info else "title"

    def _job_select_all(info=None):
        info = info or _jobs_info()
        if "title" in info:
            return "SELECT id, title, client, status, city, code, date, note FROM jobs"
        if "name" in info:
            return "SELECT id, name AS title, client, status, city, code, date, note FROM jobs"
        return "SELECT id, '' AS title, client, status, city, code, date, note FROM jobs"

    if request.method == "GET":
        rows = [dict(r) for r in db.execute(_job_select_all() + " ORDER BY date(date) DESC, id DESC").fetchall()]
        for r in rows:
            if "date" in r and r["date"]:
                r["date"] = _normalize_date(r["date"])
        return jsonify({"ok": True, "jobs": rows})

    data = request.get_json(force=True, silent=True) or {}
    title = (data.get("title") or "").strip()
    client = (data.get("client") or "").strip()
    status = (data.get("status") or "Plán").strip()
    city   = (data.get("city")   or "").strip()
    code   = (data.get("code")   or "").strip()
    note   = data.get("note") or ""
    dt     = _normalize_date(data.get("date"))

    info = _jobs_info()

    if request.method == "POST":
        req = [title, city, code, dt]
        if not all((v is not None and str(v).strip()!='') for v in req):
            return jsonify({"ok": False, "error":"missing_fields"}), 400
        cols = []; vals = []
        if "title" in info: cols.append("title"); vals.append(title)
        if "name" in info:  cols.append("name");  vals.append(title)
        cols += ["client","status","city","code","date","note"]; vals += [client,status,city,code,dt,note]
        now = datetime.utcnow().isoformat()
        if "created_at" in info: cols.append("created_at"); vals.append(now)
        if "updated_at" in info: cols.append("updated_at"); vals.append(now)
        if "owner_id" in info:
            owner = db.execute("SELECT id FROM users WHERE active=1 ORDER BY id ASC").fetchone()
            cols.append("owner_id"); vals.append(owner["id"] if owner else 1)
        sql = "INSERT INTO jobs(" + ",".join(cols) + ") VALUES (" + ",".join(["?"]*len(vals)) + ")"
        db.execute(sql, vals)
        db.commit()
        return jsonify({"ok": True})

    if request.method == "PATCH":
        jid = data.get("id")
        if not jid: return jsonify({"ok": False, "error":"missing_id"}), 400
        updates = []; params = []
        if "title" in data and data["title"] is not None:
            if "title" in info: updates.append("title=?"); params.append(title)
            if "name" in info:  updates.append("name=?");  params.append(title)
        for f in ("client","status","city","code","date","note"):
            if f in data:
                v = _normalize_date(data[f]) if f=="date" else data[f]
                updates.append(f"{f}=?"); params.append(v)
        if "updated_at" in info:
            updates.append("updated_at=?"); params.append(datetime.utcnow().isoformat())
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

# timesheets (OPEN)
@app.route("/api/timesheets", methods=["GET","POST","PATCH","DELETE"])
def api_timesheets():
    db = get_db()

    if request.method == "GET":
        emp = request.args.get("employee_id", type=int)
        jid = request.args.get("job_id", type=int)
        d_from = _normalize_date(request.args.get("from"))
        d_to   = _normalize_date(request.args.get("to"))
        # detect title column
        info = {r[1]: r for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
        title_col = "title" if "title" in info else ("name" if "name" in info else "title")
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

# ----------------- run -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
