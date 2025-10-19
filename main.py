# -*- coding: utf-8 -*-
import os, sqlite3, re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, Response, send_from_directory, abort, make_response

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "db.sqlite3")

# --------- Utilities ---------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_date(s):
    if not s:
        return None
    s = str(s)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date().isoformat()
        except Exception:
            pass
    return s[:10]

def get_admin_id(db):
    row = db.execute("SELECT id FROM employees ORDER BY id LIMIT 1").fetchone()
    return row["id"] if row else 1

INJECT_SNIPPET = '<script src="/fix-frontend.js?v=20251019"></script>'

def serve_html_with_injection(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
    except UnicodeDecodeError:
        with open(path, "rb") as f:
            raw = f.read()
        try:
            html = raw.decode("cp1250")
        except Exception:
            html = raw.decode("latin-1", errors="ignore")
    # inject only if not present
    if "fix-frontend.js" not in html:
        if re.search(r"</body\s*>", html, flags=re.I):
            html = re.sub(r"</body\s*>", INJECT_SNIPPET + "</body>", html, count=1, flags=re.I)
        else:
            html = html + INJECT_SNIPPET
    return Response(html, mimetype="text/html; charset=utf-8")

# --------- Static / index with auto-inject ---------
@app.route("/")
def root():
    if os.path.exists("index.html"):
        return serve_html_with_injection("index.html")
    return Response("<!doctype html><html><body>OK "+INJECT_SNIPPET+"</body></html>", mimetype="text/html")

@app.route("/<path:fname>")
def static_files(fname):
    # serve HTML with injection, others as-is
    if os.path.exists(fname):
        if fname.lower().endswith(".html"):
            return serve_html_with_injection(fname)
        return send_from_directory(".", fname)
    abort(404)

# Serve the helper JS from file if present, otherwise from embedded string
FIX_JS_TEXT = r"""
(function(){
  function qsAll(sel){ return Array.prototype.slice.call(document.querySelectorAll(sel)); }
  async function httpDelete(url){
    const res = await fetch(url, { method: 'DELETE' });
    if(!res.ok){ throw new Error('HTTP '+res.status+' '+(await res.text().catch(()=>''))); }
    return res.json().catch(()=> ({}));
  }
  async function httpPatch(url, patch){
    const res = await fetch(url, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch || {})
    });
    if(!res.ok){ throw new Error('HTTP '+res.status+' '+(await res.text().catch(()=>''))); }
    return res.json().catch(()=> ({}));
  }
  async function reloadAfter(promise){
    try{ await promise; location.reload(); }catch(e){ alert('Chyba: '+e.message); }
  }
  window.deleteJob = function(id){
    if(!id){ alert('Chybí ID zakázky'); return; }
    if(!confirm('Opravdu smazat zakázku #'+id+'?')) return;
    reloadAfter(httpDelete(`/api/jobs/${id}`));
  };
  window.updateJobStatus = function(id, newStatus){
    if(!id){ alert('Chybí ID zakázky'); return; }
    const s = (newStatus || prompt('Nový stav (např. "Probíhá", "Dokončeno"):', 'Probíhá')) || '';
    if(!s.trim()) return;
    reloadAfter(httpPatch(`/api/jobs/${id}`, { status: s.trim() }));
  };
  window.deleteCalendarForJob = function(jobId){
    if(!jobId){ alert('Chybí ID zakázky'); return; }
    reloadAfter(httpDelete(`/gd/api/calendar?id=job-${jobId}`));
  };
  function bind(){
    qsAll('[data-action="delete"][data-id]').forEach(btn=>{
      btn.addEventListener('click', function(ev){
        ev.preventDefault();
        window.deleteJob(btn.getAttribute('data-id'));
      });
    });
    qsAll('.delete-job[data-id]').forEach(btn=>{
      btn.addEventListener('click', function(ev){
        ev.preventDefault();
        window.deleteJob(btn.getAttribute('data-id'));
      });
    });
    qsAll('a[data-id],button[data-id]').forEach(el=>{
      const t=(el.textContent||'').toLowerCase();
      if(t.includes('smazat')){
        el.addEventListener('click', function(ev){
          ev.preventDefault();
          window.deleteJob(el.getAttribute('data-id'));
        });
      }
    });
    qsAll('[data-action="set-status"][data-id]').forEach(btn=>{
      btn.addEventListener('click', function(ev){
        ev.preventDefault();
        window.updateJobStatus(btn.getAttribute('data-id'), btn.getAttribute('data-status')||undefined);
      });
    });
    qsAll('[data-action="cal-del"][data-id]').forEach(btn=>{
      btn.addEventListener('click', function(ev){
        ev.preventDefault();
        window.deleteCalendarForJob(btn.getAttribute('data-id'));
      });
    });
  }
  if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', bind); }
  else { bind(); }
})();
"""

@app.route("/fix-frontend.js")
def serve_fix_js():
    path = "fix-frontend.js"
    if os.path.exists(path):
        return send_from_directory(".", path)
    return Response(FIX_JS_TEXT, mimetype="application/javascript; charset=utf-8")

# ========================= AUTH (dummy) ==============================
@app.route("/api/login", methods=["POST", "OPTIONS"])
def api_login():
    if request.method == "OPTIONS":
        # simple CORS preflight allow
        r = make_response("", 204)
        r.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        r.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return r
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or data.get("email") or "admin").strip()
    # Always accept (no real password check) – front-end očekává jen 200 a nějaké info o uživateli
    resp = jsonify({"ok": True, "token": "devtoken", "user": {"name": username or "admin", "role": "owner"}})
    # set a simple cookie that index.html může číst (pokud ho používá)
    resp.set_cookie("gd_token", "devtoken", max_age=7*24*3600, httponly=False, samesite="Lax")
    return resp

