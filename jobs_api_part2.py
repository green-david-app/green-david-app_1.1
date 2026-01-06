"""
GREEN DAVID - Jobs Extended API - Part 2
=========================================
Materials, Equipment, Team Management
"""

# ============================================================================
# 5. MATERIALS MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/materials', methods=['GET', 'POST'])
@require_auth
def manage_materials(job_id):
    """Seznam a vytvoření materiálu"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            # Filters
            status = request.args.get('status')  # 'pending', 'delivered', etc.
            
            query = "SELECT * FROM job_materials WHERE job_id = ?"
            params = [job_id]
            
            if status:
                query += " AND delivery_status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            materials = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Calculate totals
            total_cost = sum(m.get('total_price', 0) or 0 for m in materials)
            ordered_count = len([m for m in materials if m.get('ordered')])
            delivered_count = len([m for m in materials if m.get('delivery_status') == 'delivered'])
            
            return jsonify({
                "materials": materials,
                "summary": {
                    "total": len(materials),
                    "ordered": ordered_count,
                    "delivered": delivered_count,
                    "total_cost": total_cost,
                    "ordered_percent": round(ordered_count / len(materials) * 100) if materials else 0,
                    "delivered_percent": round(delivered_count / len(materials) * 100) if materials else 0
                }
            }), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('name'):
                return jsonify({"error": "Name is required"}), 400
            
            # Auto-calculate total_price
            quantity = float(data.get('quantity', 0))
            price_per_unit = float(data.get('price_per_unit', 0))
            total_price = quantity * price_per_unit
            
            cursor.execute("""
                INSERT INTO job_materials (
                    job_id, name, category, quantity, unit,
                    price_per_unit, total_price,
                    supplier, supplier_contact,
                    ordered, order_date, order_number,
                    delivery_date, delivery_status,
                    storage_location, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('name'),
                data.get('category'),
                quantity,
                data.get('unit', 'ks'),
                price_per_unit,
                total_price,
                data.get('supplier'),
                data.get('supplier_contact'),
                data.get('ordered', False),
                data.get('order_date'),
                data.get('order_number'),
                data.get('delivery_date'),
                data.get('delivery_status', 'pending'),
                data.get('storage_location'),
                data.get('notes')
            ))
            
            material_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": material_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/materials/<int:material_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_material(job_id, material_id):
    """Detail, update, delete materiálu"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_materials 
                WHERE id = ? AND job_id = ?
            """, (material_id, job_id))
            material = dict_from_row(cursor.fetchone())
            
            if not material:
                return jsonify({"error": "Material not found"}), 404
            
            return jsonify(material), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Auto-calculate total_price
            quantity = float(data.get('quantity', 0))
            price_per_unit = float(data.get('price_per_unit', 0))
            total_price = quantity * price_per_unit
            
            cursor.execute("""
                UPDATE job_materials SET
                    name = ?,
                    category = ?,
                    quantity = ?,
                    unit = ?,
                    price_per_unit = ?,
                    total_price = ?,
                    supplier = ?,
                    supplier_contact = ?,
                    ordered = ?,
                    order_date = ?,
                    order_number = ?,
                    delivery_date = ?,
                    delivery_status = ?,
                    actual_delivery_date = ?,
                    storage_location = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND job_id = ?
            """, (
                data.get('name'),
                data.get('category'),
                quantity,
                data.get('unit'),
                price_per_unit,
                total_price,
                data.get('supplier'),
                data.get('supplier_contact'),
                data.get('ordered'),
                data.get('order_date'),
                data.get('order_number'),
                data.get('delivery_date'),
                data.get('delivery_status'),
                data.get('actual_delivery_date'),
                data.get('storage_location'),
                data.get('notes'),
                material_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            cursor.execute("""
                DELETE FROM job_materials 
                WHERE id = ? AND job_id = ?
            """, (material_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Quick action: Mark material as ordered
@app.route('/api/jobs/<int:job_id>/materials/<int:material_id>/order', methods=['POST'])
@require_auth
def mark_material_ordered(job_id, material_id):
    """Označí materiál jako objednaný"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        data = request.get_json() or {}
        
        cursor.execute("""
            UPDATE job_materials SET
                ordered = 1,
                order_date = ?,
                order_number = ?,
                delivery_status = 'confirmed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND job_id = ?
        """, (
            data.get('order_date', datetime.now().date().isoformat()),
            data.get('order_number'),
            material_id,
            job_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Material marked as ordered"}), 200
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Quick action: Mark material as delivered
@app.route('/api/jobs/<int:job_id>/materials/<int:material_id>/deliver', methods=['POST'])
@require_auth
def mark_material_delivered(job_id, material_id):
    """Označí materiál jako dodaný"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        data = request.get_json() or {}
        
        cursor.execute("""
            UPDATE job_materials SET
                delivery_status = 'delivered',
                actual_delivery_date = ?,
                storage_location = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND job_id = ?
        """, (
            data.get('actual_delivery_date', datetime.now().date().isoformat()),
            data.get('storage_location'),
            material_id,
            job_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Material marked as delivered"}), 200
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 6. EQUIPMENT MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/equipment', methods=['GET', 'POST'])
@require_auth
def manage_equipment(job_id):
    """Seznam a vytvoření techniky"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_equipment 
                WHERE job_id = ? 
                ORDER BY date_from, status
            """, (job_id,))
            equipment = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Calculate totals
            total_cost = sum(e.get('total_cost', 0) or 0 for e in equipment)
            reserved_count = len([e for e in equipment if e.get('status') in ['reserved', 'in_use']])
            
            return jsonify({
                "equipment": equipment,
                "summary": {
                    "total": len(equipment),
                    "reserved": reserved_count,
                    "total_cost": total_cost
                }
            }), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('name'):
                return jsonify({"error": "Name is required"}), 400
            
            # Auto-calculate total_cost
            days_needed = int(data.get('days_needed', 0))
            cost_per_day = float(data.get('cost_per_day', 0))
            total_cost = days_needed * cost_per_day
            
            cursor.execute("""
                INSERT INTO job_equipment (
                    job_id, name, type, days_needed, date_from, date_to,
                    cost_per_day, total_cost,
                    supplier, supplier_contact,
                    reservation_date, reservation_confirmed,
                    status, owned, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('name'),
                data.get('type'),
                days_needed,
                data.get('date_from'),
                data.get('date_to'),
                cost_per_day,
                total_cost,
                data.get('supplier'),
                data.get('supplier_contact'),
                data.get('reservation_date'),
                data.get('reservation_confirmed', False),
                data.get('status', 'needed'),
                data.get('owned', False),
                data.get('notes')
            ))
            
            equipment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": equipment_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/equipment/<int:equipment_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_equipment_item(job_id, equipment_id):
    """Detail, update, delete techniky"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_equipment 
                WHERE id = ? AND job_id = ?
            """, (equipment_id, job_id))
            equipment = dict_from_row(cursor.fetchone())
            
            if not equipment:
                return jsonify({"error": "Equipment not found"}), 404
            
            return jsonify(equipment), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Auto-calculate total_cost
            days_needed = int(data.get('days_needed', 0))
            cost_per_day = float(data.get('cost_per_day', 0))
            total_cost = days_needed * cost_per_day
            
            cursor.execute("""
                UPDATE job_equipment SET
                    name = ?,
                    type = ?,
                    days_needed = ?,
                    date_from = ?,
                    date_to = ?,
                    cost_per_day = ?,
                    total_cost = ?,
                    supplier = ?,
                    supplier_contact = ?,
                    reservation_date = ?,
                    reservation_confirmed = ?,
                    status = ?,
                    owned = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND job_id = ?
            """, (
                data.get('name'),
                data.get('type'),
                days_needed,
                data.get('date_from'),
                data.get('date_to'),
                cost_per_day,
                total_cost,
                data.get('supplier'),
                data.get('supplier_contact'),
                data.get('reservation_date'),
                data.get('reservation_confirmed'),
                data.get('status'),
                data.get('owned'),
                data.get('notes'),
                equipment_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            cursor.execute("""
                DELETE FROM job_equipment 
                WHERE id = ? AND job_id = ?
            """, (equipment_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 7. TEAM MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/team', methods=['GET', 'POST'])
@require_auth
def manage_team(job_id):
    """Seznam a přiřazení týmu"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT 
                    jta.*,
                    e.name as employee_name,
                    e.position,
                    e.phone
                FROM job_team_assignments jta
                LEFT JOIN employees e ON jta.employee_id = e.id
                WHERE jta.job_id = ? AND jta.is_active = 1
                ORDER BY jta.role, e.name
            """, (job_id,))
            team = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Calculate stats
            total_hours_planned = sum(t.get('hours_planned', 0) or 0 for t in team)
            total_hours_actual = sum(t.get('hours_actual', 0) or 0 for t in team)
            
            return jsonify({
                "team": team,
                "summary": {
                    "size": len(team),
                    "hours_planned": total_hours_planned,
                    "hours_actual": total_hours_actual,
                    "hours_remaining": total_hours_planned - total_hours_actual
                }
            }), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('employee_id'):
                return jsonify({"error": "Employee ID is required"}), 400
            
            # Check if already assigned
            cursor.execute("""
                SELECT id FROM job_team_assignments 
                WHERE job_id = ? AND employee_id = ? AND is_active = 1
            """, (job_id, data.get('employee_id')))
            
            if cursor.fetchone():
                return jsonify({"error": "Employee already assigned to this job"}), 400
            
            cursor.execute("""
                INSERT INTO job_team_assignments (
                    job_id, employee_id, role,
                    hours_planned, hours_actual,
                    availability, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('employee_id'),
                data.get('role', 'worker'),
                data.get('hours_planned', 0),
                data.get('hours_actual', 0),
                data.get('availability', 'full-time'),
                data.get('notes')
            ))
            
            assignment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": assignment_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/team/<int:assignment_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_team_member(job_id, assignment_id):
    """Detail, update, remove člena týmu"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT 
                    jta.*,
                    e.name as employee_name,
                    e.position,
                    e.phone
                FROM job_team_assignments jta
                LEFT JOIN employees e ON jta.employee_id = e.id
                WHERE jta.id = ? AND jta.job_id = ?
            """, (assignment_id, job_id))
            member = dict_from_row(cursor.fetchone())
            
            if not member:
                return jsonify({"error": "Team member not found"}), 404
            
            return jsonify(member), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            cursor.execute("""
                UPDATE job_team_assignments SET
                    role = ?,
                    hours_planned = ?,
                    hours_actual = ?,
                    availability = ?,
                    notes = ?
                WHERE id = ? AND job_id = ?
            """, (
                data.get('role'),
                data.get('hours_planned'),
                data.get('hours_actual'),
                data.get('availability'),
                data.get('notes'),
                assignment_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            # Soft delete - just mark as inactive
            cursor.execute("""
                UPDATE job_team_assignments SET
                    is_active = 0,
                    removed_date = date('now')
                WHERE id = ? AND job_id = ?
            """, (assignment_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 8. SUBCONTRACTORS MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/subcontractors', methods=['GET', 'POST'])
@require_auth
def manage_subcontractors(job_id):
    """Seznam a vytvoření subdodavatelů"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_subcontractors 
                WHERE job_id = ? 
                ORDER BY status, name
            """, (job_id,))
            subcontractors = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Calculate totals
            total_price = sum(s.get('price', 0) or 0 for s in subcontractors)
            confirmed_count = len([s for s in subcontractors if s.get('status') == 'confirmed'])
            
            return jsonify({
                "subcontractors": subcontractors,
                "summary": {
                    "total": len(subcontractors),
                    "confirmed": confirmed_count,
                    "total_price": total_price
                }
            }), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('name') or not data.get('service'):
                return jsonify({"error": "Name and service are required"}), 400
            
            cursor.execute("""
                INSERT INTO job_subcontractors (
                    job_id, name, company, service,
                    contact_person, phone, email,
                    price, payment_terms,
                    status, start_date, end_date,
                    contract_signed, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('name'),
                data.get('company'),
                data.get('service'),
                data.get('contact_person'),
                data.get('phone'),
                data.get('email'),
                data.get('price'),
                data.get('payment_terms'),
                data.get('status', 'requested'),
                data.get('start_date'),
                data.get('end_date'),
                data.get('contract_signed', False),
                data.get('notes')
            ))
            
            subcontractor_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": subcontractor_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/subcontractors/<int:subcontractor_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_subcontractor(job_id, subcontractor_id):
    """Detail, update, delete subdodavatele"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_subcontractors 
                WHERE id = ? AND job_id = ?
            """, (subcontractor_id, job_id))
            subcontractor = dict_from_row(cursor.fetchone())
            
            if not subcontractor:
                return jsonify({"error": "Subcontractor not found"}), 404
            
            return jsonify(subcontractor), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            cursor.execute("""
                UPDATE job_subcontractors SET
                    name = ?,
                    company = ?,
                    service = ?,
                    contact_person = ?,
                    phone = ?,
                    email = ?,
                    price = ?,
                    payment_terms = ?,
                    status = ?,
                    start_date = ?,
                    end_date = ?,
                    contract_signed = ?,
                    invoice_number = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND job_id = ?
            """, (
                data.get('name'),
                data.get('company'),
                data.get('service'),
                data.get('contact_person'),
                data.get('phone'),
                data.get('email'),
                data.get('price'),
                data.get('payment_terms'),
                data.get('status'),
                data.get('start_date'),
                data.get('end_date'),
                data.get('contract_signed'),
                data.get('invoice_number'),
                data.get('notes'),
                subcontractor_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            cursor.execute("""
                DELETE FROM job_subcontractors 
                WHERE id = ? AND job_id = ?
            """, (subcontractor_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Pokračování v dalším souboru...
