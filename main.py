

@app.route("/api/jobs/<int:jid>", methods=["GET","PATCH","DELETE"])
def api_jobs_item(jid):
    # Proxy to api_jobs logic by injecting id
    if request.method == "GET":
        db = get_db()
        row = db.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
        if not row: 
            return jsonify({"error":"not_found"}), 404
        return jsonify(dict(row))
    # For PATCH/DELETE reuse api_jobs by setting args
    from werkzeug.datastructures import ImmutableMultiDict
    # Merge existing args with id
    args = request.args.to_dict(flat=True)
    args["id"] = str(jid)
    request.args = ImmutableMultiDict(args)
    return api_jobs()
