import os
import sqlite3
import json
from urllib.parse import parse_qs
from datetime import datetime, date
from flask import Flask, request, jsonify, g, render_template, send_from_directory

DB_PATH = os.environ.get("DB_PATH", "app.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-" + os.urandom(16).hex())
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")

app = Flask(__name__, static_folder=".", static_url_path="")
app.secret_key = SECRET_KEY
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        ensure_meta(g.db); migrate(g.db)
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None: db.close()

def ensure_meta(db):
    db.execute("CREATE TABLE IF NOT EXISTS app_meta (id INTEGER PRIMARY KEY CHECK (id=1), version INTEGER NOT NULL)")
    if db.execute("SELECT 1 FROM app_meta WHERE id=1").fetchone() is None:
        db.execute("INSERT INTO app_meta(id,version) VALUES (1,0)")
        db.commit()

def get_version(db):
    return db.execute("SELECT version FROM app_meta WHERE id=1").fetchone()["version"]

def set_version(db, v):
    db.execute("UPDATE app_meta SET version=? WHERE id=1", (v,)); db.commit()

def migrate(db):
    v = get_version(db)
    if v < 1:
        db.execute("""CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            title TEXT,
            kind TEXT NOT NULL DEFAULT 'note',
            job_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            note TEXT,
            color TEXT DEFAULT 'green'
        )""")
        db.commit(); set_version(db, 1); v=1

def ensure_calendar_table():
    db = get_db()
    db.execute("""CREATE TABLE IF NOT EXISTS calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        title TEXT,
        kind TEXT NOT NULL DEFAULT 'note',
        job_id INTEGER,
        start_time TEXT,
        end_time TEXT,
        note TEXT,
        color TEXT DEFAULT 'green'
    )""")
    db.commit()

def migrate_calendar_columns():
    db = get_db()
    cols = [r[1] for r in db.execute("PRAGMA table_info(calendar_events)").fetchall()]
    def add_col(name, ddl):
        if name not in cols:
            db.execute(f"ALTER TABLE calendar_events ADD COLUMN {ddl}")
    add_col("kind", "TEXT NOT NULL DEFAULT 'note'")
    add_col("job_id", "INTEGER")
    add_col("start_time", "TEXT")
    add_col("end_time", "TEXT")
    add_col("note", "TEXT DEFAULT ''")
    add_col("color", "TEXT DEFAULT 'green'")
    db.commit()

def normalize_date(v):
    if not v: return None
    if isinstance(v, (datetime, date)): return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    try:
        if len(s)==10 and s[4]=='-' and s[7]=='-':
            datetime.strptime(s, "%Y-%m-%d"); return s
    except Exception: pass
    try:
        return datetime.fromisoformat(s).strftime("%Y-%m-%d")
    except Exception:
        return s

def payload_any():
    data = {}
    j = request.get_json(silent=True, force=True)
    if isinstance(j, dict):
        data.update(j)
    if request.form:
        for k in request.form:
            data[k] = request.form.get(k)
    for k in request.args:
        data.setdefault(k, request.args.get(k))
    if not data:
        raw = request.get_data(as_text=True) or ""
        if raw:
            try:
                j2 = json.loads(raw)
                if isinstance(j2, dict): data.update(j2)
            except Exception:
                try:
                    q = parse_qs(raw, keep_blank_values=True)
                    for k, vals in q.items():
                        if vals: data[k] = vals[0]
                except Exception:
                    pass
    if "note" not in data:
        for k in ("title","text","desc","description"):
            if k in data and data[k]:
                data["note"] = data[k]; break
    if "color" not in data and "tag" in data:
        data["color"] = data.get("tag")
    if "kind" not in data:
        data["kind"] = "note"
    return data

