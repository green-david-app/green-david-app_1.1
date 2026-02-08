# Green David App
from flask import Blueprint

documents_bp = Blueprint('documents', __name__)

# Additional routes from main.py
@documents_bp.route("/api/attachments/<path:filename>")
def download_attachment(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

# === COMMENTS API ===
@documents_bp.route("/gd/api/warehouse/items", methods=["GET"])
def gd_api_warehouse_items():
    """Get warehouse items for autocomplete"""
    u, err = require_role(write=False)
    if err:
        return err
    db = get_db()
    
    try:
        search = request.args.get("search", "").strip()
        limit = request.args.get("limit", type=int) or 50
        
        q = "SELECT id, name, sku, category, quantity, unit, unit_price, location FROM warehouse_items WHERE quantity > 0"
        params = []
        
        if search:
            q += " AND (name LIKE ? OR sku LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        q += " ORDER BY name ASC LIMIT ?"
        params.append(limit)
        
        rows = db.execute(q, params).fetchall()
        items = []
        for row in rows:
            items.append({
                "id": row["id"],
                "name": row["name"],
                "sku": row.get("sku"),
                "category": row.get("category"),
                "quantity": float(row["quantity"] or 0),
                "unit": row.get("unit", "ks"),
                "unit_price": float(row.get("unit_price") or 0),
                "location": row.get("location")
            })
        
        return jsonify({"ok": True, "items": items})
    except Exception as e:
        print(f"✗ Error getting warehouse items: {e}")
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

# ----------------- Training Service Functions -----------------

# Additional routes from main.py
@documents_bp.route('/portal')
def client_portal():
    """Serve client portal page."""
    return render_template('client-portal.html')


@documents_bp.route('/api/portal/job')
def api_portal_job():
    """Get job by client code (no auth required)."""
    code = request.args.get('code', '').strip()
    
    if not code:
        return jsonify({'error': 'Code required'}), 400
    
    db = get_db()
    
    # Search by code or client name
    job = db.execute('''
        SELECT * FROM jobs 
        WHERE code = ? OR client LIKE ? OR id = ?
        LIMIT 1
    ''', [code, f'%{code}%', code if code.isdigit() else -1]).fetchone()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    job_dict = dict(job)
    
    # Get task stats
    tasks = db.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as completed
        FROM tasks WHERE job_id = ?
    ''', [job['id']]).fetchone()
    
    job_dict['tasks_total'] = tasks['total'] or 0
    job_dict['tasks_completed'] = tasks['completed'] or 0
    
    # Calculate progress
    if job_dict['tasks_total'] > 0:
        job_dict['progress'] = int((job_dict['tasks_completed'] / job_dict['tasks_total']) * 100)
    else:
        job_dict['progress'] = job.get('progress', 0) or 0
    
    return jsonify(job_dict)


@documents_bp.route('/api/portal/job/<int:job_id>/updates')
def api_portal_updates(job_id):
    """Get job updates/timeline for portal."""
    db = get_db()
    
    # Get completed tasks as updates
    tasks = db.execute('''
        SELECT title, 'Úkol dokončen' as description, 
               COALESCE(updated_at, created_at) as date
        FROM tasks 
        WHERE job_id = ? AND status = 'done'
        ORDER BY date DESC
        LIMIT 10
    ''', [job_id]).fetchall()
    
    updates = [{'title': t['title'], 'description': t['description'], 'date': t['date']} for t in tasks]
    
    # Add job notes as updates if available
    job = db.execute('SELECT note, created_at FROM jobs WHERE id = ?', [job_id]).fetchone()
    if job and job['note']:
        updates.insert(0, {
            'title': 'Poznámka k zakázce',
            'description': job['note'][:200],
            'date': job['created_at']
        })
    
    return jsonify(updates)


@documents_bp.route('/api/portal/job/<int:job_id>/photos')
def api_portal_photos(job_id):
    """Get job photos for portal."""
    db = get_db()
    
    # Check if job_photos table exists
    try:
        photos = db.execute('''
            SELECT url, thumbnail, created_at as date
            FROM job_photos
            WHERE job_id = ?
            ORDER BY created_at DESC
        ''', [job_id]).fetchall()
        
        return jsonify([dict(p) for p in photos])
    except:
        # Table doesn't exist
        return jsonify([])


# ============================================================
# AI ESTIMATE API (for future AI integration)
# ============================================================

