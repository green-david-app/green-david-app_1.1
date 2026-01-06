"""
GREEN DAVID - Jobs Extended API - Part 3
=========================================
Communications, Payments, Photos, Risks, Change Requests
"""

# ============================================================================
# 9. COMMUNICATIONS LOG
# ============================================================================

@app.route('/api/jobs/<int:job_id>/communications', methods=['GET', 'POST'])
@require_auth
def manage_communications(job_id):
    """Log komunikace s klientem"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            limit = request.args.get('limit', 50, type=int)
            type_filter = request.args.get('type')  # 'phone', 'email', etc.
            
            query = """
                SELECT jc.*, u.username as by_user_name
                FROM job_communications jc
                LEFT JOIN users u ON jc.by_user_id = u.id
                WHERE jc.job_id = ?
            """
            params = [job_id]
            
            if type_filter:
                query += " AND jc.type = ?"
                params.append(type_filter)
            
            query += " ORDER BY jc.communication_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            communications = [dict_from_row(row) for row in cursor.fetchall()]
            
            return jsonify(communications), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('summary'):
                return jsonify({"error": "Summary is required"}), 400
            
            # TODO: Get current user ID from session
            user_id = data.get('by_user_id')  # Replace with actual auth
            
            cursor.execute("""
                INSERT INTO job_communications (
                    job_id, communication_date, type, direction,
                    subject, summary, full_content,
                    by_user_id, with_client, participants,
                    outcome, action_items, is_internal, attachments
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('communication_date', datetime.now().isoformat()),
                data.get('type', 'note'),
                data.get('direction', 'internal'),
                data.get('subject'),
                data.get('summary'),
                data.get('full_content'),
                user_id,
                data.get('with_client', True),
                json.dumps(data.get('participants', [])),
                data.get('outcome'),
                json.dumps(data.get('action_items', [])),
                data.get('is_internal', False),
                json.dumps(data.get('attachments', []))
            ))
            
            comm_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": comm_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/communications/<int:comm_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_communication(job_id, comm_id):
    """Detail, update, delete komunikace"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT jc.*, u.username as by_user_name
                FROM job_communications jc
                LEFT JOIN users u ON jc.by_user_id = u.id
                WHERE jc.id = ? AND jc.job_id = ?
            """, (comm_id, job_id))
            comm = dict_from_row(cursor.fetchone())
            
            if not comm:
                return jsonify({"error": "Communication not found"}), 404
            
            return jsonify(comm), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            cursor.execute("""
                UPDATE job_communications SET
                    type = ?,
                    direction = ?,
                    subject = ?,
                    summary = ?,
                    full_content = ?,
                    outcome = ?,
                    action_items = ?,
                    is_internal = ?
                WHERE id = ? AND job_id = ?
            """, (
                data.get('type'),
                data.get('direction'),
                data.get('subject'),
                data.get('summary'),
                data.get('full_content'),
                data.get('outcome'),
                json.dumps(data.get('action_items', [])),
                data.get('is_internal'),
                comm_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            cursor.execute("""
                DELETE FROM job_communications 
                WHERE id = ? AND job_id = ?
            """, (comm_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 10. PAYMENTS MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/payments', methods=['GET', 'POST'])
@require_auth
def manage_payments(job_id):
    """Payment schedule a tracking"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_payments 
                WHERE job_id = ? 
                ORDER BY planned_date
            """, (job_id,))
            payments = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Calculate stats
            total_planned = sum(p.get('amount', 0) or 0 for p in payments)
            total_paid = sum(p.get('paid_amount', 0) or 0 for p in payments if p.get('status') == 'paid')
            total_pending = sum(p.get('amount', 0) or 0 for p in payments if p.get('status') in ['pending', 'sent'])
            overdue = [p for p in payments if p.get('status') == 'overdue']
            
            return jsonify({
                "payments": payments,
                "summary": {
                    "total_planned": total_planned,
                    "total_paid": total_paid,
                    "total_pending": total_pending,
                    "overdue_count": len(overdue),
                    "overdue_amount": sum(p.get('amount', 0) or 0 for p in overdue)
                }
            }), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('amount'):
                return jsonify({"error": "Amount is required"}), 400
            
            cursor.execute("""
                INSERT INTO job_payments (
                    job_id, planned_date, amount, percentage,
                    payment_type, status,
                    invoice_id, invoice_date, invoice_due_date,
                    note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('planned_date'),
                data.get('amount'),
                data.get('percentage'),
                data.get('payment_type', 'progress'),
                data.get('status', 'pending'),
                data.get('invoice_id'),
                data.get('invoice_date'),
                data.get('invoice_due_date'),
                data.get('note')
            ))
            
            payment_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": payment_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/payments/<int:payment_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_payment(job_id, payment_id):
    """Detail, update, delete platby"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT * FROM job_payments 
                WHERE id = ? AND job_id = ?
            """, (payment_id, job_id))
            payment = dict_from_row(cursor.fetchone())
            
            if not payment:
                return jsonify({"error": "Payment not found"}), 404
            
            return jsonify(payment), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            cursor.execute("""
                UPDATE job_payments SET
                    planned_date = ?,
                    amount = ?,
                    percentage = ?,
                    payment_type = ?,
                    status = ?,
                    paid_date = ?,
                    paid_amount = ?,
                    payment_method = ?,
                    invoice_id = ?,
                    invoice_date = ?,
                    invoice_due_date = ?,
                    note = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND job_id = ?
            """, (
                data.get('planned_date'),
                data.get('amount'),
                data.get('percentage'),
                data.get('payment_type'),
                data.get('status'),
                data.get('paid_date'),
                data.get('paid_amount'),
                data.get('payment_method'),
                data.get('invoice_id'),
                data.get('invoice_date'),
                data.get('invoice_due_date'),
                data.get('note'),
                payment_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            cursor.execute("""
                DELETE FROM job_payments 
                WHERE id = ? AND job_id = ?
            """, (payment_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# Quick action: Mark payment as paid
@app.route('/api/jobs/<int:job_id>/payments/<int:payment_id>/mark-paid', methods=['POST'])
@require_auth
def mark_payment_paid(job_id, payment_id):
    """Označí platbu jako zaplacenou"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        data = request.get_json() or {}
        
        cursor.execute("""
            UPDATE job_payments SET
                status = 'paid',
                paid_date = ?,
                paid_amount = amount,
                payment_method = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND job_id = ?
        """, (
            data.get('paid_date', datetime.now().date().isoformat()),
            data.get('payment_method', 'bank_transfer'),
            payment_id,
            job_id
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Payment marked as paid"}), 200
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 11. PHOTOS MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/photos', methods=['GET', 'POST'])
@require_auth
def manage_photos(job_id):
    """Fotodokumentace"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            phase = request.args.get('phase')  # 'before', 'progress', 'after', 'issue'
            limit = request.args.get('limit', 100, type=int)
            
            query = "SELECT * FROM job_photos WHERE job_id = ?"
            params = [job_id]
            
            if phase:
                query += " AND phase = ?"
                params.append(phase)
            
            query += " ORDER BY taken_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            photos = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Count by phase
            cursor.execute("""
                SELECT phase, COUNT(*) as count 
                FROM job_photos 
                WHERE job_id = ? 
                GROUP BY phase
            """, (job_id,))
            counts = {row['phase']: row['count'] for row in cursor.fetchall()}
            
            return jsonify({
                "photos": photos,
                "counts": {
                    "before": counts.get('before', 0),
                    "progress": counts.get('progress', 0),
                    "after": counts.get('after', 0),
                    "issue": counts.get('issue', 0),
                    "total": sum(counts.values())
                }
            }), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('file_path'):
                return jsonify({"error": "File path is required"}), 400
            
            # TODO: Get current user ID from session
            user_id = data.get('taken_by')  # Replace with actual auth
            
            cursor.execute("""
                INSERT INTO job_photos (
                    job_id, file_path, thumbnail_path,
                    phase, milestone_id,
                    caption, description,
                    taken_by, taken_date,
                    location_on_site, lat, lng,
                    related_issue_id, severity, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('file_path'),
                data.get('thumbnail_path'),
                data.get('phase', 'progress'),
                data.get('milestone_id'),
                data.get('caption'),
                data.get('description'),
                user_id,
                data.get('taken_date', datetime.now().isoformat()),
                data.get('location_on_site'),
                data.get('lat'),
                data.get('lng'),
                data.get('related_issue_id'),
                data.get('severity'),
                json.dumps(data.get('tags', []))
            ))
            
            photo_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": photo_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/photos/<int:photo_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_photo(job_id, photo_id):
    """Detail, update, delete fotky"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT jp.*, u.username as taken_by_name
                FROM job_photos jp
                LEFT JOIN users u ON jp.taken_by = u.id
                WHERE jp.id = ? AND jp.job_id = ?
            """, (photo_id, job_id))
            photo = dict_from_row(cursor.fetchone())
            
            if not photo:
                return jsonify({"error": "Photo not found"}), 404
            
            return jsonify(photo), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            cursor.execute("""
                UPDATE job_photos SET
                    phase = ?,
                    milestone_id = ?,
                    caption = ?,
                    description = ?,
                    location_on_site = ?,
                    related_issue_id = ?,
                    severity = ?,
                    tags = ?
                WHERE id = ? AND job_id = ?
            """, (
                data.get('phase'),
                data.get('milestone_id'),
                data.get('caption'),
                data.get('description'),
                data.get('location_on_site'),
                data.get('related_issue_id'),
                data.get('severity'),
                json.dumps(data.get('tags', [])),
                photo_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            # TODO: Also delete actual file from filesystem
            cursor.execute("""
                DELETE FROM job_photos 
                WHERE id = ? AND job_id = ?
            """, (photo_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 12. RISKS MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/risks', methods=['GET', 'POST'])
@require_auth
def manage_risks(job_id):
    """Risk management"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            status = request.args.get('status')
            
            query = "SELECT * FROM job_risks WHERE job_id = ?"
            params = [job_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            else:
                query += " AND status != 'closed'"
            
            # Order by risk score (probability * impact)
            query += """ 
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
            """
            
            cursor.execute(query, params)
            risks = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM job_risks 
                WHERE job_id = ? 
                GROUP BY status
            """, (job_id,))
            counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            return jsonify({
                "risks": risks,
                "counts": counts,
                "active": counts.get('identified', 0) + counts.get('monitoring', 0)
            }), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('description'):
                return jsonify({"error": "Description is required"}), 400
            
            # Calculate risk score
            prob_score = {'low': 1, 'medium': 2, 'high': 3}.get(data.get('probability', 'medium'), 2)
            impact_score = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}.get(data.get('impact', 'medium'), 2)
            risk_score = prob_score * impact_score
            
            cursor.execute("""
                INSERT INTO job_risks (
                    job_id, description, category,
                    probability, impact, risk_score,
                    mitigation_plan, contingency_plan,
                    status, owner_id, review_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('description'),
                data.get('category'),
                data.get('probability', 'medium'),
                data.get('impact', 'medium'),
                risk_score,
                data.get('mitigation_plan'),
                data.get('contingency_plan'),
                data.get('status', 'identified'),
                data.get('owner_id'),
                data.get('review_date')
            ))
            
            risk_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": risk_id, "risk_score": risk_score}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/risks/<int:risk_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def manage_risk(job_id, risk_id):
    """Detail, update, delete rizika"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            cursor.execute("""
                SELECT jr.*, u.username as owner_name
                FROM job_risks jr
                LEFT JOIN users u ON jr.owner_id = u.id
                WHERE jr.id = ? AND jr.job_id = ?
            """, (risk_id, job_id))
            risk = dict_from_row(cursor.fetchone())
            
            if not risk:
                return jsonify({"error": "Risk not found"}), 404
            
            return jsonify(risk), 200
            
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Recalculate risk score
            prob_score = {'low': 1, 'medium': 2, 'high': 3}.get(data.get('probability', 'medium'), 2)
            impact_score = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}.get(data.get('impact', 'medium'), 2)
            risk_score = prob_score * impact_score
            
            cursor.execute("""
                UPDATE job_risks SET
                    description = ?,
                    category = ?,
                    probability = ?,
                    impact = ?,
                    risk_score = ?,
                    mitigation_plan = ?,
                    contingency_plan = ?,
                    status = ?,
                    owner_id = ?,
                    review_date = ?,
                    closed_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND job_id = ?
            """, (
                data.get('description'),
                data.get('category'),
                data.get('probability'),
                data.get('impact'),
                risk_score,
                data.get('mitigation_plan'),
                data.get('contingency_plan'),
                data.get('status'),
                data.get('owner_id'),
                data.get('review_date'),
                data.get('closed_date'),
                risk_id,
                job_id
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
        elif request.method == 'DELETE':
            cursor.execute("""
                DELETE FROM job_risks 
                WHERE id = ? AND job_id = ?
            """, (risk_id, job_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True}), 200
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 13. CHANGE REQUESTS MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/change-requests', methods=['GET', 'POST'])
@require_auth
def manage_change_requests(job_id):
    """Změnové požadavky"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            status = request.args.get('status')
            
            query = "SELECT * FROM job_change_requests WHERE job_id = ?"
            params = [job_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY urgency DESC, requested_date DESC"
            
            cursor.execute(query, params)
            changes = [dict_from_row(row) for row in cursor.fetchall()]
            
            # Count by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM job_change_requests 
                WHERE job_id = ? 
                GROUP BY status
            """, (job_id,))
            counts = {row['status']: row['count'] for row in cursor.fetchall()}
            
            return jsonify({
                "change_requests": changes,
                "counts": counts,
                "pending": counts.get('pending', 0)
            }), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('description'):
                return jsonify({"error": "Description is required"}), 400
            
            cursor.execute("""
                INSERT INTO job_change_requests (
                    job_id, requested_by, requested_by_name,
                    description, reason,
                    impact_cost, impact_time, impact_scope,
                    urgency, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('requested_by', 'client'),
                data.get('requested_by_name'),
                data.get('description'),
                data.get('reason'),
                data.get('impact_cost'),
                data.get('impact_time'),
                data.get('impact_scope'),
                data.get('urgency', 'medium'),
                'pending'
            ))
            
            change_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": change_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/change-requests/<int:change_id>/approve', methods=['POST'])
@require_auth
def approve_change_request(job_id, change_id):
    """Schválit změnový požadavek"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # TODO: Get current user ID from session
        user_id = request.get_json().get('approved_by')  # Replace with actual auth
        
        cursor.execute("""
            UPDATE job_change_requests SET
                status = 'approved',
                approved_by = ?,
                approved_date = date('now'),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND job_id = ?
        """, (user_id, change_id, job_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Change request approved"}), 200
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/jobs/<int:job_id>/change-requests/<int:change_id>/reject', methods=['POST'])
@require_auth
def reject_change_request(job_id, change_id):
    """Zamítnout změnový požadavek"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        data = request.get_json() or {}
        
        cursor.execute("""
            UPDATE job_change_requests SET
                status = 'rejected',
                rejection_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND job_id = ?
        """, (data.get('rejection_reason'), change_id, job_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Change request rejected"}), 200
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# 14. DOCUMENTS MANAGEMENT
# ============================================================================

@app.route('/api/jobs/<int:job_id>/documents', methods=['GET', 'POST'])
@require_auth
def manage_documents(job_id):
    """Správa dokumentů"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if request.method == 'GET':
            doc_type = request.args.get('type')  # 'contract', 'permit', etc.
            
            query = "SELECT * FROM job_documents WHERE job_id = ? AND is_latest = 1"
            params = [job_id]
            
            if doc_type:
                query += " AND type = ?"
                params.append(doc_type)
            
            query += " ORDER BY type, created_at DESC"
            
            cursor.execute(query, params)
            documents = [dict_from_row(row) for row in cursor.fetchall()]
            
            return jsonify(documents), 200
            
        elif request.method == 'POST':
            data = request.get_json()
            
            if not data.get('name') or not data.get('file_path'):
                return jsonify({"error": "Name and file path are required"}), 400
            
            # TODO: Get current user ID from session
            user_id = data.get('uploaded_by')  # Replace with actual auth
            
            cursor.execute("""
                INSERT INTO job_documents (
                    job_id, name, type, category,
                    file_path, file_size, mime_type,
                    description, uploaded_by,
                    signed, approval_status, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get('name'),
                data.get('type', 'other'),
                data.get('category'),
                data.get('file_path'),
                data.get('file_size'),
                data.get('mime_type'),
                data.get('description'),
                user_id,
                data.get('signed', False),
                data.get('approval_status', 'pending'),
                json.dumps(data.get('tags', []))
            ))
            
            doc_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "id": doc_id}), 201
            
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

# ============================================================================
# KONEC API
# ============================================================================

# NOTE: Nezapomeň přidat tyto endpointy do main.py!
# Nebo importuj tento modul:
# from jobs_api import *