@app.route("/api/logout", methods=["POST"])
def api_logout():
    resp = jsonify({"ok": True})
    resp.set_cookie("gd_token", "", expires=0)
    return resp

@app.route("/api/me")
def api_me():
    # if cookie/token needed in the future, read it
    return jsonify({"user":"admin","role":"owner","name":"Green David","tz":"Europe/Prague"})

# ========================= JOBS ==============================
@app.route("/api/jobs", methods=["GET","POST","PATCH","DELETE"])
def api_jobs():
    db = get_db()

    if request.method == "GET":
        rows = [dict(r) for r in db.execute(
            "SELECT * FROM jobs ORDER BY date(date) DESC, id DESC"
        ).fetchall()]
        return jsonify({"ok": True, "jobs": rows})

    data = request.get_json(silent=True) or {}

    def parse_id():
        v = request.args.get("id")
        if v is None and isinstance(data, dict):
            v = data.get("id")
        try:
            return int(str(v).strip()) if v is not None else None
        except Exception:
            return None

    if request.method == "PATCH":
        jid = parse_id()
        if not jid:
            return jsonify({"ok": False, "error": "missing_id"}), 400
        updates, params = [], []
        for f in ["title","client","status","city","code","date","note"]:
            if f in data and data.get(f) is not None:
                updates.append(f"{f}=?"); params.append(data.get(f))
        if not updates:
            return jsonify({"ok": False, "error": "no_changes"}), 400
        params.append(jid)
        db.execute("UPDATE jobs SET " + ",".join(updates) + " WHERE id=?", params)
        db.commit()
        return jsonify({"ok": True})

    if request.method == "DELETE":
        jid = parse_id()
        if not jid:
            return jsonify({"ok": False, "error": "missing_or_bad_id"}), 400
        deleted = 0
        for tbl in ["job_materials","job_tools","job_photos","job_assignments","tasks","timesheets","calendar_events"]:
            try:
                cur = db.execute(f"DELETE FROM {tbl} WHERE job_id=?", (jid,))
                deleted += cur.rowcount or 0
            except Exception:
                pass
        cur = db.execute("DELETE FROM jobs WHERE id=?", (jid,))
        deleted += cur.rowcount or 0
        db.commit()
        return jsonify({"ok": True, "deleted": int(deleted)})

    # POST
    for k in ("title", "city", "code", "date"):
        if not (data.get(k) and str(data.get(k)).strip()):
            return jsonify({"ok": False, "error": "missing_fields", "field": k}), 400

    title  = str(data["title"]).strip()
    city   = str(data["city"]).strip()
    code   = str(data["code"]).strip()
    client = str((data.get("client") or "")).strip()
    status = str((data.get("status") or "Plán")).strip()
    date_s = normalize_date(str(data["date"]).strip())
    note   = (data.get("note") or "").strip()
    uid    = data.get("owner_id") or get_admin_id(db)

    cols = {r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
    need_name = ("name" in cols)
    has_created_at = ("created_at" in cols)

    if need_name and has_created_at:
        db.execute(
            "INSERT INTO jobs(title, name, client, status, city, code, date, note, owner_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))",
            (title, title, client, status, city, code, date_s, note, uid)
        )
    elif need_name and not has_created_at:
        db.execute(
            "INSERT INTO jobs(title, name, client, status, city, code, date, note, owner_id) VALUES (?,?,?,?,?,?,?,?,?)",
            (title, title, client, status, city, code, date_s, note, uid)
        )
    elif (not need_name) and has_created_at:
        db.execute(
            "INSERT INTO jobs(title, client, status, city, code, date, note, owner_id, created_at) VALUES (?,?,?,?,?,?,?,?,datetime('now'))",
            (title, client, status, city, code, date_s, note, uid)
        )
    else:
        db.execute(
            "INSERT INTO jobs(title, client, status, city, code, date, note, owner_id) VALUES (?,?,?,?,?,?,?,?)",
            (title, client, status, city, code, date_s, note, uid)
        )
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/jobs/<int:jid>", methods=["GET","PATCH","DELETE"])
def api_jobs_item(jid):
    db = get_db()

    if request.method == "GET":
        row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        if not row:
            return jsonify({"error": "not_found"}), 404
        return jsonify(dict(row))

    if request.method == "PATCH":
        data = request.get_json(silent=True) or {}
        updates, params = [], []
        for f in ["title","client","status","city","code","date","note"]:
            if f in data and data.get(f) is not None:
                updates.append(f"{f}=?"); params.append(data.get(f))
        if not updates:
            return jsonify({"ok": False, "error": "no_changes"}), 400
        params.append(jid)
        db.execute("UPDATE jobs SET " + ",".join(updates) + " WHERE id=?", params)
        db.commit()
        return jsonify({"ok": True})

    deleted = 0
    for tbl in ["job_materials","job_tools","job_photos","job_assignments","tasks","timesheets","calendar_events"]:
        try:
            cur = db.execute(f"DELETE FROM {tbl} WHERE job_id=?", (jid,))
            deleted += cur.rowcount or 0
        except Exception:
            pass
    cur = db.execute("DELETE FROM jobs WHERE id=?", (jid,))
    deleted += cur.rowcount or 0
    db.commit()
    return jsonify({"ok": True, "deleted": int(deleted)})

# ========================= CALENDAR ==============================
@app.route("/gd/api/calendar", methods=["GET","POST","PATCH","DELETE"])
def api_calendar():
    db = get_db()

    if request.method == "GET":
        frm = request.args.get("from")
        to  = request.args.get("to")
        if frm and to:
            rows = [dict(r) for r in db.execute(
                "SELECT * FROM calendar_events WHERE date(date)>=? AND date(date)<=? ORDER BY date(date) ASC, id ASC",
                (normalize_date(frm), normalize_date(to))
            ).fetchall()]
        else:
            rows = [dict(r) for r in db.execute(
                "SELECT * FROM calendar_events ORDER BY date(date) ASC, id ASC"
            ).fetchall()]
        return jsonify({"ok": True, "events": rows})

    data = request.get_json(silent=True) or {}

    if request.method == "DELETE":
        eid_raw = request.args.get("id") or (data.get("id") if isinstance(data, dict) else None)
        if not eid_raw:
            return jsonify({"error":"Missing id"}), 400
        deleted = 0
        try:
            if isinstance(eid_raw, str) and eid_raw.startswith("job-"):
                jid = int(eid_raw.split("-",1)[1])
                cur = db.execute("DELETE FROM calendar_events WHERE job_id=?", (jid,))
                deleted = cur.rowcount or 0
            else:
                eid = int(eid_raw)
                cur = db.execute("DELETE FROM calendar_events WHERE id=?", (eid,))
                deleted = cur.rowcount or 0
            db.commit()
        except Exception:
            return jsonify({"error":"Bad id"}), 400
        if deleted == 0:
            return jsonify({"ok": False, "deleted": 0}), 404
        return jsonify({"ok": True, "deleted": int(deleted)})

    if request.method in ("POST","PATCH"):
        need = ("date","title")
        for k in need:
            if not (data.get(k) and str(data.get(k)).strip()):
                return jsonify({"ok": False, "error":"missing_fields", "field": k}), 400
        d = normalize_date(data["date"])
        title = str(data["title"]).strip()
        note  = str((data.get("note") or "")).strip()
        job_id = data.get("job_id")
        if request.method == "POST":
            db.execute(
                "INSERT INTO calendar_events(date, title, note, job_id) VALUES (?,?,?,?)",
                (d, title, note, job_id)
            )
            db.commit()
            return jsonify({"ok": True})
        else:
            eid = data.get("id")
            if not eid:
                return jsonify({"ok": False, "error":"missing_id"}), 400
            db.execute(
                "UPDATE calendar_events SET date=?, title=?, note=?, job_id=? WHERE id=?",
                (d, title, note, job_id, eid)
            )
            db.commit()
            return jsonify({"ok": True})

    return jsonify({"ok": False, "error":"unsupported"}), 405