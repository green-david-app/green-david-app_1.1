
from flask import Flask, request, jsonify, make_response, Response
import sqlite3, os, csv, io
from datetime import datetime, timedelta

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "app.db")

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    PRAGMA journal_mode=WAL;

    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        client TEXT, status TEXT, city TEXT, code TEXT, date TEXT,
        note TEXT
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT, status TEXT, due_date TEXT,
        employee_id INTEGER, job_id INTEGER
    );

    CREATE TABLE IF NOT EXISTS timesheets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL, job_id INTEGER NOT NULL,
        date TEXT NOT NULL, hours REAL NOT NULL,
        place TEXT, activity TEXT
    );

    CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, start TEXT NOT NULL, end TEXT,
        all_day INTEGER NOT NULL DEFAULT 1,
        type TEXT NOT NULL DEFAULT 'note',  -- note|task|job
        ref_id INTEGER, notes TEXT
    );
    """)
    if not db.execute("SELECT 1 FROM employees LIMIT 1").fetchone():
        db.executemany("INSERT INTO employees(name,email,phone) VALUES (?,?,?)",
                       [("Pepa","pepa@greendavid.local",""),("Míša","misa@greendavid.local",""),("Kája","kaja@greendavid.local","")])
    db.commit()
    db.close()

@app.route("/health")
def health():
    return jsonify(ok=True)

# ---------------- Employees CRUD ----------------
@app.route("/api/employees", methods=["GET","POST"])
def employees_list_create():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM employees ORDER BY name")]
        return jsonify(ok=True, employees=rows)
    d = request.get_json(force=True, silent=True) or {}
    name = (d.get("name") or "").strip()
    if not name: return jsonify(ok=False, error="missing_name"), 400
    cur = db.execute("INSERT INTO employees(name,email,phone) VALUES (?,?,?)", (name, d.get("email"), d.get("phone")))
    db.commit()
    return jsonify(ok=True, id=cur.lastrowid)

@app.route("/api/employees/<int:eid>", methods=["PATCH","DELETE"])
def employees_update_delete(eid):
    db = get_db()
    if request.method == "DELETE":
        db.execute("DELETE FROM employees WHERE id=?", (eid,)); db.commit(); return jsonify(ok=True)
    d = request.get_json(force=True, silent=True) or {}
    sets = []; vals = []
    for k in ("name","email","phone"):
        if k in d: sets.append(f"{k}=?"); vals.append(d[k])
    if not sets: return jsonify(ok=True)
    vals.append(eid)
    db.execute(f"UPDATE employees SET {', '.join(sets)} WHERE id=?", vals)
    db.commit()
    return jsonify(ok=True)

# ---------------- Jobs CRUD ----------------
@app.route("/api/jobs", methods=["GET","POST"])
def jobs_list_create():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY COALESCE(date,'9999-12-31') DESC, id DESC")]
        return jsonify(ok=True, jobs=rows)
    d = request.get_json(force=True, silent=True) or {}
    title, date = d.get("title"), d.get("date")
    if not (title and date): return jsonify(ok=False, error="missing_fields"), 400
    cur = db.execute("INSERT INTO jobs(title,client,status,city,code,date,note) VALUES (?,?,?,?,?,?,?)",
                     (title, d.get("client"), d.get("status") or "Plán", d.get("city"), d.get("code"), date, d.get("note")))
    db.commit()
    return jsonify(ok=True, id=cur.lastrowid)

@app.route("/api/jobs/<int:jid>", methods=["PATCH","DELETE"])
def jobs_update_delete(jid):
    db = get_db()
    if request.method == "DELETE":
        db.execute("DELETE FROM jobs WHERE id=?", (jid,)); db.commit(); return jsonify(ok=True)
    d = request.get_json(force=True, silent=True) or {}
    sets = []; vals = []
    for k in ("title","client","status","city","code","date","note"):
        if k in d: sets.append(f"{k}=?"); vals.append(d[k])
    if not sets: return jsonify(ok=True)
    vals.append(jid)
    db.execute(f"UPDATE jobs SET {', '.join(sets)} WHERE id=?", vals)
    db.commit()
    return jsonify(ok=True)

# ---------------- Tasks CRUD ----------------
@app.route("/api/tasks", methods=["GET","POST"])
def tasks_list_create():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM tasks ORDER BY COALESCE(due_date,'9999-12-31') DESC, id DESC")]
        return jsonify(ok=True, tasks=rows)
    d = request.get_json(force=True, silent=True) or {}
    title, due_date = d.get("title"), d.get("due_date")
    if not (title and due_date): return jsonify(ok=False, error="missing_fields"), 400
    cur = db.execute("""INSERT INTO tasks(title,description,status,due_date,employee_id,job_id)
                        VALUES (?,?,?,?,?,?)""",
                     (title, d.get("description"), d.get("status") or "nový",
                      due_date, d.get("employee_id"), d.get("job_id")))
    db.commit()
    return jsonify(ok=True, id=cur.lastrowid)

@app.route("/api/tasks/<int:tid>", methods=["PATCH","DELETE"])
def tasks_update_delete(tid):
    db = get_db()
    if request.method == "DELETE":
        db.execute("DELETE FROM tasks WHERE id=?", (tid,)); db.commit(); return jsonify(ok=True)
    d = request.get_json(force=True, silent=True) or {}
    sets = []; vals = []
    for k in ("title","description","status","due_date","employee_id","job_id"):
        if k in d: sets.append(f"{k}=?"); vals.append(d[k])
    if not sets: return jsonify(ok=True)
    vals.append(tid)
    db.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id=?", vals)
    db.commit()
    return jsonify(ok=True)

# ---------------- Timesheets ----------------
@app.route("/api/timesheets", methods=["GET","POST"])
def timesheets_list_create():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("""
          SELECT t.*, j.title as job_title, j.code as job_code, e.name as employee_name
          FROM timesheets t
          JOIN jobs j ON j.id = t.job_id
          JOIN employees e ON e.id = t.employee_id
          ORDER BY date DESC, t.id DESC
        """)]
        return jsonify(ok=True, timesheets=rows)
    d = request.get_json(force=True, silent=True) or {}
    if not (d.get("employee_id") and d.get("job_id") and d.get("date") and d.get("hours") is not None):
        return jsonify(ok=False, error="missing_fields"), 400
    db.execute("""INSERT INTO timesheets(employee_id, job_id, date, hours, place, activity)
                  VALUES (?,?,?,?,?,?)""",
               (d["employee_id"], d["job_id"], d["date"], float(d["hours"]), d.get("place"), d.get("activity")))
    db.commit()
    return jsonify(ok=True)

@app.route("/api/timesheets/<int:tid>", methods=["DELETE"])
def timesheets_delete(tid):
    db = get_db()
    db.execute("DELETE FROM timesheets WHERE id=?", (tid,)); db.commit(); return jsonify(ok=True)

# ---------------- Reports ----------------
@app.route("/api/reports/employee_hours")
def api_report_employee_hours():
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    date_from, date_to = request.args.get("from"), request.args.get("to")
    if not emp: return jsonify(ok=False, error="missing_employee"), 400
    rows = [dict(r) for r in db.execute("""
      SELECT t.date, t.hours, t.place, t.activity,
             j.title as title, j.code as code, j.city as city
      FROM timesheets t JOIN jobs j ON j.id = t.job_id
      WHERE t.employee_id=?
        AND (? IS NULL OR date(t.date) >= date(?))
        AND (? IS NULL OR date(t.date) <= date(?))
      ORDER BY t.date ASC
    """, (emp, date_from, date_from, date_to, date_to)).fetchall()]
    total = sum((r["hours"] or 0) for r in rows)
    return jsonify(ok=True, rows=rows, total_hours=total)

@app.route("/export/employee_hours.csv")
def export_employee_hours_csv():
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    date_from, date_to = request.args.get("from"), request.args.get("to")
    if not emp: return make_response("missing_employee", 400)
    rows = db.execute("""
      SELECT t.date, t.hours, t.place, t.activity,
             j.title as title, j.code as code, j.city as city
      FROM timesheets t JOIN jobs j ON j.id = t.job_id
      WHERE t.employee_id=?
        AND (? IS NULL OR date(t.date) >= date(?))
        AND (? IS NULL OR date(t.date) <= date(?))
      ORDER BY t.date ASC
    """, (emp, date_from, date_from, date_to, date_to)).fetchall()
    sio = io.StringIO()
    w = csv.writer(sio)
    w.writerow(["Datum","Hodiny","Zakázka","Kód","Město","Místo","Popis"])
    for r in rows:
        w.writerow([r["date"], r["hours"], r["title"], r["code"], r["city"], r["place"], r["activity"]])
    out = sio.getvalue().encode("utf-8")
    return Response(out, headers={
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": "attachment; filename=employee_hours.csv"
    })

# ---------------- Inline SPA ----------------
PAGE = r"""<!doctype html><html lang='cs'><head>
<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Green David – App</title>
<style>
:root{--bg:#0d1311;--panel:#111a16;--line:#1f2a25;--txt:#eaf6ef;--muted:#9bb3a8;--accent:#1dbf73;--accent-2:#2e7d5b}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--txt);font-family:system-ui,-apple-system,Segoe UI,Roboto,Inter,sans-serif}
.topbar{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:linear-gradient(180deg,#0f1714,#0d1311)}
.brand{font-weight:700}
#tabs{display:flex;gap:6px;flex-wrap:wrap}
.tab{padding:8px 12px;border:1px solid var(--line);border-radius:10px;cursor:pointer}
.tab.active{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent) inset}
main{padding:16px;max-width:1200px;margin:0 auto}
.grid{display:grid;gap:14px}
.card{border:1px solid var(--line);border-radius:16px;background:var(--panel);overflow:hidden}
.card-h{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid var(--line);font-weight:600}
.card-c{padding:14px}
.form-row{display:flex;gap:10px;margin:8px 0;flex-wrap:wrap}
.form-row input,.form-row select,.form-row button,.form-row textarea{padding:10px;border-radius:10px;border:1px solid var(--line);background:#0e1513;color:var(--txt)}
.form-row button{background:#0f1915;border-color:var(--accent-2);cursor:pointer}
.table{width:100%;border-collapse:collapse}.table th,.table td{border-bottom:1px solid var(--line);padding:10px;text-align:left;font-size:14px}
.actions{display:flex;gap:8px}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:6px}
.cal-dow{font-weight:700;font-size:12px;color:var(--muted);text-align:center;padding:6px 0}
.cal-cell{background:var(--panel);border:1px solid var(--line);border-radius:12px;min-height:86px;padding:8px;cursor:pointer;position:relative}
.cal-dim{opacity:.45}.cal-today{outline:2px solid var(--accent)}.cal-date{position:absolute;top:6px;right:8px;font-size:12px;color:#a8b7ae}
.cal-dots{display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-top:16px}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#d0d7d3}.dot.job{background:#7fbf7f}.dot.task{background:#92a7ff}.dot.note{background:#ffd280}
.dot.more{border-radius:6px;padding:0 4px;height:18px;line-height:18px;font-size:11px;background:#62706a;color:#eaf6ef}
.pill{display:inline-block;font-size:11px;padding:2px 6px;border-radius:999px;background:#62706a;color:#fff;margin-right:6px;text-transform:uppercase}
.pill.task{background:#5b6be0}.pill.job{background:#2b8c4f}.pill.note{background:#b7892e}
.alert{padding:10px;border-radius:8px;margin:8px 0;font-size:13px}.alert.ok{background:#203c2c;color:#d9ffe9;border:1px solid #2a8c5f}.alert.error{background:#3c2020;color:#ffd9d9;border:1px solid #8c2a2a}
.muted{color:#9bb3a8;font-size:13px}.right{margin-left:auto;display:flex;align-items:center;gap:6px}
.btn{display:inline-block;padding:10px 14px;border-radius:10px;border:1px solid var(--accent-2);background:var(--panel);color:var(--txt);text-decoration:none}
.btn.small{padding:6px 10px;font-size:12px}
.btn.danger{border-color:#8c2a2a}
.btn.disabled{pointer-events:none;opacity:.5}
</style>
</head><body>
<header class="topbar"><div class="brand">Green David</div><nav id="tabs"></nav></header>
<main id="view"></main>
<script>
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const api=async (url,opts={})=>{const res=await fetch(url,Object.assign({headers:{"Content-Type":"application/json"}},opts));const data=await res.json().catch(()=>({}));if(!res.ok||data.ok===false){throw new Error((data&&(data.error||data.detail))||("HTTP "+res.status))}return data};

window.App=(function(){
  const tabs=[{key:"calendar",label:"Kalendář"},{key:"reports",label:"Výkazy"},{key:"jobs",label:"Zakázky"},{key:"tasks",label:"Úkoly"},{key:"employees",label:"Zaměstnanci"}];
  let state={tab:"calendar"};
  function renderTabs(){const el=$("#tabs"); el.innerHTML=""; tabs.forEach(t=>{const a=document.createElement("div"); a.className="tab"+(state.tab===t.key?" active":""); a.textContent=t.label; a.onclick=()=>{state.tab=t.key; render();}; el.appendChild(a);});}
  async function render(){renderTabs(); const root=$("#view"); if(state.tab==="calendar") await CalendarView(root); else if(state.tab==="reports") await ReportsView(root); else if(state.tab==="jobs") await JobsView(root); else if(state.tab==="tasks") await TasksView(root); else await EmployeesView(root);}
  return {start:()=>render()};
})();

async function CalendarView(root){
  root.innerHTML = `<div class="grid" style="grid-template-columns:1.2fr 0.8fr">
    <div class="card"><div class="card-h"><div class="right"><button class="tab" id="cal_prev">◀</button><b id="cal_title"></b><button class="tab" id="cal_next">▶</button></div><div class="right">Kalendář</div></div>
      <div class="card-c"><div class="cal-grid" id="cal_grid"></div></div></div>
    <div class="card"><div class="card-h"><div>Detail dne</div></div><div class="card-c">
      <div style="margin-bottom:8px"><b id="sel_date">Vyber den</b></div>
      <div id="cal_err" class="alert error" style="display:none"></div>
      <ul class="list" id="cal_list"></ul>
      <form id="cal_form">
        <div class="form-row">
          <select id="f_type"><option value="note">Poznámka</option><option value="task">Úkol</option><option value="job">Zakázka</option></select>
          <input type="date" id="f_date" required>
        </div>
        <div class="form-row"><input id="f_title" placeholder="Nadpis" required></div>
        <div class="form-row"><input id="f_notes" placeholder="Poznámka (volitelné)"></div>
        <div class="form-row" id="f_job_more" style="display:none"><input id="f_client" placeholder="Klient"><input id="f_city" placeholder="Město"><input id="f_code" placeholder="Kód"></div>
        <div class="form-row" id="f_task_more" style="display:none"><select id="f_employee_id"></select><select id="f_job_id"></select></div>
        <div class="form-row"><button type="submit">Přidat</button></div>
      </form>
    </div></div>`;
  let today=new Date(); let ym={y:today.getFullYear(), m:today.getMonth()+1}; let selected=null;
  const grid=$("#cal_grid"), title=$("#cal_title"), sel=$("#sel_date"), list=$("#cal_list"), err=$("#cal_err");

  const employees=(await api("/api/employees")).employees||[]; const jobs=(await api("/api/jobs")).jobs||[];
  $("#f_employee_id").innerHTML=`<option value="">Zaměstnanec (volit.)</option>`+employees.map(e=>`<option value="${e.id}">${e.name}</option>`).join("");
  $("#f_job_id").innerHTML=`<option value="">Zakázka (volit.)</option>`+jobs.map(j=>`<option value="${j.id}">${j.title} (${j.code||""})</option>`).join("");

  const pad=n=>String(n).padStart(2,"0"), iso=d=>d.toISOString().slice(0,10), eom=(y,m)=>new Date(y,m,0).getDate();
  async function load(){err.style.display="none"; const from=`${ym.y}-${pad(ym.m)}-01`, to=`${ym.y}-${pad(eom(ym.y,ym.m))}`; const j=await api(`/api/calendar?from=${from}&to=${to}`); draw(j.events||[])}
  function draw(events){
    const first=new Date(ym.y, ym.m-1, 1); const start=new Date(first); const dow=first.getDay()||7; start.setDate(1-(dow-1));
    const days=Array.from({length:42},(_,i)=>new Date(start.getFullYear(),start.getMonth(),start.getDate()+i));
    title.textContent=`${ym.y}-${pad(ym.m)}`;
    grid.innerHTML=["Po","Út","St","Čt","Pá","So","Ne"].map(d=>`<div class="cal-dow">${d}</div>`).join("")+
      days.map(d=>{const k=iso(d); const ev=events.filter(e=>e.start===k); const inMonth=(d.getMonth()+1)===ym.m;
        const dots=ev.slice(0,4).map(e=>`<span class="dot dot-${e.type}" title="${(e.title||"").replace(/"/g,'&quot;')}"></span>`).join("");
        const more=ev.length>4?`<span class="dot more">+${ev.length-4}</span>`:""; const todayIso=iso(new Date());
        return `<div class="cal-cell${inMonth?"":" cal-dim"}${k===todayIso?" cal-today":""}" data-date="${k}"><div class="cal-date">${d.getDate()}</div><div class="cal-dots">${dots}${more}</div></div>`;}).join("");
    $$(".cal-cell", grid).forEach(c=>{c.onclick=()=>{selected=c.getAttribute("data-date"); sel.textContent=selected; $("#f_date").value=selected; renderList(events.filter(e=>e.start===selected));}});
    if(!selected){selected=`${ym.y}-${pad(ym.m)}-01`; sel.textContent=selected; $("#f_date").value=selected; renderList(events.filter(e=>e.start===selected));}
  }
  function renderList(evts){list.innerHTML=evts.map(e=>`<li><span class="pill ${e.type}">${e.type}</span> ${e.title||""}</li>`).join("") || `<div class="muted">Žádné položky.</div>`}
  $("#cal_prev").onclick=()=>{ym.m--; if(ym.m<1){ym.m=12; ym.y--;} load();};
  $("#cal_next").onclick=()=>{ym.m++; if(ym.m>12){ym.m=1; ym.y++;} load();};

  const typeSel=$("#f_type"), jobMore=$("#f_job_more"), taskMore=$("#f_task_more");
  const toggle=()=>{jobMore.style.display=(typeSel.value==="job")?"flex":"none"; taskMore.style.display=(typeSel.value!=="note")?"flex":"none"}; typeSel.onchange=toggle; toggle();

  $("#cal_form").onsubmit=async ev=>{
    ev.preventDefault(); err.style.display="none";
    const type=typeSel.value; const payload={type, title:$("#f_title").value.trim(), start:$("#f_date").value, notes:($("#f_notes").value||"").trim()||null};
    if(!payload.title||!payload.start){err.textContent="Vyplň název a datum."; err.style.display="block"; return;}
    if(type==="job"){payload.client=$("#f_client").value.trim(); payload.city=$("#f_city").value.trim(); payload.code=$("#f_code").value.trim();
      if(!(payload.client&&payload.city&&payload.code)){err.textContent="Pro zakázku vyplň Klient, Město a Kód."; err.style.display="block"; return;}}
    if(type==="task"){const eid=$("#f_employee_id").value, jid=$("#f_job_id").value; if(eid) payload.employee_id=Number(eid); if(jid) payload.job_id=Number(jid);}
    try{ await fetch("/api/calendar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}).then(r=>r.json()); $("#f_title").value=""; $("#f_notes").value=""; await load(); }
    catch(ex){ err.textContent="Chyba uložení: "+ex.message; err.style.display="block"; }
  };
  await load();
}

async function ReportsView(root){
  root.innerHTML = `<div class="grid">
    <div class="card"><div class="card-h"><div>Výkaz hodin zaměstnance</div></div><div class="card-c">
      <form id="rep_form"><div class="form-row">
        <select id="rep_employee" required></select>
        <input type="date" id="rep_from"><input type="date" id="rep_to">
        <button type="submit">Načíst</button>
        <a id="rep_export" class="btn disabled" href="#">Export CSV</a>
      </div></form>
      <div class="muted" style="margin:8px 0">Celkem hodin: <b id="rep_total">0</b></div>
      <table class="table"><thead><tr><th>Datum</th><th>Hodiny</th><th>Zakázka</th><th>Kód</th><th>Město</th><th>Místo</th><th>Popis</th></tr></thead><tbody id="rep_tbody"></tbody></table>
    </div></div>
    <div class="card"><div class="card-h"><div>Přidat záznam do výkazu</div></div><div class="card-c">
      <div id="rep_msg" class="alert" style="display:none"></div>
      <form id="rep_add"><div class="form-row">
        <select id="ts_employee"></select><select id="ts_job"></select></div>
        <div class="form-row"><input type="date" id="ts_date" required><input type="number" id="ts_hours" step="0.25" min="0" placeholder="Hodiny" required></div>
        <div class="form-row"><input id="ts_place" placeholder="Místo (volit.)"><input id="ts_activity" placeholder="Popis (volit.)"></div>
        <div class="form-row"><button type="submit">Přidat do výkazu</button></div>
      </form>
    </div></div>
  </div>`;

  const employees=(await api("/api/employees")).employees||[]; const jobs=(await api("/api/jobs")).jobs||[];
  const empSel=$("#rep_employee"); empSel.innerHTML=`<option value="">Vyber zaměstnance…</option>`+employees.map(e=>`<option value="${e.id}">${e.name}</option>`).join("");
  $("#ts_employee").innerHTML=employees.map(e=>`<option value="${e.id}">${e.name}</option>`).join("");
  $("#ts_job").innerHTML=jobs.map(j=>`<option value="${j.id}">${j.title} (${j.code||""})</option>`).join("");

  const tbody=$("#rep_tbody"), totalEl=$("#rep_total"), exp=$("#rep_export");

  async function loadRows(){
    const emp=empSel.value; if(!emp) return;
    const f=$("#rep_from").value||"", t=$("#rep_to").value||"";
    const j=await api(`/api/reports/employee_hours?employee_id=${emp}&from=${f}&to=${t}`);
    tbody.innerHTML=j.rows.map(r=>`<tr><td>${r.date}</td><td>${r.hours}</td><td>${r.title||""}</td><td>${r.code||""}</td><td>${r.city||""}</td><td>${r.place||""}</td><td>${r.activity||""}</td></tr>`).join("");
    totalEl.textContent=j.total_hours; exp.classList.remove("disabled"); exp.href=\`/export/employee_hours.csv?employee_id=\${emp}&from=\${f}&to=\${t}\`;
  }
  $("#rep_form").onsubmit=(ev)=>{ev.preventDefault(); loadRows();};

  const msg=$("#rep_msg");
  $("#rep_add").onsubmit=async ev=>{
    ev.preventDefault(); msg.style.display="none";
    const d={employee_id:Number($("#ts_employee").value), job_id:Number($("#ts_job").value),
             date:$("#ts_date").value, hours:Number($("#ts_hours").value),
             place:$("#ts_place").value||null, activity:$("#ts_activity").value||null};
    try{ await api("/api/timesheets",{method:"POST", body:JSON.stringify(d)}); msg.textContent="Zapsáno."; msg.className="alert ok"; msg.style.display="block"; await loadRows(); ev.target.reset(); }
    catch(ex){ msg.textContent="Uložení selhalo: "+ex.message; msg.className="alert error"; msg.style.display="block"; }
  };
}

async function JobsView(root){
  root.innerHTML = `<div class="grid"><div class="card"><div class="card-h"><div>Zakázky</div></div><div class="card-c">
    <div class="form-row">
      <input id="job_title" placeholder="Název" required>
      <input id="job_date" type="date" required>
      <input id="job_client" placeholder="Klient">
      <input id="job_city" placeholder="Město">
      <input id="job_code" placeholder="Kód">
      <button id="job_add">Přidat</button>
    </div>
    <table class="table"><thead><tr><th>Datum</th><th>Název</th><th>Kód</th><th>Klient</th><th>Město</th><th>Pozn.</th><th></th></tr></thead><tbody id="jobs_tbody"></tbody></table>
  </div></div></div>`;
  const tb=$("#jobs_tbody");
  async function load(){
    const j=await api("/api/jobs");
    tb.innerHTML=j.jobs.map(r=>`<tr data-id="${r.id}">
      <td><input value="${r.date||""}" class="in date"></td>
      <td><input value="${r.title||""}" class="in title"></td>
      <td><input value="${r.code||""}" class="in code"></td>
      <td><input value="${r.client||""}" class="in client"></td>
      <td><input value="${r.city||""}" class="in city"></td>
      <td><input value="${r.note||""}" class="in note"></td>
      <td class="actions"><button class="btn small save">Uložit</button><button class="btn small danger del">Smazat</button></td>
    </tr>`).join("");
    $$(".save", tb).forEach(b=>b.onclick=save);
    $$(".del", tb).forEach(b=>b.onclick=del);
  }
  $("#job_add").onclick=async()=>{
    await api("/api/jobs",{method:"POST", body:JSON.stringify({
      title:$("#job_title").value, date:$("#job_date").value, client:$("#job_client").value, city:$("#job_city").value, code:$("#job_code").value
    })});
    ["#job_title","#job_date","#job_client","#job_city","#job_code"].forEach(id=>$(id).value=""); await load();
  };
  async function save(ev){
    const tr=ev.target.closest("tr"), id=tr.getAttribute("data-id");
    const payload={date: $(".date",tr).value, title:$(".title",tr).value, code:$(".code",tr).value, client:$(".client",tr).value, city:$(".city",tr).value, note:$(".note",tr).value};
    await api(\`/api/jobs/\${id}\`,{method:"PATCH", body:JSON.stringify(payload)}); await load();
  }
  async function del(ev){
    const tr=ev.target.closest("tr"), id=tr.getAttribute("data-id");
    await api(\`/api/jobs/\${id}\`,{method:"DELETE"}); await load();
  }
  await load();
}

async function TasksView(root){
  root.innerHTML = `<div class="grid"><div class="card"><div class="card-h"><div>Úkoly</div></div><div class="card-c">
    <div class="form-row">
      <input id="task_title" placeholder="Název" required>
      <input id="task_due" type="date" required>
      <select id="task_employee"></select>
      <select id="task_job"></select>
      <button id="task_add">Přidat</button>
    </div>
    <table class="table"><thead><tr><th>Termín</th><th>Název</th><th>Status</th><th>Zaměstnanec</th><th>Zakázka</th><th></th></tr></thead><tbody id="tasks_tbody"></tbody></table>
  </div></div></div>`;
  const employees=(await api("/api/employees")).employees||[]; const jobs=(await api("/api/jobs")).jobs||[];
  $("#task_employee").innerHTML=`<option value="">– zaměstnanec –</option>`+employees.map(e=>`<option value="${e.id}">${e.name}</option>`).join("");
  $("#task_job").innerHTML=`<option value="">– zakázka –</option>`+jobs.map(j=>`<option value="${j.id}">${j.title} (${j.code||""})</option>`).join("");

  const tb=$("#tasks_tbody");
  async function load(){
    const j=await api("/api/tasks");
    tb.innerHTML=j.tasks.map(r=>`<tr data-id="${r.id}">
      <td><input value="${r.due_date||""}" class="in due"></td>
      <td><input value="${r.title||""}" class="in title"></td>
      <td><input value="${r.status||""}" class="in status"></td>
      <td><input value="${r.employee_id||""}" class="in employee" placeholder="ID"></td>
      <td><input value="${r.job_id||""}" class="in job" placeholder="ID"></td>
      <td class="actions"><button class="btn small save">Uložit</button><button class="btn small danger del">Smazat</button></td>
    </tr>`).join("");
    $$(".save", tb).forEach(b=>b.onclick=save);
    $$(".del", tb).forEach(b=>b.onclick=del);
  }
  $("#task_add").onclick=async()=>{
    await api("/api/tasks",{method:"POST", body:JSON.stringify({
      title:$("#task_title").value, due_date:$("#task_due").value,
      employee_id: $("#task_employee").value || null, job_id: $("#task_job").value || null
    })});
    ["#task_title","#task_due"].forEach(id=>$(id).value=""); await load();
  };
  async function save(ev){
    const tr=ev.target.closest("tr"), id=tr.getAttribute("data-id");
    const payload={
      due_date: $(".due",tr).value,
      title: $(".title",tr).value,
      status: $(".status",tr).value,
      employee_id: $(".employee",tr).value || null,
      job_id: $(".job",tr).value || null
    };
    await api(\`/api/tasks/\${id}\`, {method:"PATCH", body: JSON.stringify(payload)});
    await load();
  }
  async function del(ev){
    const tr=ev.target.closest("tr"), id=tr.getAttribute("data-id");
    await api(\`/api/tasks/\${id}\`, {method:"DELETE"});
    await load();
  }
  await load();
}

async function EmployeesView(root){
  root.innerHTML = `<div class="grid"><div class="card"><div class="card-h"><div>Zaměstnanci</div></div><div class="card-c">
    <div class="form-row">
      <input id="emp_name" placeholder="Jméno" required>
      <input id="emp_email" placeholder="Email (volit.)">
      <input id="emp_phone" placeholder="Telefon (volit.)">
      <button id="emp_add">Přidat</button>
    </div>
    <table class="table"><thead><tr><th>Jméno</th><th>Email</th><th>Telefon</th><th></th></tr></thead><tbody id="emp_tbody"></tbody></table>
  </div></div></div>`;
  const tb=$("#emp_tbody");
  async function load(){
    const j=await api("/api/employees");
    tb.innerHTML=j.employees.map(r=>`<tr data-id="${r.id}">
      <td><input value="${r.name||""}" class="in name"></td>
      <td><input value="${r.email||""}" class="in email"></td>
      <td><input value="${r.phone||""}" class="in phone"></td>
      <td class="actions"><button class="btn small save">Uložit</button><button class="btn small danger del">Smazat</button></td>
    </tr>`).join("");
    $$(".save", tb).forEach(b=>b.onclick=save);
    $$(".del", tb).forEach(b=>b.onclick=del);
  }
  $("#emp_add").onclick=async()=>{
    await api("/api/employees",{method:"POST", body:JSON.stringify({name:$("#emp_name").value, email:$("#emp_email").value||null, phone:$("#emp_phone").value||null})});
    ["#emp_name","#emp_email","#emp_phone"].forEach(id=>$(id).value=""); await load();
  };
  async function save(ev){
    const tr=ev.target.closest("tr"), id=tr.getAttribute("data-id");
    const payload={name:$(".name",tr).value, email:$(".email",tr).value||null, phone:$(".phone",tr).value||null};
    await api(\`/api/employees/\${id}\`, {method:"PATCH", body: JSON.stringify(payload)}); await load();
  }
  async function del(ev){
    const tr=ev.target.closest("tr"), id=tr.getAttribute("data-id");
    await api(\`/api/employees/\${id}\`, {method:"DELETE"}); await load();
  }
  await load();
}

App.start();
</script>
</body></html>
"""

@app.route("/")
def index():
    init_db()
    return make_response(PAGE, 200, {"Content-Type":"text/html; charset=utf-8"})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
