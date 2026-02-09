from flask import Blueprint, request, jsonify, send_from_directory
import json
from app.database import get_db

parties_bp = Blueprint('parties', __name__)


# Route pro directory.html stránku
@parties_bp.route("/directory")
def directory_page():
    return send_from_directory(".", "directory.html")

# GET /api/parties — seznam s filtrací
@parties_bp.route('/api/parties', methods=['GET'])
def get_parties():
    """Query params: role, status, tier, search, sort_by, limit, offset"""
    db = get_db()
    
    query = "SELECT * FROM parties WHERE 1=1"
    params = []
    
    role = request.args.get('role')
    if role:
        query += " AND roles LIKE ?"
        params.append(f'%"{role}"%')
    
    status = request.args.get('status')
    if status:
        query += " AND status = ?"
        params.append(status)
    
    tier = request.args.get('tier')
    if tier:
        query += " AND tier = ?"
        params.append(tier)
    
    search = request.args.get('search')
    if search:
        query += " AND (display_name LIKE ? OR legal_name LIKE ? OR email LIKE ? OR ico LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
    
    # Řazení
    sort = request.args.get('sort_by', 'display_name')
    allowed_sorts = ['display_name', 'total_revenue', 'health_index', 'last_job_date', 'created_at']
    if sort in allowed_sorts:
        if sort == 'display_name':
            query += " ORDER BY display_name ASC"
        else:
            query += f" ORDER BY {sort} DESC"
    else:
        query += " ORDER BY display_name ASC"
    
    # Počet celkem
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    total = db.execute(count_query, params).fetchone()[0]
    
    # Stránkování
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    rows = db.execute(query, params).fetchall()
    parties = [dict(r) for r in rows]
    
    return jsonify({"parties": parties, "total": total})


# GET /api/parties/<id> — detail s kontakty, interakcemi a zakázkami
@parties_bp.route('/api/parties/<int:party_id>', methods=['GET'])
def get_party(party_id):
    db = get_db()
    
    party = db.execute("SELECT * FROM parties WHERE id = ?", (party_id,)).fetchone()
    if not party:
        return jsonify({"error": "not_found"}), 404
    
    party = dict(party)
    
    # Kontaktní osoby
    contacts = db.execute(
        "SELECT * FROM party_contacts WHERE party_id = ? ORDER BY is_primary DESC, name",
        (party_id,)
    ).fetchall()
    party['contacts'] = [dict(c) for c in contacts]
    
    # Interakce (posledních 20)
    interactions = db.execute(
        "SELECT * FROM party_interactions WHERE party_id = ? ORDER BY date DESC LIMIT 20",
        (party_id,)
    ).fetchall()
    party['interactions'] = [dict(i) for i in interactions]
    
    # Zakázky
    jobs = db.execute(
        "SELECT id, title, name, status, created_at, deadline FROM jobs WHERE party_id = ? ORDER BY created_at DESC",
        (party_id,)
    ).fetchall()
    party['jobs'] = [dict(j) for j in jobs]
    
    return jsonify(party)


# POST /api/parties — nová protistrana
@parties_bp.route('/api/parties', methods=['POST'])
def create_party():
    db = get_db()
    data = request.json or {}
    
    if not data.get('display_name'):
        return jsonify({"error": "display_name is required"}), 400
    
    fields = ['type', 'display_name', 'legal_name', 'email', 'phone', 'website',
              'street', 'city', 'zip', 'country', 'ico', 'dic', 'bank_account',
              'roles', 'tier', 'status', 'tags', 'note', 'source']
    
    cols = []
    vals = []
    for f in fields:
        if f in data:
            val = data[f]
            if isinstance(val, (list, dict)):
                val = json.dumps(val)
            cols.append(f)
            vals.append(val)
    
    if not cols:
        return jsonify({"error": "No valid fields provided"}), 400
    
    placeholders = ','.join(['?'] * len(cols))
    col_names = ','.join(cols)
    
    cursor = db.execute(f"INSERT INTO parties ({col_names}) VALUES ({placeholders})", vals)
    db.commit()
    
    return jsonify({"ok": True, "id": cursor.lastrowid})


