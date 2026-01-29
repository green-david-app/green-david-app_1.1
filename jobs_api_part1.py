"""
GREEN DAVID - Jobs Extended API
================================
Flask API endpointy pro rozšířenou správu zakázek

Tento soubor přidej do main.py nebo importuj jako modul
"""

from flask import jsonify, request
from functools import wraps
import json
from datetime import datetime, date

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_db():
    """Helper pro získání DB connection"""
    import sqlite3
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def require_auth(f):
    """Decorator pro autentizaci"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implementuj autentizaci podle tvého systému
        # user = get_current_user()
        # if not user:
        #     return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

def json_serial(obj):
    """JSON serializer pro datetime objekty"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def dict_from_row(row):
    """Převede sqlite3.Row na dict"""
    if row is None:
        return None
    return dict(zip(row.keys(), row))

# ============================================================================
# 1. JOB DETAIL - Kompletní info o zakázce
# ============================================================================

@app.route('/api/jobs/<int:job_id>/complete', methods=['GET'])
@require_auth
def get_job_complete(job_id):
    """
    Získá kompletní informace o zakázce včetně všech souvisejících dat
    
    Returns:
        {
            "job": {...},
            "client": {...},
            "location": {...},
            "milestones": [...],
            "materials": [...],
            "equipment": [...],
            "team": [...],
            "subcontractors": [...],
            "risks": [...],
            "communications": [...],
            "change_requests": [...],
            "payments": [...],
            "documents": [...],
            "photos": {...},
            "metrics": {...}
        }
    """
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Základní info o zakázce
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job = dict_from_row(cursor.fetchone())
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Klient
        cursor.execute("SELECT * FROM job_clients WHERE job_id = ?", (job_id,))
        client = dict_from_row(cursor.fetchone())
        
        # Lokace
        cursor.execute("SELECT * FROM job_locations WHERE job_id = ?", (job_id,))
        location = dict_from_row(cursor.fetchone())
        
        # Milníky
        cursor.execute("""
            SELECT * FROM job_milestones 
            WHERE job_id = ? 
            ORDER BY order_num, planned_date
        """, (job_id,))
        milestones = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Materiál
        cursor.execute("""
            SELECT * FROM job_materials 
            WHERE job_id = ? 
            ORDER BY created_at DESC
        """, (job_id,))
        materials = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Technika
        cursor.execute("""
            SELECT * FROM job_equipment 
            WHERE job_id = ? 
            ORDER BY date_from
        """, (job_id,))
        equipment = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Tým
        cursor.execute("""
            SELECT jta.*, e.name as employee_name, e.position
            FROM job_team_assignments jta
            LEFT JOIN employees e ON jta.employee_id = e.id
            WHERE jta.job_id = ? AND jta.is_active = 1
            ORDER BY jta.role
        """, (job_id,))
        team = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Externí dodavatelé
        cursor.execute("""
            SELECT * FROM job_subcontractors 
            WHERE job_id = ? 
            ORDER BY status, name
        """, (job_id,))
        subcontractors = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Rizika
        cursor.execute("""
            SELECT * FROM job_risks 
            WHERE job_id = ? AND status != 'closed'
            ORDER BY 
                CASE probability 
                    WHEN 'high' THEN 3 
                    WHEN 'medium' THEN 2 
                    ELSE 1 
                END * 
                CASE impact 
                    WHEN 'critical' THEN 4
                    WHEN 'high' THEN 3 
                    WHEN 'medium' THEN 2 
                    ELSE 1 
                END DESC
        """, (job_id,))
        risks = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Komunikace (posledních 20)
        cursor.execute("""
            SELECT jc.*, u.username as by_user_name
            FROM job_communications jc
            LEFT JOIN users u ON jc.by_user_id = u.id
            WHERE jc.job_id = ? 
            ORDER BY jc.communication_date DESC
            LIMIT 20
        """, (job_id,))
        communications = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Change requests (aktivní)
        cursor.execute("""
            SELECT * FROM job_change_requests 
            WHERE job_id = ? AND status IN ('pending', 'approved')
            ORDER BY 
                CASE urgency 
                    WHEN 'critical' THEN 4
                    WHEN 'high' THEN 3 
                    WHEN 'medium' THEN 2 
                    ELSE 1 
                END DESC,
                requested_date DESC
        """, (job_id,))
        change_requests = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Platby
        cursor.execute("""
            SELECT * FROM job_payments 
            WHERE job_id = ? 
            ORDER BY planned_date
        """, (job_id,))
        payments = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Dokumenty
        cursor.execute("""
            SELECT * FROM job_documents 
            WHERE job_id = ? AND is_latest = 1
            ORDER BY type, created_at DESC
        """, (job_id,))
        documents = [dict_from_row(row) for row in cursor.fetchall()]
        
        # Fotky (seskupené podle fází)
        cursor.execute("""
            SELECT * FROM job_photos 
            WHERE job_id = ? AND phase = 'before'
            ORDER BY taken_date
        """, (job_id,))
        photos_before = [dict_from_row(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT * FROM job_photos 
            WHERE job_id = ? AND phase = 'progress'
            ORDER BY taken_date DESC
            LIMIT 50
        """, (job_id,))
        photos_progress = [dict_from_row(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT * FROM job_photos 
            WHERE job_id = ? AND phase = 'after'
            ORDER BY taken_date DESC
        """, (job_id,))
        photos_after = [dict_from_row(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT * FROM job_photos 
            WHERE job_id = ? AND phase = 'issue'
            ORDER BY taken_date DESC
        """, (job_id,))
        photos_issues = [dict_from_row(row) for row in cursor.fetchall()]
        
        photos = {
            "before": photos_before,
            "progress": photos_progress,
            "after": photos_after,
            "issues": photos_issues,
            "total": len(photos_before) + len(photos_progress) + len(photos_after) + len(photos_issues)
        }
        
        # Metriky (nejnovější)
        cursor.execute("""
            SELECT * FROM job_metrics 
            WHERE job_id = ? 
            ORDER BY calculated_at DESC 
            LIMIT 1
        """, (job_id,))
        metrics = dict_from_row(cursor.fetchone())
        
        conn.close()
        
        # Sestavení odpovědi
        result = {
            "job": job,
            "client": client,
            "location": location,
            "milestones": milestones,
            "materials": materials,
            "equipment": equipment,
            "team": team,
            "subcontractors": subcontractors,
            "risks": risks,
            "communications": communications,
            "change_requests": change_requests,
            "payments": payments,
            "documents": documents,
            "photos": photos,
            "metrics": metrics,
            
            # Summary stats
            "summary": {
                "milestones_count": len(milestones),
                "milestones_completed": len([m for m in milestones if m.get('status') == 'completed']),
                "materials_count": len(materials),
                "materials_delivered": len([m for m in materials if m.get('delivery_status') == 'delivered']),
                "team_size": len(team),
                "active_risks": len(risks),
                "pending_changes": len([c for c in change_requests if c.get('status') == 'pending']),
                "photos_total": photos['total']
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 2. CLIENT MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/client', methods=['GET', 'POST', 'PUT'])
@require_auth
def manage_job_client(job_id):
    """
    GET: Získá info o klientovi
    POST: Vytvoří nového klienta pro zakázku
    PUT: Aktualizuje info o klientovi
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("SELECT * FROM job_clients WHERE job_id = ?", (job_id,))
            client = dict_from_row(cursor.fetchone())
            return jsonify(client if client else {}), 200
            
        elif request.method in ['POST', 'PUT']:
            data = request.get_json()
            
            # Validace
            if not data.get('name'):
                return jsonify({"error": "Name is required"}), 400
            
            # Check if exists
            cursor.execute("SELECT id FROM job_clients WHERE job_id = ?", (job_id,))
            exists = cursor.fetchone()
            
            if request.method == 'POST' and exists:
                return jsonify({"error": "Client already exists for this job"}), 400
            
            if request.method == 'PUT' and not exists:
                return jsonify({"error": "Client not found"}), 404
            
            # INSERT or UPDATE
            if exists:
                cursor.execute("""
                    UPDATE job_clients SET
                        name = ?,
                        company = ?,
                        ico = ?,
                        dic = ?,
                        email = ?,
                        phone = ?,
                        phone_secondary = ?,
                        preferred_contact = ?,
                        billing_street = ?,
                        billing_city = ?,
                        billing_zip = ?,
                        billing_country = ?,
                        payment_rating = ?,
                        notes = ?
                    WHERE job_id = ?
                """, (
                    data.get('name'),
                    data.get('company'),
                    data.get('ico'),
                    data.get('dic'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('phone_secondary'),
                    data.get('preferred_contact', 'phone'),
                    data.get('billing_street'),
                    data.get('billing_city'),
                    data.get('billing_zip'),
                    data.get('billing_country', 'CZ'),
                    data.get('payment_rating', 'good'),
                    data.get('notes'),
                    job_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO job_clients (
                        job_id, name, company, ico, dic, email, phone, 
                        phone_secondary, preferred_contact, billing_street,
                        billing_city, billing_zip, billing_country,
                        payment_rating, notes, client_since
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'))
                """, (
                    job_id,
                    data.get('name'),
                    data.get('company'),
                    data.get('ico'),
                    data.get('dic'),
                    data.get('email'),
                    data.get('phone'),
                    data.get('phone_secondary'),
                    data.get('preferred_contact', 'phone'),
                    data.get('billing_street'),
                    data.get('billing_city'),
                    data.get('billing_zip'),
                    data.get('billing_country', 'CZ'),
                    data.get('payment_rating', 'good'),
                    data.get('notes')
                ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "message": "Client saved"}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 3. LOCATION MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/location', methods=['GET', 'POST', 'PUT'])
@require_auth
def manage_job_location(job_id):
    """Správa lokace zakázky"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("SELECT * FROM job_locations WHERE job_id = ?", (job_id,))
            location = dict_from_row(cursor.fetchone())
            return jsonify(location if location else {}), 200
            
        elif request.method in ['POST', 'PUT']:
            data = request.get_json()
            
            # Check if exists
            cursor.execute("SELECT id FROM job_locations WHERE job_id = ?", (job_id,))
            exists = cursor.fetchone()
            
            if request.method == 'POST' and exists:
                return jsonify({"error": "Location already exists"}), 400
            
            if request.method == 'PUT' and not exists:
                return jsonify({"error": "Location not found"}), 404
            
            if exists:
                cursor.execute("""
                    UPDATE job_locations SET
                        street = ?, city = ?, zip = ?, country = ?,
                        lat = ?, lng = ?,
                        parking = ?, parking_notes = ?,
                        access_notes = ?, gate_code = ?, key_location = ?,
                        has_electricity = ?, has_water = ?, has_toilet = ?,
                        neighbors_info = ?, noise_restrictions = ?
                    WHERE job_id = ?
                """, (
                    data.get('street'), data.get('city'), data.get('zip'), data.get('country', 'CZ'),
                    data.get('lat'), data.get('lng'),
                    data.get('parking'), data.get('parking_notes'),
                    data.get('access_notes'), data.get('gate_code'), data.get('key_location'),
                    data.get('has_electricity', False), data.get('has_water', False), data.get('has_toilet', False),
                    data.get('neighbors_info'), data.get('noise_restrictions'),
                    job_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO job_locations (
                        job_id, street, city, zip, country, lat, lng,
                        parking, parking_notes, access_notes, gate_code, key_location,
                        has_electricity, has_water, has_toilet,
                        neighbors_info, noise_restrictions
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id, data.get('street'), data.get('city'), data.get('zip'), data.get('country', 'CZ'),
                    data.get('lat'), data.get('lng'),
                    data.get('parking'), data.get('parking_notes'),
                    data.get('access_notes'), data.get('gate_code'), data.get('key_location'),
                    data.get('has_electricity', False), data.get('has_water', False), data.get('has_toilet', False),
                    data.get('neighbors_info'), data.get('noise_restrictions')
                ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "message": "Location saved"}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 4. MILESTONES MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/milestones', methods=['GET', 'POST'])
@require_auth
def manage_milestones(job_id):
    """Seznam a vytvoření milníků"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_milestones 
                WHERE job_id = ? 
                ORDER BY order_num, planned_date
            """, (job_id,))
            milestones = [dict_from_row(row) for row in cursor.fetchall()]
            return jsonify(milestones), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('name'):
                return jsonify({"error": "Name is required"}), 400
            
            # Get next order_num
            cursor.execute("""
                SELECT COALESCE(MAX(order_num), 0) + 1 as next_order
                FROM job_milestones WHERE job_id = ?
            """, (job_id,))
            next_order = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO job_milestones (
                    job_id, name, description, planned_date, 
                    status, order_num, depends_on, reminder_days_before
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('name'),
                data.get('description'),
                data.get('planned_date'),
                data.get('status', 'pending'),
                data.get('order_num', next_order),
                data.get('depends_on'),
                data.get('reminder_days_before', 3)
            ))
            
            milestone_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": milestone_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/milestones/<int:milestone_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_milestone(job_id, milestone_id):
    """Detail, update, delete milníku"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_milestones 
                WHERE id = ? AND job_id = ?
            """, (milestone_id, job_id))
            milestone = dict_from_row(cursor.fetchone())
            
            if not milestone:
                return jsonify({"error": "Milestone not found"}), 404
            
            return jsonify(milestone), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            cursor.execute("""
                UPDATE job_milestones SET
                    name = ?,
                    description = ?,
                    planned_date = ?,
                    actual_date = ?,
                    status = ?,
                    completion_percent = ?,
                    order_num = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND job_id = ?
            """, (
                data.get('name'),
                data.get('description'),
                data.get('planned_date'),
                data.get('actual_date'),
                data.get('status'),
                data.get('completion_percent', 0),
                data.get('order_num'),
                milestone_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            cursor.execute("""
                DELETE FROM job_milestones 
                WHERE id = ? AND job_id = ?
            """, (milestone_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Pokračování v dalším souboru...
