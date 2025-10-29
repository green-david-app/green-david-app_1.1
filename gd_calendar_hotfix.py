
# gd_calendar_hotfix.py
# Hotfix v1.2.1: safe route registration (no duplicate endpoint assertion)
from main import app, get_db, require_role, _normalize_date
from flask import request, jsonify

def gd_api_calendar():
    # auth: same as original (write methods require elevated role)
    u, err = require_role(write=(request.method!="GET"))
    if err:
        return err

    db = get_db()

    if request.method == "GET":
        d_from = request.args.get("from")
        d_to   = request.args.get("to")
        if d_from and d_to:
            df = _normalize_date(d_from); dt = _normalize_date(d_to)
        else:
            import datetime as _dt
            today = _dt.date.today()
            df = (today.replace(day=1) - _dt.timedelta(days=365)).isoformat()
            dt = (today + _dt.timedelta(days=365)).isoformat()

        items = []

        # 1) explicit calendar_events (user-entered)
        try:
            rows = db.execute(
                "SELECT * FROM calendar_events WHERE date BETWEEN ? AND ? ORDER BY date ASC, start_time ASC",
                (df, dt)
            ).fetchall()
            items.extend([dict(r) for r in rows])
        except Exception:
            pass

        # 2) jobs as virtual events
        try:
            cols = [c[1] for c in db.execute("PRAGMA table_info(jobs)").fetchall()]
            if cols:
                rs = db.execute("SELECT * FROM jobs").fetchall()
                for r in rs:
                    rr = dict(r)
                    jd = rr.get("date") or rr.get("plan_date") or rr.get("planned_date") or rr.get("due_date") or rr.get("start_date")
                    if not jd:
                        continue
                    jd = _normalize_date(jd)
                    if jd < df or jd > dt:
                        continue
                    title = rr.get("name") or rr.get("title") or "Zakázka"
                    city  = rr.get("city") or rr.get("mesto") or ""
                    note  = rr.get("note") or rr.get("pozn") or ""
                    items.append({
                        "id": f"job-{rr.get('id')}",
                        "date": jd,
                        "title": title if not city else f"{title} ({city})",
                        "kind": "job",
                        "job_id": rr.get("id"),
                        "note": note,
                        "color": "#ef6c00"
                    })
        except Exception:
            pass

        # 3) tasks as virtual events
        try:
            cols = [c[1] for c in db.execute("PRAGMA table_info(tasks)").fetchall()]
            if cols:
                rs = db.execute("SELECT * FROM tasks").fetchall()
                for r in rs:
                    rr = dict(r)
                    td = rr.get("due_date") or rr.get("date") or rr.get("planned_date")
                    if not td:
                        continue
                    td = _normalize_date(td)
                    if td < df or td > dt:
                        continue
                    title = rr.get("title") or rr.get("name") or "Úkol"
                    items.append({
                        "id": f"task-{rr.get('id')}",
                        "date": td,
                        "title": title,
                        "kind": "task",
                        "note": rr.get("note") or "",
                        "color": "#1976d2"
                    })
        except Exception:
            pass

        items.sort(key=lambda x: (x.get("date",""), x.get("start_time") or ""))
        return jsonify({"ok": True, "items": items, "events": items})

    data = request.get_json(force=True, silent=True) or {}

    if request.method == "POST":
        date = _normalize_date(data.get("date"))
        title = (data.get("title") or "").strip()
        kind = (data.get("kind") or data.get("type") or "note").strip()
        job_id = data.get("job_id")
        start_time = (data.get("start_time") or "").strip() or None
        end_time = (data.get("end_time") or "").strip() or None
        note = (data.get("note") or data.get("details") or data.get("description") or "").strip()
        color = (data.get("color") or "").strip() or ("#1976d2" if kind=="task" else ("#ef6c00" if kind=="job" else "#2e7d32"))
        if not (date and title):
            return jsonify({"ok": False, "error":"missing_date_or_title"}), 400
        cur = db.execute(
            "INSERT INTO calendar_events(date,title,kind,job_id,start_time,end_time,note,color) VALUES(?,?,?,?,?,?,?,?)",
            (date,title,kind,job_id,start_time,end_time,note,color)
        )
        db.commit()
        return jsonify({"ok": True, "id": cur.lastrowid})

    if request.method == "PATCH":
        eid = data.get("id")
        if not eid:
            return jsonify({"ok": False, "error":"missing_id"}), 400
        fields = ["date","title","kind","job_id","start_time","end_time","note","color"]
        sets, vals = [], []
        for f in fields:
            if f in data or (f=="kind" and "type" in data):
                v = data.get(f)
                if f=="date":
                    v = _normalize_date(v)
                if f=="kind" and not v:
                    v = data.get("type")
                sets.append(f"{f}=?"); vals.append(v)
        if not sets:
            return jsonify({"ok": False, "error":"no_changes"}), 400
        vals.append(eid)
        db.execute("UPDATE calendar_events SET "+",".join(sets)+" WHERE id=?", vals)
        db.commit()
        return jsonify({"ok": True})

    # DELETE
    eid = request.args.get("id") or (data.get("id") if data else None)
    if not eid:
        return jsonify({"ok": False, "error":"missing_id"}), 400
    db.execute("DELETE FROM calendar_events WHERE id=?", (eid,))
    db.commit()
    return jsonify({"ok": True})

# Register route once (avoid duplicate endpoint mapping on multi-import)
def _route_exists(path: str) -> bool:
    try:
        for r in app.url_map.iter_rules():
            if str(r.rule) == path:
                return True
    except Exception:
        pass
    return False

if not _route_exists("/gd/api/calendar"):
    app.add_url_rule("/gd/api/calendar", view_func=gd_api_calendar,
                     methods=["GET","POST","PATCH","DELETE"], endpoint="gd_api_calendar_hotfix")
