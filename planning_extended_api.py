"""
Planning Extended API - All New Features
Nursery, Recurring, Materials, Photos, etc.
"""
from flask import jsonify, request, session
from datetime import datetime, date, timedelta
import json
import os

get_db = None

# ================================================================
# 1. NURSERY - Trvalkové školka 🌸
# ================================================================

def get_nursery_overview():
    """GET /api/nursery/overview"""
    try:
        db = get_db()
        
        # Stats
        stats = db.execute("""
            SELECT 
                COUNT(*) as total_plants,
                SUM(CASE WHEN stage='prodejní' THEN quantity ELSE 0 END) as ready_for_sale,
                SUM(CASE WHEN stage='sazenice' THEN quantity ELSE 0 END) as growing,
                SUM(CASE WHEN status='dead' THEN quantity ELSE 0 END) as dead
            FROM nursery_plants
            WHERE status='active'
        """).fetchone()
        
        # Plants by stage
        by_stage = db.execute("""
            SELECT stage, COUNT(*) as count, SUM(quantity) as total_qty
            FROM nursery_plants
            WHERE status='active'
            GROUP BY stage
        """).fetchall()
        
        # Watering today
        watering_today = db.execute("""
            SELECT np.id, np.species, np.location, np.quantity
            FROM nursery_plants np
            JOIN nursery_watering_schedule nws ON np.id = nws.plant_id
            WHERE nws.next_watering <= date('now')
            AND np.status='active'
        """).fetchall()
        
        # Low stock alerts
        low_stock = db.execute("""
            SELECT * FROM nursery_plants
            WHERE quantity < 10 AND stage='prodejní' AND status='active'
            ORDER BY quantity ASC
        """).fetchall()
        
        return jsonify({
            'success': True,
            'stats': dict(stats) if stats else {},
            'by_stage': [dict(s) for s in by_stage],
            'watering_today': [dict(w) for w in watering_today],
            'low_stock': [dict(l) for l in low_stock]
        })
    except Exception as e:
        print(f"[ERROR] Nursery overview: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def get_nursery_plants():
    """GET /api/nursery/plants"""
    try:
        db = get_db()
        stage = request.args.get('stage')
        
        query = "SELECT * FROM nursery_plants WHERE status='active'"
        params = []
        if stage:
            query += " AND stage = ?"
            params.append(stage)
        query += " ORDER BY species, variety"
        
        plants = db.execute(query, params).fetchall()
        return jsonify({
            'success': True,
            'plants': [dict(p) for p in plants]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_nursery_plant():
    """POST /api/nursery/plants"""
    try:
        data = request.json
        db = get_db()
        
        cursor = db.execute("""
            INSERT INTO nursery_plants 
            (species, variety, quantity, stage, location, planted_date, 
             purchase_price, selling_price, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['species'],
            data.get('variety'),
            data.get('quantity', 0),
            data.get('stage', 'semínko'),
            data.get('location'),
            data.get('planted_date'),
            data.get('purchase_price'),
            data.get('selling_price'),
            data.get('notes')
        ))
        db.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def log_watering():
    """POST /api/nursery/watering"""
    try:
        data = request.json
        db = get_db()
        
        # Get user_id from session - with fallback
        user_id = session.get('user_id', 1)  # Default to 1 if no session
        
        # Log watering
        db.execute("""
            INSERT INTO nursery_watering_log
            (plant_id, watered_date, amount_liters, watered_by, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data['plant_id'],
            data.get('date', date.today().isoformat()),
            data.get('amount'),
            user_id,
            data.get('notes')
        ))
        
        # Update schedule
        db.execute("""
            UPDATE nursery_watering_schedule
            SET last_watered = ?,
                next_watering = date(?, '+' || frequency_days || ' days')
            WHERE plant_id = ?
        """, (
            data.get('date', date.today().isoformat()),
            data.get('date', date.today().isoformat()),
            data['plant_id']
        ))
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# 2. RECURRING TASKS 🔄
# ================================================================

def get_recurring_templates():
    """GET /api/recurring/templates"""
    try:
        db = get_db()
        templates = db.execute("""
            SELECT rt.*, j.name as job_name, e.name as assigned_name
            FROM recurring_task_templates rt
            LEFT JOIN jobs j ON rt.job_id = j.id
            LEFT JOIN employees e ON rt.assigned_to = e.id
            WHERE rt.is_active = 1
            ORDER BY j.name, rt.title
        """).fetchall()
        
        return jsonify({
            'success': True,
            'templates': [dict(t) for t in templates]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_recurring_template():
    """POST /api/recurring/templates"""
    try:
        data = request.json
        db = get_db()
        user_id = session.get('user_id', 1)  # Fallback to 1
        
        cursor = db.execute("""
            INSERT INTO recurring_task_templates
            (title, description, job_id, frequency, frequency_value,
             day_of_week, start_date, assigned_to, estimated_hours, 
             checklist, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['title'],
            data.get('description'),
            data.get('job_id'),
            data['frequency'],
            data.get('frequency_value', 1),
            data.get('day_of_week'),
            data['start_date'],
            data.get('assigned_to'),
            data.get('estimated_hours'),
            json.dumps(data.get('checklist', [])),
            user_id
        ))
        db.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_recurring_tasks():
    """POST /api/recurring/generate - Generate tasks for next period"""
    try:
        db = get_db()
        user_id = session.get('user_id', 1)  # Fallback to 1
        
        # Get active templates
        templates = db.execute("""
            SELECT * FROM recurring_task_templates
            WHERE is_active = 1
            AND (end_date IS NULL OR end_date >= date('now'))
        """).fetchall()
        
        generated_count = 0
        today = date.today()
        
        for template in templates:
            # Calculate next occurrence
            next_date = calculate_next_occurrence(
                template['start_date'],
                template['frequency'],
                template['frequency_value'],
                template['day_of_week']
            )
            
            if not next_date or next_date > today + timedelta(days=30):
                continue
            
            # Check if already generated
            existing = db.execute("""
                SELECT id FROM recurring_task_instances
                WHERE template_id = ? AND scheduled_date = ?
            """, (template['id'], next_date.isoformat())).fetchone()
            
            if existing:
                continue
            
            # Create task
            task_cursor = db.execute("""
                INSERT INTO tasks
                (title, description, job_id, employee_id, due_date, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                template['title'],
                template['description'],
                template['job_id'],
                template['assigned_to'],
                next_date.isoformat(),
                user_id
            ))
            
            # Record instance
            db.execute("""
                INSERT INTO recurring_task_instances
                (template_id, task_id, scheduled_date, status, generated_at)
                VALUES (?, ?, ?, 'generated', datetime('now'))
            """, (template['id'], task_cursor.lastrowid, next_date.isoformat()))
            
            generated_count += 1
        
        db.commit()
        return jsonify({'success': True, 'generated': generated_count})
    except Exception as e:
        print(f"[ERROR] Generate recurring: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def calculate_next_occurrence(start_date, frequency, frequency_value, day_of_week):
    """Calculate next occurrence date"""
    start = datetime.fromisoformat(start_date).date() if isinstance(start_date, str) else start_date
    today = date.today()
    
    if frequency == 'daily':
        next_date = today + timedelta(days=frequency_value)
    elif frequency == 'weekly':
        days_ahead = day_of_week - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7 * frequency_value
        next_date = today + timedelta(days=days_ahead)
    elif frequency == 'monthly':
        next_date = today.replace(day=1) + timedelta(days=32)
        next_date = next_date.replace(day=1)
    else:
        return None
    
    return next_date if next_date >= start else None

# ================================================================
# 3. MATERIALS 📦
# ================================================================

def get_materials():
    """GET /api/materials"""
    try:
        db = get_db()
        materials = db.execute("""
            SELECT * FROM materials
            ORDER BY category, name
        """).fetchall()
        
        # Add alert flag
        result = []
        for m in materials:
            m_dict = dict(m)
            m_dict['low_stock_alert'] = m['current_stock'] < m['min_stock']
            result.append(m_dict)
        
        return jsonify({'success': True, 'materials': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_material():
    """POST /api/materials"""
    try:
        data = request.json
        db = get_db()
        
        cursor = db.execute("""
            INSERT INTO materials
            (name, category, unit, current_stock, min_stock, unit_price, supplier, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['name'],
            data.get('category'),
            data['unit'],
            data.get('current_stock', 0),
            data.get('min_stock', 0),
            data.get('unit_price'),
            data.get('supplier'),
            data.get('location')
        ))
        db.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def update_material():
    """PUT /api/materials/<id>"""
    try:
        material_id = request.view_args.get('material_id')
        data = request.json
        db = get_db()
        
        db.execute("""
            UPDATE materials
            SET name = ?, category = ?, unit = ?, current_stock = ?,
                min_stock = ?, unit_price = ?, supplier = ?, location = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data['name'],
            data.get('category'),
            data['unit'],
            data.get('current_stock', 0),
            data.get('min_stock', 0),
            data.get('unit_price'),
            data.get('supplier'),
            data.get('location'),
            material_id
        ))
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def add_material_movement():
    """POST /api/materials/movement"""
    try:
        data = request.json
        db = get_db()
        user_id = session.get('user_id', 1)  # Fallback to 1
        
        # Record movement
        db.execute("""
            INSERT INTO material_movements
            (material_id, movement_type, quantity, unit_price, total_price,
             job_id, task_id, movement_date, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['material_id'],
            data['movement_type'],
            data['quantity'],
            data.get('unit_price'),
            data.get('total_price'),
            data.get('job_id'),
            data.get('task_id'),
            data.get('movement_date', date.today().isoformat()),
            data.get('notes'),
            user_id
        ))
        
        # Update stock
        if data['movement_type'] == 'in':
            db.execute("""
                UPDATE materials
                SET current_stock = current_stock + ?
                WHERE id = ?
            """, (data['quantity'], data['material_id']))
        elif data['movement_type'] == 'out':
            db.execute("""
                UPDATE materials
                SET current_stock = current_stock - ?
                WHERE id = ?
            """, (data['quantity'], data['material_id']))
        
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_material_movements():
    """GET /api/materials/movements"""
    try:
        db = get_db()
        movements = db.execute("""
            SELECT mm.*, m.name as material_name, m.unit, j.name as job_name
            FROM material_movements mm
            LEFT JOIN materials m ON mm.material_id = m.id
            LEFT JOIN jobs j ON mm.job_id = j.id
            ORDER BY mm.movement_date DESC, mm.created_at DESC
            LIMIT 100
        """).fetchall()
        
        return jsonify({
            'success': True,
            'movements': [dict(m) for m in movements]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ================================================================
# 4. PHOTOS 📸
# ================================================================

def upload_task_photo():
    """POST /api/tasks/<task_id>/photos"""
    try:
        task_id = request.view_args.get('task_id')
        file = request.files.get('photo')
        photo_type = request.form.get('type', 'progress')
        caption = request.form.get('caption')
        
        if not file:
            return jsonify({'success': False, 'error': 'No file'}), 400
        
        # Save file
        upload_dir = 'uploads/task_photos'
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Save to DB
        db = get_db()
        user_id = session.get('user_id', 1)  # Fallback to 1
        
        db.execute("""
            INSERT INTO task_photos
            (task_id, photo_type, file_path, file_name, caption, uploaded_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, photo_type, filepath, filename, caption, user_id))
        db.commit()
        
        return jsonify({'success': True, 'file_path': filepath})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_task_photos(task_id):
    """GET /api/tasks/<task_id>/photos"""
    try:
        db = get_db()
        photos = db.execute("""
            SELECT tp.*, e.name as uploaded_by_name
            FROM task_photos tp
            LEFT JOIN users u ON tp.uploaded_by = u.id
            LEFT JOIN employees e ON u.employee_id = e.id
            WHERE tp.task_id = ?
            ORDER BY tp.created_at DESC
        """, (task_id,)).fetchall()
        
        return jsonify({
            'success': True,
            'photos': [dict(p) for p in photos]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Placeholder functions for other features
def get_plant_species(): 
    return jsonify({'success': True, 'species': []})

def get_maintenance_contracts():
    return jsonify({'success': True, 'contracts': []})

def get_seasonal_tasks():
    return jsonify({'success': True, 'tasks': []})
