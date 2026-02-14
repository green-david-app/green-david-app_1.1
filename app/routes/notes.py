from flask import Blueprint, request, jsonify, send_from_directory, session
from datetime import datetime
from app.database import get_db

notes_bp = Blueprint('notes', __name__)


@notes_bp.route("/notes")
@notes_bp.route("/notes.html")
def notes_page():
    return send_from_directory(".", "notes.html")


def _notes_base_query():
    return """
        SELECT n.*,
            j.title as job_title, j.code as job_code,
            e.name as employee_name,
            p.display_name as party_name
        FROM notes n
        LEFT JOIN jobs j ON n.job_id = j.id
        LEFT JOIN employees e ON n.employee_id = e.id
        LEFT JOIN parties p ON n.party_id = p.id
        WHERE 1=1
    """


@notes_bp.route('/api/notes', methods=['GET'])
def get_notes():
    """Query params: category, job_id, employee_id, party_id, search, pinned, sort_by, limit, offset"""
    db = get_db()
    query = _notes_base_query()
    params = []

    category = request.args.get('category')
    if category:
        query += " AND n.category = ?"
        params.append(category)

    job_id = request.args.get('job_id', type=int)
    if job_id:
        query += " AND n.job_id = ?"
        params.append(job_id)

    employee_id = request.args.get('employee_id', type=int)
    if employee_id:
        query += " AND n.employee_id = ?"
        params.append(employee_id)

    party_id = request.args.get('party_id', type=int)
    if party_id:
        query += " AND n.party_id = ?"
        params.append(party_id)

    link_type = request.args.get('link_type')
    if link_type == 'free':
        query += " AND n.job_id IS NULL AND n.employee_id IS NULL AND n.party_id IS NULL"
    elif link_type == 'job':
        query += " AND n.job_id IS NOT NULL"
    elif link_type == 'employee':
        query += " AND n.employee_id IS NOT NULL"
    elif link_type == 'party':
        query += " AND n.party_id IS NOT NULL"

    search = request.args.get('search')
    if search:
        s = f"%{search}%"
        query += " AND (n.title LIKE ? OR n.content LIKE ?)"
        params.extend([s, s])

    pinned = request.args.get('pinned')
    if pinned is not None and pinned.lower() in ('1', 'true', 'yes'):
        query += " AND n.is_pinned = 1"

    # Sort: pinned always first
    sort_by = request.args.get('sort_by', 'created_at')
    allowed_sorts = ['created_at', 'updated_at', 'title']
    if sort_by not in allowed_sorts:
        sort_by = 'created_at'
    order_dir = 'DESC'
    if sort_by == 'title':
        order_dir = 'ASC'
    query += f" ORDER BY n.is_pinned DESC, n.{sort_by} {order_dir}"

    count_query = "SELECT COUNT(*) FROM notes n WHERE 1=1"
    count_params = []
    if category:
        count_params.append(category)
        count_query += " AND n.category = ?"
    if job_id:
        count_params.append(job_id)
        count_query += " AND n.job_id = ?"
    if employee_id:
        count_params.append(employee_id)
        count_query += " AND n.employee_id = ?"
    if party_id:
        count_params.append(party_id)
        count_query += " AND n.party_id = ?"
    if link_type == 'free':
        count_query += " AND n.job_id IS NULL AND n.employee_id IS NULL AND n.party_id IS NULL"
    elif link_type == 'job':
        count_query += " AND n.job_id IS NOT NULL"
    elif link_type == 'employee':
        count_query += " AND n.employee_id IS NOT NULL"
    elif link_type == 'party':
        count_query += " AND n.party_id IS NOT NULL"
    if search:
        count_params.extend([s, s])
        count_query += " AND (n.title LIKE ? OR n.content LIKE ?)"
    if pinned is not None and pinned.lower() in ('1', 'true', 'yes'):
        count_query += " AND n.is_pinned = 1"

    total = db.execute(count_query, count_params).fetchone()[0]

    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = db.execute(query, params).fetchall()
    notes = [dict(r) for r in rows]

    for n in notes:
        if 'is_pinned' in n:
            n['is_pinned'] = bool(n['is_pinned'])

    return jsonify({"notes": notes, "total": total})


