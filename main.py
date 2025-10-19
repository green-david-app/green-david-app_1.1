# -*- coding: utf-8 -*-
import os, sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")
DB_PATH = os.environ.get("DB_PATH", "app.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def norm_date(s):
    if not s: return None
    s = str(s)[:10]
    for fmt in ("%Y-%m-%d","%d.%m.%Y","%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            pass
    return s

def ensure_schema():
    c = db()
    c.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, client TEXT, status TEXT, city TEXT, code TEXT, date TEXT, note TEXT, owner_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS calendar_events (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, title TEXT NOT NULL, note TEXT, job_id INTEGER)")
    c.commit(); c.close()

ensure_schema()

@app.route('/api/me')
def api_me():
    return jsonify({"user":"admin","role":"owner","name":"Green David","tz":"Europe/Prague"})

@app.route('/')
def root():
    if os.path.exists('index.html'):
        return send_from_directory('.', 'index.html')
    return '', 200

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return '', 404

# ---------- JOBS ----------
@app.route('/api/jobs', methods=['GET','POST','PATCH','DELETE'])
def jobs():
    conn = db()
    if request.method == 'GET':
        rows = [dict(r) for r in conn.execute('SELECT * FROM jobs ORDER BY date(date) DESC, id DESC').fetchall()]
        conn.close()
        return jsonify(rows if request.args.get('flat') else {"ok": True, "jobs": rows})

    data = request.get_json(silent=True) or {}
    jid = request.args.get('id') or data.get('id')

    if request.method == 'DELETE':
        try: jid = int(jid)
        except: conn.close(); return jsonify({"ok": False, "error":"missing_or_bad_id"}), 400
        conn.execute('DELETE FROM calendar_events WHERE job_id=?', (jid,))
        cur = conn.execute('DELETE FROM jobs WHERE id=?', (jid,))
        conn.commit(); conn.close()
        return jsonify({"ok": True, "deleted": cur.rowcount or 0})

    if request.method == 'PATCH':
        try: jid = int(jid)
        except: conn.close(); return jsonify({"ok": False, "error":"missing_id"}), 400
        updates, params = [], []
        for f in ['title','client','status','city','code','date','note']:
            if f in data and data[f] is not None:
                val = norm_date(data[f]) if f=='date' else data[f]
                updates.append(f"{f}=?"); params.append(val)
        if not updates: conn.close(); return jsonify({"ok": False, "error":"no_changes"}), 400
        params.append(jid)
        conn.execute('UPDATE jobs SET '+','.join(updates)+' WHERE id=?', params)
        conn.commit(); conn.close()
        return jsonify({"ok": True})

    # POST
    for k in ('title','city','code','date'):
        if not str(data.get(k) or '').strip():
            conn.close(); return jsonify({"ok": False, "error":"missing_fields","field":k}), 400
    vals = (
        data.get('title','').strip(),
        data.get('client','').strip(),
        data.get('status','Plán').strip(),
        data.get('city','').strip(),
        data.get('code','').strip(),
        norm_date(data.get('date')),
        data.get('note','').strip(),
        int(data.get('owner_id') or 1),
    )
    conn.execute('INSERT INTO jobs(title,client,status,city,code,date,note,owner_id) VALUES (?,?,?,?,?,?,?,?)', vals)
    conn.commit(); conn.close()
    return jsonify({"ok": True})

@app.route('/api/jobs/<int:jid>', methods=['GET','PATCH','DELETE'])
def jobs_item(jid):
    conn = db()
    if request.method == 'GET':
        r = conn.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
        conn.close()
        return (jsonify(dict(r)) if r else (jsonify({"error":"not_found"}),404))

    if request.method == 'PATCH':
        data = request.get_json(silent=True) or {}
        updates, params = [], []
        for f in ['title','client','status','city','code','date','note']:
            if f in data and data[f] is not None:
                val = norm_date(data[f]) if f=='date' else data[f]
                updates.append(f"{f}=?"); params.append(val)
        if not updates: conn.close(); return jsonify({"ok": False, "error":"no_changes"}), 400
        params.append(jid)
        conn.execute('UPDATE jobs SET '+','.join(updates)+' WHERE id=?', params)
        conn.commit(); conn.close()
        return jsonify({"ok": True})

    conn.execute('DELETE FROM calendar_events WHERE job_id=?', (jid,))
    cur = conn.execute('DELETE FROM jobs WHERE id=?', (jid,))
    conn.commit(); conn.close()
    return jsonify({"ok": True, "deleted": cur.rowcount or 0})

# ---------- CALENDAR ----------
@app.route('/gd/api/calendar', methods=['GET','POST','PATCH','DELETE'])
def calendar():
    conn = db()
    if request.method == 'GET':
        frm = request.args.get('from'); to = request.args.get('to')
        if frm and to:
            rows = [dict(r) for r in conn.execute('SELECT * FROM calendar_events WHERE date(date)>=? AND date(date)<=? ORDER BY date(date), id', (norm_date(frm), norm_date(to))).fetchall()]
        else:
            rows = [dict(r) for r in conn.execute('SELECT * FROM calendar_events ORDER BY date(date), id').fetchall()]
        conn.close(); return jsonify({"ok": True, "events": rows})

    data = request.get_json(silent=True) or {}
    if request.method == 'DELETE':
        idv = request.args.get('id') or data.get('id')
        if not idv: conn.close(); return jsonify({"error":"Missing id"}), 400
        deleted = 0
        try:
            if str(idv).startswith('job-'):
                jid = int(str(idv).split('-',1)[1])
                cur = conn.execute('DELETE FROM calendar_events WHERE job_id=?', (jid,)); deleted += cur.rowcount or 0
            else:
                cur = conn.execute('DELETE FROM calendar_events WHERE id=?', (int(idv),)); deleted += cur.rowcount or 0
            conn.commit(); conn.close()
            return (jsonify({"ok": True, "deleted": deleted}) if deleted else (jsonify({"ok": False, "deleted": 0}),404))
        except Exception:
            conn.close(); return jsonify({"error":"Bad id"}), 400

    # create/update minimal
    if request.method in ('POST','PATCH'):
        for k in ('date','title'):
            if not str(data.get(k) or '').strip():
                conn.close(); return jsonify({"ok": False, "error":"missing_fields","field":k}), 400
        d = norm_date(data['date']); title = data['title']; note = data.get('note',''); job_id = data.get('job_id')
        if request.method == 'POST':
            conn.execute('INSERT INTO calendar_events(date,title,note,job_id) VALUES (?,?,?,?)',(d,title,note,job_id))
            conn.commit(); conn.close(); return jsonify({"ok": True})
        else:
            eid = data.get('id'); 
            if not eid: conn.close(); return jsonify({"ok": False, "error":"missing_id"}), 400
            conn.execute('UPDATE calendar_events SET date=?, title=?, note=?, job_id=? WHERE id=?', (d,title,note,job_id,eid))
            conn.commit(); conn.close(); return jsonify({"ok": True})

    conn.close(); return jsonify({"ok": False, "error":"unsupported"}), 405