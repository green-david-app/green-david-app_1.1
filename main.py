
from flask import Flask, jsonify, request, send_from_directory, redirect
import os, json
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ---- tiny helpers to LOAD/SAVE json without wiping existing data ----
def _seed_if_missing(fname, default_payload):
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default_payload, f, ensure_ascii=False, indent=2)

# do NOT overwrite existing files; only create if missing
_seed_if_missing("jobs.json", {"jobs":[]})
_seed_if_missing("employees.json", {"employees":[{"id":1,"name":"Admin"}]})
_seed_if_missing("timesheets.json", {"work_logs":[]})

def _load(name, key):
    with open(os.path.join(DATA_DIR, f"{name}.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def _save(name, payload):
    with open(os.path.join(DATA_DIR, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

app = Flask(__name__)

# ---------------- PAGES (keep your index as-is) ----------------
@app.get("/calendar")
def page_calendar():
    return send_from_directory(os.path.join(BASE_DIR, "templates"), "calendar.html")

@app.get("/timesheets")
def page_timesheets():
    return send_from_directory(os.path.join(BASE_DIR, "templates"), "timesheets.html")

# ---------------- EXISTING BASIC API (kept simple) --------------
@app.get("/api/me")
def api_me():
    return jsonify(ok=True, user={"id":1,"name":"Admin","role":"admin"})

@app.get("/api/employees")
def api_employees():
    data = _load("employees", "employees")
    return jsonify(ok=True, employees=data.get("employees", []))

@app.get("/api/jobs")
def api_jobs_list():
    data = _load("jobs", "jobs")
    return jsonify(ok=True, jobs=data.get("jobs", []))

@app.post("/api/jobs")
def api_jobs_add():
    body = request.get_json(force=True, silent=True) or {}
    data = _load("jobs","jobs"); jobs = data.get("jobs",[])
    new_id = (max([j["id"] for j in jobs]) + 1) if jobs else 1
    job = {
        "id": new_id,
        "name": (body.get("name") or f"Zakázka {new_id}").strip(),
        "client": body.get("client"),
        "city": body.get("city"),
        "code": body.get("code"),
        "date": body.get("date") or datetime.utcnow().date().isoformat(),
        "status": body.get("status") or "Plán",
        "note": body.get("note"),
    }
    jobs.append(job); _save("jobs", {"jobs": jobs})
    return jsonify(ok=True, job=job)

@app.delete("/api/jobs/<int:job_id>")
def api_jobs_delete(job_id):
    data = _load("jobs","jobs")
    jobs = [j for j in data.get("jobs",[]) if j["id"] != job_id]
    _save("jobs", {"jobs": jobs})
    return jsonify(ok=True)

# ---------------- TIMESHEETS (NEW) ----------------
@app.get("/api/timesheets")
def api_timesheets_list():
    data = _load("timesheets", "work_logs")
    return jsonify(ok=True, work_logs=data.get("work_logs", []))

@app.post("/api/timesheets")
def api_timesheets_add():
    body = request.get_json(force=True, silent=True) or {}
    for k in ["employee_id","job_id","date","hours"]:
        if body.get(k) in (None, ""):
            return (f"Missing field: {k}", 400)
    data = _load("timesheets","work_logs"); logs = data.get("work_logs",[])
    new_id = (max([w.get("id",0) for w in logs]) + 1) if logs else 1
    log = {
        "id": new_id,
        "employee_id": int(body["employee_id"]),
        "job_id": int(body["job_id"]),
        "date": str(body["date"]),
        "hours": float(str(body["hours"]).replace(",", ".")),
        "note": body.get("note")
    }
    logs.append(log); _save("timesheets", {"work_logs": logs})
    return jsonify(ok=True, work_log=log)

# ---------------- CALENDAR SUMMARY (NEW) ----------------
def _jobs_by_date():
    mp={}
    for j in _load("jobs","jobs").get("jobs",[]):
        d=j.get("date"); mp.setdefault(d, []).append(j)
    return mp

def _logs_by_date():
    mp={}
    for w in _load("timesheets","work_logs").get("work_logs",[]):
        d=w.get("date"); mp.setdefault(d, []).append(w)
    return mp

@app.get("/api/calendar/summary")
def api_calendar_summary():
    qs_from = request.args.get("from")
    qs_to = request.args.get("to")
    if not qs_from or not qs_to:
        return ("/api/calendar/summary?from=YYYY-MM-DD&to=YYYY-MM-DD", 400)
    try:
        a = datetime.fromisoformat(qs_from).date()
        b = datetime.fromisoformat(qs_to).date()
    except Exception:
        return ("Bad date format", 400)

    J=_jobs_by_date(); W=_logs_by_date()
    out=[]; cur=a
    while cur<=b:
        k=cur.isoformat()
        out.append({"date":k, "jobs":len(J.get(k,[])), "work_logs":len(W.get(k,[]))})
        cur += timedelta(days=1)
    return jsonify(ok=True, summary=out)

@app.get("/api/calendar/day")
def api_calendar_day():
    date = request.args.get("date")
    if not date: return ("Missing ?date=YYYY-MM-DD", 400)
    J=_jobs_by_date(); W=_logs_by_date()
    return jsonify(ok=True, jobs=J.get(date,[]), work_logs=W.get(date,[]))

# -------------- fallback start (for local run) --------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