@notes_bp.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    db = get_db()
    row = db.execute(_notes_base_query() + " AND n.id = ?", (note_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "not_found"}), 404
    note = dict(row)
    note['is_pinned'] = bool(note.get('is_pinned', 0))
    return jsonify(note)


@notes_bp.route('/api/notes', methods=['POST'])
def create_note():
    db = get_db()
    user_id = session.get('uid') or session.get('user_id')
    data = request.json or {}

    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({"ok": False, "error": "content is required"}), 400

    title = (data.get('title') or '').strip() or None
    category = data.get('category', 'general')
    color = data.get('color', 'default')
    job_id = data.get('job_id') or None
    employee_id = data.get('employee_id') or None
    party_id = data.get('party_id') or None

    if job_id is not None and job_id == '':
        job_id = None
    if employee_id is not None and employee_id == '':
        employee_id = None
    if party_id is not None and party_id == '':
        party_id = None

    cur = db.execute(
        """INSERT INTO notes (title, content, category, color, job_id, employee_id, party_id, created_by, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
        (title, content, category, color, job_id, employee_id, party_id, user_id)
    )
    note_id = cur.lastrowid
    db.commit()

    row = db.execute(_notes_base_query() + " AND n.id = ?", (note_id,)).fetchone()
    note = dict(row) if row else {"id": note_id}
    note['is_pinned'] = bool(note.get('is_pinned', 0))

    return jsonify({"ok": True, "id": note_id, "note": note})


@notes_bp.route('/api/notes/<int:note_id>', methods=['PUT', 'PATCH'])
def update_note(note_id):
    db = get_db()
    data = request.json or {}

    allowed = ['title', 'content', 'category', 'color', 'job_id', 'employee_id', 'party_id']
    updates = []
    params = []

    for field in allowed:
        if field in data:
            if field in ('job_id', 'employee_id', 'party_id'):
                val = data[field]
                if val == '' or val is None:
                    val = None
                updates.append(f"{field} = ?")
                params.append(val)
            else:
                updates.append(f"{field} = ?")
                params.append(data[field])

    if not updates:
        row = db.execute(_notes_base_query() + " AND n.id = ?", (note_id,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "not_found"}), 404
        note = dict(row)
        note['is_pinned'] = bool(note.get('is_pinned', 0))
        return jsonify({"ok": True, "note": note})

    updates.append("updated_at = datetime('now')")
    params.append(note_id)

    db.execute(f"UPDATE notes SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()

    row = db.execute(_notes_base_query() + " AND n.id = ?", (note_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "not_found"}), 404
    note = dict(row)
    note['is_pinned'] = bool(note.get('is_pinned', 0))
    return jsonify({"ok": True, "note": note})


@notes_bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()
    return jsonify({"ok": True})


@notes_bp.route('/api/notes/<int:note_id>/pin', methods=['PUT'])
def toggle_pin_note(note_id):
    db = get_db()
    row = db.execute("SELECT is_pinned FROM notes WHERE id = ?", (note_id,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "not_found"}), 404
    new_pinned = 0 if row['is_pinned'] else 1
    db.execute("UPDATE notes SET is_pinned = ?, updated_at = datetime('now') WHERE id = ?", (new_pinned, note_id))
    db.commit()
    return jsonify({"ok": True, "is_pinned": bool(new_pinned)})


@notes_bp.route('/api/notes/stats', methods=['GET'])
def notes_stats():
    db = get_db()

    total = db.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    pinned = db.execute("SELECT COUNT(*) FROM notes WHERE is_pinned = 1").fetchone()[0]

    today = datetime.now().date().isoformat()
    week_start = datetime.now()
    from datetime import timedelta
    week_start = (week_start - timedelta(days=week_start.weekday())).date().isoformat()
    this_week = db.execute(
        "SELECT COUNT(*) FROM notes WHERE date(created_at) >= ?",
        (week_start,)
    ).fetchone()[0]

    by_cat = db.execute(
        "SELECT category, COUNT(*) as cnt FROM notes GROUP BY category ORDER BY cnt DESC LIMIT 5"
    ).fetchall()
    by_category = {r['category']: r['cnt'] for r in by_cat}

    top_category = max(by_category.items(), key=lambda x: x[1])[0] if by_category else '-'

    return jsonify({
        "total": total,
        "this_week": this_week,
        "pinned": pinned,
        "by_category": by_category,
        "top_category": top_category,
    })
