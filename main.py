
from __future__ import annotations
from flask import Flask, request, jsonify, send_from_directory, render_template
from datetime import date, timedelta
import threading

app = Flask(__name__, static_folder=".", template_folder="templates")

# --- In-memory store (demo) ---
_lock = threading.Lock()
_jobs = {}
_tasks = {}
_calendar = {}
_employees = {1: "Adam", 2: "Bob", 3: "Cyril", 4: "Dana"}
_idcounters = {"job": 10, "task": 10, "event": 16}

def _next(kind: str) -> int:
    with _lock:
        _idcounters[kind] += 1
        return _idcounters[kind]

with _lock:
    for i, title in [(9,"zahrada Třebonice"), (10,"zahrada Pavlíčkova")]:
        _jobs[i] = {"id": i, "title": title, "status": "probíhá"}
    for i in [15,16]:
        _calendar[i] = {"id": i, "title": f"Event {i}", "date": str(date.today()+timedelta(days=i-15)), "ref": None}

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/style.css")
def css():
    return send_from_directory(".", "style.css")

@app.get("/logo.jpg")
def logo():
    return send_from_directory(".", "logo.jpg")

@app.get("/api/me")
def me():
    return jsonify({"name":"Admin","role":"admin"})

@app.get("/api/employees")
def employees():
    return jsonify([{"id": i, "name": n} for i,n in _employees.items()])

@app.get("/api/jobs")
def list_jobs():
    return jsonify(sorted(_jobs.values(), key=lambda x: x["id"]))

@app.post("/api/jobs")
def add_job():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "bez názvu").strip()
    jid = _next("job")
    with _lock:
        _jobs[jid] = {"id": jid, "title": title, "status": "nový"}
        eid = _next("event")
        _calendar[eid] = {"id": eid, "title": title, "date": str(date.today()), "ref": {"type":"job","id":jid}}
    return jsonify({"ok": True, "id": jid})

@app.delete("/api/jobs")
def delete_job():
    sid = request.args.get("id", "").strip()
    if not sid.isdigit():
        return ("Missing or invalid id", 400)
    jid = int(sid)
    with _lock:
        if jid not in _jobs:
            return jsonify({"ok": True, "deleted": 0})
        # cascade tasks
        for tid in [tid for tid,t in _tasks.items() if t.get("job_id")==jid]:
            _tasks.pop(tid, None)
        # cascade calendar
        for eid, ev in list(_calendar.items()):
            ref = ev.get("ref")
            if ref and ref.get("type")=="job" and int(ref.get("id"))==jid:
                _calendar.pop(eid, None)
        _jobs.pop(jid, None)
    return jsonify({"ok": True})

@app.get("/api/tasks")
def list_tasks():
    return jsonify(sorted(_tasks.values(), key=lambda x: x["id"]))

@app.post("/api/tasks")
def add_task():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "task").strip()
    emp_id = int(data.get("employee_id") or 1)
    job_id = int(data.get("job_id") or 2)
    tid = _next("task")
    with _lock:
        _tasks[tid] = {"id": tid, "title": title, "employee_id": emp_id, "job_id": job_id, "status":"nový"}
        eid = _next("event")
        _calendar[eid] = {"id": eid, "title": title, "date": str(date.today()), "ref":{"type":"task","id":tid}}
    return jsonify({"ok": True, "id": tid})

@app.delete("/api/tasks")
def delete_task():
    sid = (request.args.get("id") or "").strip()
    if sid.startswith("task-"):
        sid = sid.split("-",1)[1]
    if not sid.isdigit():
        return ("Missing or invalid id", 400)
    tid = int(sid)
    with _lock:
        if tid not in _tasks:
            return jsonify({"ok": True, "deleted": 0})
        for eid, ev in list(_calendar.items()):
            ref = ev.get("ref")
            if ref and ref.get("type")=="task" and int(ref.get("id"))==tid:
                _calendar.pop(eid, None)
        _tasks.pop(tid, None)
    return jsonify({"ok": True})

@app.get("/gd/api/calendar")
def cal_list():
    out = []
    with _lock:
        for ev in sorted(_calendar.values(), key=lambda x: x["id"]):
            rid = ev.get("ref")
            if rid:
                out_id = f'{rid["type"]}-{rid["id"]}'
            else:
                out_id = str(ev["id"])
            out.append({"id": out_id, "title": ev["title"], "date": ev["date"]})
    return jsonify(out)

@app.post("/gd/api/calendar")
def cal_add():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "event").strip()
    eid = _next("event")
    with _lock:
        _calendar[eid] = {"id": eid, "title": title, "date": str(date.today()), "ref": None}
    return jsonify({"ok": True, "id": eid})

@app.delete("/gd/api/calendar")
def cal_delete():
    rid = (request.args.get("id") or "").strip()
    with _lock:
        deleted = 0
        if rid.isdigit():
            deleted += 1 if _calendar.pop(int(rid), None) else 0
        elif rid.startswith("job-") and rid.split("-",1)[1].isdigit():
            jid = int(rid.split("-",1)[1])
            for eid, ev in list(_calendar.items()):
                ref = ev.get("ref")
                if ref and ref.get("type")=="job" and int(ref.get("id"))==jid:
                    _calendar.pop(eid, None); deleted += 1
        elif rid.startswith("task-") and rid.split("-",1)[1].isdigit():
            tid = int(rid.split("-",1)[1])
            for eid, ev in list(_calendar.items()):
                ref = ev.get("ref")
                if ref and ref.get("type")=="task" and int(ref.get("id"))==tid:
                    _calendar.pop(eid, None); deleted += 1
        else:
            return ("Invalid id format", 400)
    return jsonify({"ok": True, "deleted": deleted})

if __name__ == "__main__":
    app.run(debug=True)
