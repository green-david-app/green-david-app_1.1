# -*- coding: utf-8 -*-
import os, sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

# Create app BEFORE any @app.route
app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "db.sqlite3")

# ------------- Helpers -------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def normalize_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date().isoformat()
    except Exception:
        try:
            return datetime.strptime(s[:10], "%d.%m.%Y").date().isoformat()
        except Exception:
            return s[:10]

def get_admin_id(db):
    row = db.execute("SELECT id FROM employees ORDER BY id LIMIT 1").fetchone()
    return row["id"] if row else 1

# ------------- Static passthrough -------------
@app.route("/")
def root():
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    return "", 200

@app.route("/<path:fname>")
def static_files(fname):
    if os.path.exists(fname):
        return send_from_directory(".", fname)
    return "", 404

@app.route("/api/me")
def api_me():
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