from flask import Blueprint, render_template, request, jsonify, make_response
import sqlite3, os, io, csv
from datetime import datetime

GD_BP = Blueprint("gd", __name__)

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(APP_DIR, "app.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_gd_db():
    db = get_db()
    db.executescript("""
    PRAGMA journal_mode=WAL;
    CREATE TABLE IF NOT EXISTS employees (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT, phone TEXT);
    CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, client TEXT, status TEXT, city TEXT, code TEXT, date TEXT, note TEXT);
    CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, status TEXT, due_date TEXT, employee_id INTEGER, job_id INTEGER);
    CREATE TABLE IF NOT EXISTS timesheets (id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id INTEGER NOT NULL, job_id INTEGER NOT NULL, date TEXT NOT NULL, hours REAL NOT NULL, place TEXT, activity TEXT);
    CREATE TABLE IF NOT EXISTS calendar_events (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, start TEXT NOT NULL, "end" TEXT, all_day INTEGER NOT NULL DEFAULT 1, type TEXT NOT NULL DEFAULT 'note', ref_id INTEGER, notes TEXT);
    """)
    if not db.execute("SELECT 1 FROM employees LIMIT 1").fetchone():
        db.executemany("INSERT INTO employees(name,email,phone) VALUES (?,?,?)",
                    [("Pepa","pepa@greendavid.local",""), ("Míša","misa@greendavid.local",""), ("Kája","kaja@greendavid.local","")])
    db.commit()
    db.close()

@GD_BP.route("/calendar")
def page_calendar():
    ensure_gd_db()
    return render_template("gd_ext/calendar.html")

@GD_BP.route("/timesheets")
def page_timesheets():
    ensure_gd_db()
    return render_template("gd_ext/timesheets.html")

@GD_BP.route("/gd/api/employees", methods=["GET","POST"])
def employees_list_create():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM employees ORDER BY name")]
        return jsonify(ok=True, employees=rows)
    d = request.get_json(force=True, silent=True) or {}
    name = (d.get("name") or "").strip()
    if not name:
        return jsonify(ok=False, error="missing_name"), 400
    cur = db.execute("INSERT INTO employees(name,email,phone) VALUES (?,?,?)", (name, d.get("email"), d.get("phone")))
    db.commit()
    return jsonify(ok=True, id=cur.lastrowid)

@GD_BP.route("/gd/api/jobs", methods=["GET","POST"])
def jobs_list_create():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY COALESCE(date,'9999-12-31') DESC, id DESC")]
        return jsonify(ok=True, jobs=rows)
    d = request.get_json(force=True, silent=True) or {}
    title, date = d.get("title"), d.get("date")
    if not (title and date):
        return jsonify(ok=False, error="missing_fields"), 400
    cur = db.execute("INSERT INTO jobs(title,client,status,city,code,date,note) VALUES (?,?,?,?,?,?,?)",
                    (title, d.get("client"), d.get("status") or "Plán", d.get("city"), d.get("code"), date, d.get("note")))
    db.commit()
    return jsonify(ok=True, id=cur.lastrowid)

@GD_BP.route("/gd/api/tasks", methods=["GET","POST"])
def tasks_list_create():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM tasks ORDER BY COALESCE(due_date,'9999-12-31') DESC, id DESC")]
        return jsonify(ok=True, tasks=rows)
    d = request.get_json(force=True, silent=True) or {}
    title, due_date = d.get("title"), d.get("due_date")
    if not (title and due_date):
        return jsonify(ok=False, error="missing_fields"), 400
    cur = db.execute("INSERT INTO tasks(title,description,status,due_date,employee_id,job_id) VALUES (?,?,?,?,?,?)",
                    (title, d.get("description"), d.get("status") or "nový", due_date, d.get("employee_id"), d.get("job_id")))
    db.commit()
    return jsonify(ok=True, id=cur.lastrowid)

@GD_BP.route("/gd/api/timesheets", methods=["GET","POST"])
def timesheets_list_create():
    db = get_db()
    if request.method == "GET":
        rows = [dict(r) for r in db.execute("""            SELECT t.*, j.title as job_title, j.code as job_code, e.name as employee_name
        FROM timesheets t
        JOIN jobs j ON j.id = t.job_id
        JOIN employees e ON e.id = t.employee_id
        ORDER BY date DESC, t.id DESC
        """)]
        return jsonify(ok=True, timesheets=rows)
    d = request.get_json(force=True, silent=True) or {}
    if not (d.get("employee_id") and d.get("job_id") and d.get("date") and d.get("hours") is not None):
        return jsonify(ok=False, error="missing_fields"), 400
    db.execute("INSERT INTO timesheets(employee_id,job_id,date,hours,place,activity) VALUES (?,?,?,?,?,?)",
            (d["employee_id"], d["job_id"], d["date"], float(d["hours"]), d.get("place"), d.get("activity")))
    db.commit()
    return jsonify(ok=True)

@GD_BP.route("/gd/api/reports/employee_hours")
def api_report_employee_hours():
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    dfrom, dto = request.args.get("from"), request.args.get("to")
    if not emp:
        return jsonify(ok=False, error="missing_employee"), 400
    rows = [dict(r) for r in db.execute("""        SELECT t.date, t.hours, t.place, t.activity,
            j.title as title, j.code as code, j.city as city
    FROM timesheets t JOIN jobs j ON j.id = t.job_id
    WHERE t.employee_id=?
        AND (? IS NULL OR date(t.date) >= date(?))
        AND (? IS NULL OR date(t.date) <= date(?))
    ORDER BY t.date ASC
    """, (emp, dfrom, dfrom, dto, dto)).fetchall()]
    total = sum((r["hours"] or 0) for r in rows)
    return jsonify(ok=True, rows=rows, total_hours=total)

@GD_BP.route("/gd/api/export/employee_hours.csv")
def export_employee_hours_csv():
    db = get_db()
    emp = request.args.get("employee_id", type=int)
    dfrom, dto = request.args.get("from"), request.args.get("to")
    if not emp:
        return make_response("missing_employee", 400)
    rows = db.execute("""        SELECT t.date, t.hours, t.place, t.activity,
            j.title as title, j.code as code, j.city as city
    FROM timesheets t JOIN jobs j ON j.id = t.job_id
    WHERE t.employee_id=?
        AND (? IS NULL OR date(t.date) >= date(?))
        AND (? IS NULL OR date(t.date) <= date(?))
    ORDER BY t.date ASC
    """, (emp, dfrom, dfrom, dto, dto)).fetchall()
    sio = io.StringIO()
    w = csv.writer(sio)
    w.writerow(["Datum","Hodiny","Zakázka","Kód","Město","Místo","Popis"])
    for r in rows:
        w.writerow([r["date"], r["hours"], r["title"], r["code"], r["city"], r["place"], r["activity"]])
    out = sio.getvalue().encode("utf-8")
    return make_response(out, 200, {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": "attachment; filename=employee_hours.csv"
    })

@GD_BP.route("/gd/api/calendar", methods=["GET","POST","PATCH","DELETE"])
def api_calendar():
    db = get_db()
    if request.method == "GET":
        q_from = request.args.get("from") or request.args.get("start")
        q_to   = request.args.get("to") or request.args.get("end")
        if not q_from or not q_to:
            now = datetime.now(); q_from=f"{now.year}-{now.month:02d}-01"
            y2,m2 = (now.year+1,1) if now.month==12 else (now.year,now.month+1)
            q_to=f"{y2}-{m2:02d}-01"
        rows = [dict(r) for r in db.execute(
            "SELECT id,title,start,"end",all_day,type,ref_id,notes FROM calendar_events "
            "WHERE date(start) >= date(?) AND date(start) < date(?) ORDER BY start ASC, id ASC",
            (q_from, q_to)).fetchall()]
        return jsonify(ok=True, events=rows)

    data = request.get_json(force=True, silent=True) or {}
    if request.method == "POST":
        title = (data.get("title") or "").strip()
        start = (data.get("start") or "").strip()
        typ = (data.get("type") or "note").strip()
        if not title or not start:
            return jsonify(ok=False, error="missing_title_or_date"), 400
        ref_id = data.get("ref_id"); notes = data.get("notes")
        db.execute("INSERT INTO calendar_events(title,start,"end",all_day,type,ref_id,notes) VALUES (?,?,?,?,?,?,?)",
                (title, start, None, 1, typ, ref_id, notes))
        if typ == "job":
            db.execute("INSERT INTO jobs(title,client,status,city,code,date,note) VALUES (?,?,?,?,?,?,?)",
                    (title, data.get("client"), "Plán", data.get("city"), data.get("code"), start, notes))
        if typ == "task":
            db.execute("INSERT INTO tasks(title,description,status,due_date,employee_id,job_id) VALUES (?,?,?,?,?,?)",
                    (title, notes, "nový", start, data.get("employee_id"), data.get("job_id")))
        db.commit()
        return jsonify(ok=True)

    if request.method == "PATCH":
        eid = data.get("id")
        if not eid:
            return jsonify(ok=False, error="missing_id"), 400
        sets = []; vals = []
        for k in ("title","start","end","all_day","type","ref_id","notes"):
            if k in data:
                sets.append(f"{k}=?"); vals.append(data[k])
        if sets:
            vals.append(eid)
            db.execute(f"UPDATE calendar_events SET {', '.join(sets)} WHERE id=?", vals)
            db.commit()
        return jsonify(ok=True)

    # DELETE
    eid = data.get("id")
    if not eid:
        return jsonify(ok=False, error="missing_id"), 400
    db.execute("DELETE FROM calendar_events WHERE id=?", (eid,))
    db.commit()
    return jsonify(ok=True)