# PUT /api/parties/<id> — úprava
@parties_bp.route('/api/parties/<int:party_id>', methods=['PUT', 'PATCH'])
def update_party(party_id):
    db = get_db()
    data = request.json or {}
    
    updates = []
    params = []
    
    allowed = ['type', 'display_name', 'legal_name', 'email', 'phone', 'website',
               'street', 'city', 'zip', 'country', 'ico', 'dic', 'bank_account',
               'roles', 'tier', 'status', 'health_index', 'payment_reliability',
               'tags', 'note', 'source']
    
    for field in allowed:
        if field in data:
            updates.append(f"{field} = ?")
            val = data[field]
            if isinstance(val, (list, dict)):
                val = json.dumps(val)
            params.append(val)
    
    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400
    
    updates.append("updated_at = datetime('now')")
    params.append(party_id)
    
    db.execute(f"UPDATE parties SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    
    return jsonify({"ok": True})


# DELETE /api/parties/<id>
@parties_bp.route('/api/parties/<int:party_id>', methods=['DELETE'])
def delete_party(party_id):
    db = get_db()
    db.execute("DELETE FROM parties WHERE id = ?", (party_id,))
    db.commit()
    return jsonify({"ok": True})


# POST /api/parties/<id>/contacts — přidat kontaktní osobu
@parties_bp.route('/api/parties/<int:party_id>/contacts', methods=['POST'])
def add_contact(party_id):
    db = get_db()
    data = request.json or {}
    
    # Pokud je nový kontakt primární, zruš primárnost ostatních
    if data.get('is_primary'):
        db.execute("UPDATE party_contacts SET is_primary = 0 WHERE party_id = ?", (party_id,))
    
    db.execute(
        "INSERT INTO party_contacts (party_id, name, role, email, phone, is_primary, note) VALUES (?,?,?,?,?,?,?)",
        (party_id, data.get('name',''), data.get('role'), data.get('email'), 
         data.get('phone'), 1 if data.get('is_primary') else 0, data.get('note'))
    )
    db.commit()
    return jsonify({"ok": True})


# DELETE /api/parties/<id>/contacts/<contact_id>
@parties_bp.route('/api/parties/<int:party_id>/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(party_id, contact_id):
    db = get_db()
    db.execute("DELETE FROM party_contacts WHERE id = ? AND party_id = ?", (contact_id, party_id))
    db.commit()
    return jsonify({"ok": True})


# POST /api/parties/<id>/interactions — přidat interakci
@parties_bp.route('/api/parties/<int:party_id>/interactions', methods=['POST'])
def add_interaction(party_id):
    db = get_db()
    data = request.json or {}
    db.execute(
        "INSERT INTO party_interactions (party_id, type, summary, date, created_by) VALUES (?,?,?,?,?)",
        (party_id, data.get('type', 'NOTE'), data.get('summary', ''), data.get('date'), data.get('created_by'))
    )
    db.commit()
    return jsonify({"ok": True})


# DELETE /api/parties/<id>/interactions/<interaction_id>
@parties_bp.route('/api/parties/<int:party_id>/interactions/<int:interaction_id>', methods=['DELETE'])
def delete_interaction(party_id, interaction_id):
    db = get_db()
    db.execute("DELETE FROM party_interactions WHERE id = ? AND party_id = ?", (interaction_id, party_id))
    db.commit()
    return jsonify({"ok": True})


# GET /api/parties/stats — statistiky pro dashboard
@parties_bp.route('/api/parties/stats', methods=['GET'])
def parties_stats():
    db = get_db()
    
    total = db.execute("SELECT COUNT(*) FROM parties").fetchone()[0]
    active = db.execute("SELECT COUNT(*) FROM parties WHERE status = 'ACTIVE'").fetchone()[0]
    strategic = db.execute("SELECT COUNT(*) FROM parties WHERE tier = 'STRATEGIC'").fetchone()[0]
    leads = db.execute("SELECT COUNT(*) FROM parties WHERE status = 'LEAD'").fetchone()[0]
    revenue = db.execute("SELECT SUM(total_revenue) FROM parties").fetchone()[0] or 0
    
    return jsonify({
        "total": total, "active": active, "strategic": strategic, 
        "leads": leads, "total_revenue": revenue
    })


# POST /api/parties/<id>/recalculate — přepočítat statistiky
@parties_bp.route('/api/parties/<int:party_id>/recalculate', methods=['POST'])
def recalculate_party_stats(party_id):
    """Zavolej po vytvoření/úpravě/smazání zakázky"""
    db = get_db()
    
    stats = db.execute("""
        SELECT 
            COUNT(*) as total_jobs,
            SUM(COALESCE(estimated_value, 0)) as total_revenue,
            MAX(created_at) as last_job_date
        FROM jobs WHERE party_id = ?
    """, (party_id,)).fetchone()
    
    if stats:
        db.execute("""
            UPDATE parties SET 
                total_jobs = ?,
                total_revenue = ?,
                last_job_date = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (stats['total_jobs'] or 0, stats['total_revenue'] or 0, stats['last_job_date'], party_id))
        db.commit()
    
    return jsonify({"ok": True})