@app.route("/gd/api/calendar", methods=["GET","POST","PATCH","DELETE"])
def api_calendar():
    db = get_db()
    ensure_calendar_table()
    migrate_calendar_columns()

    if request.method == "GET":
        d_from = request.args.get("from"); d_to = request.args.get("to")
        if d_from and d_to:
            rows = db.execute(
                "SELECT * FROM calendar_events WHERE date BETWEEN ? AND ? ORDER BY date ASC, COALESCE(start_time,'') ASC",
                (d_from, d_to)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM calendar_events ORDER BY date DESC, COALESCE(start_time,'') ASC LIMIT 1000"
            ).fetchall()
        return jsonify([dict(r) for r in rows])

    data = payload_any()

    if request.method == "POST" and (str(data.get("_method") or "").upper() == "DELETE"):
        eid = data.get("id") or request.args.get("id")
        if not eid: return jsonify({"error":"Missing id"}), 400
        db.execute("DELETE FROM calendar_events WHERE id=?", (eid,)); db.commit()
        return jsonify({"ok": True})

    if request.method == "POST":
        date_s = normalize_date(data.get("date"))
        kind = (data.get("kind") or "note").strip()
        job_id = data.get("job_id")
        start_time = (data.get("start_time") or None)
        end_time = (data.get("end_time") or None)
        note = (data.get("note") or "").strip()
        color = (data.get("color") or "green").strip()
        title = (data.get("title") or None)
        if not date_s: return jsonify({"error":"Missing date"}), 400
        cur = db.execute(
            "INSERT INTO calendar_events(date,title,kind,job_id,start_time,end_time,note,color) VALUES (?,?,?,?,?,?,?,?)",
            (date_s, title, kind, job_id, start_time, end_time, note, color)
        )
        db.commit(); return jsonify({"ok": True, "id": cur.lastrowid})

    if request.method == "PATCH":
        eid = data.get("id") or request.args.get("id")
        if not eid: return jsonify({"error":"Missing id"}), 400
        fields = ["date","title","kind","job_id","start_time","end_time","note","color"]
        sets, vals = [], []
        for f in fields:
            if f in data:
                v = normalize_date(data[f]) if f=="date" else data[f]
                sets.append(f"{f}=?"); vals.append(v)
        if not sets: return jsonify({"error":"No changes"}), 400
        vals.append(eid)
        db.execute("UPDATE calendar_events SET "+",".join(sets)+" WHERE id=?", vals)
        db.commit(); return jsonify({"ok": True})

    eid = request.args.get("id") or data.get("id")
    if not eid: return jsonify({"error":"Missing id"}), 400
    db.execute("DELETE FROM calendar_events WHERE id=?", (eid,)); db.commit()
    return jsonify({"ok": True})

@app.route("/gd/api/calendar/save", methods=["POST"])
def api_calendar_save_legacy():
    db = get_db(); ensure_calendar_table(); migrate_calendar_columns()
    data = payload_any()
    date_s = normalize_date(data.get("date"))
    kind = (data.get("kind") or "note").strip()
    job_id = data.get("job_id")
    start_time = (data.get("start_time") or None)
    end_time = (data.get("end_time") or None)
    note = (data.get("note") or "").strip()
    color = (data.get("color") or "green").strip()
    title = (data.get("title") or None)
    if not date_s: return jsonify({"error":"Missing date"}), 400
    cur = db.execute(
        "INSERT INTO calendar_events(date,title,kind,job_id,start_time,end_time,note,color) VALUES (?,?,?,?,?,?,?,?)",
        (date_s, title, kind, job_id, start_time, end_time, note, color)
    )
    db.commit(); return jsonify({"ok": True, "id": cur.lastrowid})

@app.route("/gd/api/calendar/delete", methods=["POST"])
def api_calendar_delete_legacy():
    db = get_db(); ensure_calendar_table(); migrate_calendar_columns()
    data = payload_any()
    eid = data.get("id") or request.args.get("id")
    if not eid: return jsonify({"error":"Missing id"}), 400
    db.execute("DELETE FROM calendar_events WHERE id=?", (eid,)); db.commit()
    return jsonify({"ok": True})

@app.route("/")
def index():
    try:
        return render_template("index.html", title="green david app")
    except Exception:
        return "<!doctype html><title>green david app</title><h1>green david app</h1>", 200

@app.route("/calendar")
def page_calendar():
    return render_template("calendar.html", title="Kalendář")

@app.route("/uploads/<path:fn>")
def uploads(fn):
    return send_from_directory(UPLOAD_DIR, fn)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
