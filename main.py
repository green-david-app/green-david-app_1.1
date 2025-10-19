

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
