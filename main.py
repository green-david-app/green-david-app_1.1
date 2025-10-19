
app = Flask(

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

    # DELETE
    deleted = 0
    for tbl, col in [
        ("job_materials","job_id"),
        ("job_tools","job_id"),
        ("job_photos","job_id"),
        ("job_assignments","job_id"),
        ("tasks","job_id"),
        ("timesheets","job_id"),
        ("calendar_events","job_id"),
    ]:
        try:
            cur = db.execute(f"DELETE FROM {tbl} WHERE {col}=?", (jid,))
            deleted += cur.rowcount or 0
        except Exception:
            pass
    cur = db.execute("DELETE FROM jobs WHERE id=?", (jid,))
    deleted += cur.rowcount or 0
    db.commit()
    return jsonify({"ok": True, "deleted": int(deleted)})


__name__)



@app.route("/api/jobs", methods=["GET","POST","PATCH","DELETE"])def api_jobs():
    db = get_db()

    if request.method == "GET":
        rows = [dict(r) for r in db.execute("SELECT * FROM jobs ORDER BY date(date) DESC, id DESC").fetchall()]
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

    # PATCH: update existing job
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

    # DELETE: remove job and related records
    if request.method == "DELETE":
        jid = parse_id()
        if not jid:
            return jsonify({"ok": False, "error": "missing_or_bad_id"}), 400
        deleted = 0
        for tbl, col in [
            ("job_materials","job_id"),
            ("job_tools","job_id"),
            ("job_photos","job_id"),
            ("job_assignments","job_id"),
            ("tasks","job_id"),
            ("timesheets","job_id"),
            ("calendar_events","job_id"),
        ]:
            try:
                cur = db.execute(f"DELETE FROM {tbl} WHERE {col}=?", (jid,))
                deleted += cur.rowcount or 0
            except Exception:
                pass
        cur = db.execute("DELETE FROM jobs WHERE id=?", (jid,))
        deleted += cur.rowcount or 0
        db.commit()
        return jsonify({"ok": True, "deleted": int(deleted)})

    # POST: create new job
    for k in ("title", "city", "code", "date"):
        if not (data.get(k) and str(data.get(k)).strip()):
            return jsonify({"ok": False, "error": "missing_fields", "field": k}), 400

    title  = str(data["title"]).strip()
    city   = str(data["city"]).strip()
    code   = str(data["code"]).strip()
    client = str((data.get("client") or "")).strip()
    status = str((data.get("status") or "Plán")).strip()
    date   = normalize_date(str(data["date"]).strip())
    note   = (data.get("note") or "").strip()
    uid    = data.get("owner_id")
    if uid is None:
        uid = get_admin_id(db)

    cols = {r[1] for r in db.execute("PRAGMA table_info(jobs)").fetchall()}
    need_name = ("name" in cols)
    has_created_at = ("created_at" in cols)

    if need_name and has_created_at:
        db.execute(
            "INSERT INTO jobs(title, name, client, status, city, code, date, note, owner_id, created_at) VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))",
            (title, title, client, status, city, code, date, note, uid)
        )
    elif need_name and not has_created_at:
        db.execute(
            "INSERT INTO jobs(title, name, client, status, city, code, date, note, owner_id) VALUES (?,?,?,?,?,?,?,?,?)",
            (title, title, client, status, city, code, date, note, uid)
        )
    elif (not need_name) and has_created_at:
        db.execute(
            "INSERT INTO jobs(title, client, status, city, code, date, note, owner_id, created_at) VALUES (?,?,?,?,?,?,?,?,datetime('now'))",
            (title, client, status, city, code, date, note, uid)
        )
    else:
        db.execute(
            "INSERT INTO jobs(title, client, status, city, code, date, note, owner_id) VALUES (?,?,?,?,?,?,?,?)",
            (title, client, status, city, code, date, note, uid)
        )

    db.commit()
    return jsonify({"ok": True})
