from flask import Blueprint, request, jsonify, g
from datetime import datetime
from marshmallow import ValidationError
import json
import uuid as uuid_lib
import sys
import os
import importlib.util

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import services directly
_dependency_graph_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'dependency_graph_service.py')
spec = importlib.util.spec_from_file_location("dependency_graph_service", _dependency_graph_path)
dependency_graph_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dependency_graph_module)
DependencyGraphService = dependency_graph_module.DependencyGraphService

_risk_propagation_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'risk_propagation_service.py')
spec = importlib.util.spec_from_file_location("risk_propagation_service", _risk_propagation_path)
risk_propagation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(risk_propagation_module)
RiskPropagationService = risk_propagation_module.RiskPropagationService

_task_event_service_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'task_event_service.py')
spec = importlib.util.spec_from_file_location("task_event_service", _task_event_service_path)
event_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_service_module)
TaskEventService = event_service_module.TaskEventService

_task_integrity_service_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'task_integrity_service.py')
spec = importlib.util.spec_from_file_location("task_integrity_service", _task_integrity_service_path)
integrity_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity_service_module)
TaskIntegrityService = integrity_service_module.TaskIntegrityService

_event_types_path = os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'event_types.py')
spec = importlib.util.spec_from_file_location("event_types", _event_types_path)
event_types_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_types_module)
TaskEventType = event_types_module.TaskEventType

# Import schemas
_schemas_path = os.path.join(os.path.dirname(__file__), '..', '..', 'schemas', 'task_schemas.py')
spec = importlib.util.spec_from_file_location("task_schemas", _schemas_path)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)
CreateTaskSchema = schemas_module.CreateTaskSchema
UpdateTaskSchema = schemas_module.UpdateTaskSchema
StartTaskSchema = schemas_module.StartTaskSchema
CompleteTaskSchema = schemas_module.CompleteTaskSchema
BlockTaskSchema = schemas_module.BlockTaskSchema

tasks_bp = Blueprint('tasks_api', __name__, url_prefix='/api/tasks')


# === HELPER FUNCTIONS ===

def api_response(data=None, message=None, success=True, status_code=200):
    """Standardní formát API odpovědi."""
    response = {'success': success}
    if message:
        response['message'] = message
    if data is not None:
        response['data'] = data
    return jsonify(response), status_code


def api_error(message, code='ERROR', details=None, status_code=400):
    """Standardní formát chybové odpovědi."""
    response = {
        'success': False,
        'error': {
            'code': code,
            'message': message
        }
    }
    if details:
        response['error']['details'] = details
    return jsonify(response), status_code


def task_to_dict(task_row, include_relations=False):
    """Convert task row to dict."""
    task_dict = dict(task_row)
    
    # Parse JSON fields
    integrity_flags_str = task_dict.get('integrity_flags', '[]')
    try:
        task_dict['integrity_flags'] = json.loads(integrity_flags_str) if isinstance(integrity_flags_str, str) else integrity_flags_str
    except:
        task_dict['integrity_flags'] = []
    
    risk_factors_str = task_dict.get('risk_factors', '[]')
    try:
        task_dict['risk_factors'] = json.loads(risk_factors_str) if isinstance(risk_factors_str, str) else risk_factors_str
    except:
        task_dict['risk_factors'] = []
    
    if include_relations:
        db_conn = get_db()
        task_id = task_dict['id']
        
        # Get materials
        materials_rows = db_conn.execute("SELECT * FROM task_materials WHERE task_id = ?", (task_id,)).fetchall()
        task_dict['materials'] = [dict(m) for m in materials_rows]
        
        # Get evidences
        evidences_rows = db_conn.execute("SELECT * FROM task_evidence WHERE task_id = ?", (task_id,)).fetchall()
        task_dict['evidences'] = [dict(e) for e in evidences_rows]
    
    return task_dict


# === CRUD ENDPOINTS ===

@tasks_bp.route('', methods=['POST'])
def create_task():
    """
    Vytvoří nový task.
    """
    db_conn = get_db()
    
    try:
        schema = CreateTaskSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return api_error('Validation failed', 'VALIDATION_ERROR', err.messages)
    
    # Get current user ID (fallback to assigned_employee_id)
    current_user_id = getattr(g, 'current_user_id', None) or data['assigned_employee_id']
    
    # Calculate duration
    planned_start = data['planned_start']
    planned_end = data['planned_end']
    if isinstance(planned_start, str):
        planned_start = datetime.fromisoformat(planned_start.replace('Z', '+00:00'))
    if isinstance(planned_end, str):
        planned_end = datetime.fromisoformat(planned_end.replace('Z', '+00:00'))
    
    duration_minutes = int((planned_end - planned_start).total_seconds() / 60)
    
    # Generate UUID
    task_uuid = data.get('offline_uuid') or str(uuid_lib.uuid4())
    
    # Insert task
    db_conn.execute("""
        INSERT INTO tasks (
            uuid, job_id, title, description, task_type, assigned_employee_id, created_by_id,
            planned_start, planned_end, planned_duration_minutes, location_type, location_id,
            location_name, gps_lat, gps_lng, expected_outcome, expected_outcome_type,
            expected_quantity, expected_unit, priority, created_offline, integrity_score, integrity_flags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        task_uuid,
        data['job_id'],
        data['title'],
        data.get('description'),
        data['task_type'],
        data['assigned_employee_id'],
        current_user_id,
        planned_start.isoformat(),
        planned_end.isoformat(),
        duration_minutes,
        data['location_type'],
        data.get('location_id'),
        data.get('location_name'),
        data.get('gps_lat'),
        data.get('gps_lng'),
        data['expected_outcome'],
        data.get('expected_outcome_type'),
        data.get('expected_quantity'),
        data.get('expected_unit'),
        data.get('priority', 'normal'),
        1 if data.get('created_offline', False) else 0,
        100.0,  # Default integrity
        '[]'
    ))
    db_conn.commit()
    
    task_id = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    
    # Add materials
    warnings = []
    if data.get('materials'):
        for mat_data in data['materials']:
            db_conn.execute("""
                INSERT INTO task_materials (
                    task_id, material_id, material_name, planned_quantity, unit
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                task_id,
                mat_data.get('material_id'),
                mat_data['material_name'],
                mat_data['planned_quantity'],
                mat_data['unit']
            ))
    
    # Add dependencies
    if data.get('dependencies'):
        for dep_data in data['dependencies']:
            # Check for cycles (simplified - would need full graph check)
            db_conn.execute("""
                INSERT INTO task_dependencies (
                    predecessor_task_id, successor_task_id, dependency_type,
                    lag_minutes, is_hard, status, risk_weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                dep_data['predecessor_task_id'],
                task_id,
                dep_data['dependency_type'],
                dep_data.get('lag_minutes', 0),
                1 if dep_data.get('is_hard', True) else 0,
                'pending',
                1.0
            ))
    
    db_conn.commit()
    
    # Emit created event
    try:
        TaskEventService.emit(
            task_id=task_id,
            event_type=TaskEventType.TASK_CREATED,
            payload={
                'created_by': current_user_id,
                'initial_status': 'planned'
            },
            employee_id=current_user_id,
            source='web_app'
        )
    except:
        pass
    
    # Recalculate integrity
    try:
        TaskIntegrityService.recalculate_and_update(task_id, emit_events=False)
    except:
        pass
    
    # Get created task
    task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    task_dict = task_to_dict(task_row, include_relations=True)
    
    return api_response({
        'task': task_dict,
        'integrity_score': task_dict.get('integrity_score', 100.0),
        'warnings': warnings
    }, status_code=201)


@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """
    Vrací detail tasku.
    """
    db_conn = get_db()
    
    task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task_row:
        return api_error('Task not found', 'NOT_FOUND', status_code=404)
    
    task_dict = task_to_dict(task_row, include_relations=True)
    
    # Add dependencies
    pred_deps = db_conn.execute("""
        SELECT * FROM task_dependencies WHERE successor_task_id = ?
    """, (task_id,)).fetchall()
    
    succ_deps = db_conn.execute("""
        SELECT * FROM task_dependencies WHERE predecessor_task_id = ?
    """, (task_id,)).fetchall()
    
    task_dict['dependencies'] = {
        'predecessors': [dict(d) for d in pred_deps],
        'successors': [dict(d) for d in succ_deps]
    }
    
    # Add recent events
    try:
        recent_events = TaskEventService.get_task_history(task_id, limit=10)
        task_dict['recent_events'] = [e.to_dict() if hasattr(e, 'to_dict') else {
            'id': e.id,
            'event_type': e.event_type,
            'occurred_at': e.occurred_at.isoformat() if isinstance(e.occurred_at, datetime) else str(e.occurred_at),
            'payload': e.payload_dict if hasattr(e, 'payload_dict') else {}
        } for e in recent_events]
    except:
        task_dict['recent_events'] = []
    
    # Integrity breakdown
    try:
        _, flags, breakdown = TaskIntegrityService.calculate_full_integrity(task_dict)
        task_dict['integrity_breakdown'] = breakdown
    except:
        task_dict['integrity_breakdown'] = {}
    
    # Can start?
    try:
        task_dict['can_start'] = DependencyGraphService.check_can_start(task_id)
    except:
        task_dict['can_start'] = {'can_start': True}
    
    return api_response(task_dict)


@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """
    Aktualizuje task s optimistic locking.
    """
    db_conn = get_db()
    
    task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task_row:
        return api_error('Task not found', 'NOT_FOUND', status_code=404)
    
    task_dict = dict(task_row)
    
    try:
        schema = UpdateTaskSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return api_error('Validation failed', 'VALIDATION_ERROR', err.messages)
    
    # Version check
    if data['version'] != task_dict.get('version', 1):
        return api_error(
            'Task was modified by another user',
            'TASK_003',
            {
                'your_version': data['version'],
                'current_version': task_dict.get('version', 1),
                'current_data': task_to_dict(task_row)
            },
            status_code=409
        )
    
    # Track changes
    changes = {}
    updates = {}
    
    # Update fields
    for field in ['title', 'description', 'expected_outcome', 'priority']:
        if field in data and data[field] is not None:
            old_value = task_dict.get(field)
            if old_value != data[field]:
                changes[field] = {'old': old_value, 'new': data[field]}
                updates[field] = data[field]
    
    # Reassignment
    if 'assigned_employee_id' in data and data['assigned_employee_id'] != task_dict.get('assigned_employee_id'):
        old_employee = task_dict.get('assigned_employee_id')
        updates['assigned_employee_id'] = data['assigned_employee_id']
        
        try:
            TaskEventService.emit(
                task_id=task_id,
                event_type=TaskEventType.TASK_REASSIGNED,
                payload={
                    'previous_employee_id': old_employee,
                    'new_employee_id': data['assigned_employee_id'],
                    'reason': data.get('reassignment_reason')
                },
                employee_id=data['assigned_employee_id'],
                source='web_app'
            )
        except:
            pass
    
    # Reschedule
    if 'planned_start' in data or 'planned_end' in data:
        old_start = task_dict.get('planned_start')
        old_end = task_dict.get('planned_end')
        
        new_start = data.get('planned_start', old_start)
        new_end = data.get('planned_end', old_end)
        
        if isinstance(new_start, str):
            new_start = datetime.fromisoformat(new_start.replace('Z', '+00:00'))
        if isinstance(new_end, str):
            new_end = datetime.fromisoformat(new_end.replace('Z', '+00:00'))
        
        updates['planned_start'] = new_start.isoformat()
        updates['planned_end'] = new_end.isoformat()
        
        duration_minutes = int((new_end - new_start).total_seconds() / 60)
        updates['planned_duration_minutes'] = duration_minutes
        
        try:
            TaskEventService.emit(
                task_id=task_id,
                event_type=TaskEventType.TASK_RESCHEDULED,
                payload={
                    'previous_start': old_start.isoformat() if old_start else None,
                    'previous_end': old_end.isoformat() if old_end else None,
                    'new_start': new_start.isoformat(),
                    'new_end': new_end.isoformat()
                },
                source='web_app'
            )
        except:
            pass
    
    # Increment version
    updates['version'] = (task_dict.get('version', 1) + 1)
    updates['updated_at'] = datetime.utcnow().isoformat()
    
    # Build UPDATE query
    if updates:
        set_clauses = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [task_id]
        
        db_conn.execute(f"""
            UPDATE tasks 
            SET {set_clauses}
            WHERE id = ?
        """, values)
        db_conn.commit()
    
    # Recalculate integrity
    try:
        TaskIntegrityService.recalculate_and_update(task_id, emit_events=False)
    except:
        pass
    
    # Get updated task
    updated_task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    updated_task_dict = task_to_dict(updated_task_row, include_relations=True)
    
    return api_response({
        'task': updated_task_dict,
        'changes': changes
    })


@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """
    Soft delete - označí task jako cancelled.
    """
    db_conn = get_db()
    
    task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task_row:
        return api_error('Task not found', 'NOT_FOUND', status_code=404)
    
    # Check dependencies
    try:
        dependent_tasks = DependencyGraphService.get_downstream_tasks(task_id, max_depth=1)
        active_dependents = [d for d in dependent_tasks if d.get('status') not in ['completed', 'cancelled', 'failed']]
        
        if active_dependents:
            return api_error(
                'Cannot delete task with active dependencies',
                'TASK_006',
                {'dependent_tasks': active_dependents}
            )
    except:
        pass
    
    # Update status
    db_conn.execute("UPDATE tasks SET status = 'cancelled', updated_at = ? WHERE id = ?", 
               (datetime.utcnow().isoformat(), task_id))
    db_conn.commit()
    
    # Emit event
    try:
        cancel_reason = request.get_json().get('reason', 'User cancelled') if request.get_json() else 'User cancelled'
        TaskEventService.emit(
            task_id=task_id,
            event_type=TaskEventType.TASK_CANCELLED,
            payload={'reason': cancel_reason},
            source='web_app'
        )
    except:
        pass
    
    return api_response({'message': 'Task cancelled'})


# === LIFECYCLE ENDPOINTS ===

@tasks_bp.route('/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """
    Zahájí práci na tasku.
    """
    db_conn = get_db()
    
    task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task_row:
        return api_error('Task not found', 'NOT_FOUND', status_code=404)
    
    task_dict = dict(task_row)
    status = task_dict.get('status', 'planned')
    
    if status not in ['planned', 'assigned']:
        return api_error(
            f'Cannot start task in status {status}',
            'TASK_004',
            {'current_status': status, 'allowed_statuses': ['planned', 'assigned']}
        )
    
    try:
        schema = StartTaskSchema()
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return api_error('Validation failed', 'VALIDATION_ERROR', err.messages)
    
    # Check dependencies
    try:
        can_start_check = DependencyGraphService.check_can_start(task_id)
        if not can_start_check.get('can_start'):
            return api_error(
                'Task has unsatisfied dependencies',
                'TASK_001',
                can_start_check
            )
    except:
        pass
    
    # Set actual_start
    actual_start = data.get('started_at') or datetime.utcnow()
    if isinstance(actual_start, str):
        actual_start = datetime.fromisoformat(actual_start.replace('Z', '+00:00'))
    
    updates = {
        'actual_start': actual_start.isoformat(),
        'status': 'in_progress',
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # GPS
    if data.get('gps_lat'):
        updates['gps_lat'] = data['gps_lat']
        updates['gps_lng'] = data['gps_lng']
    
    # Calculate delay
    delay_minutes = 0
    planned_start_str = task_dict.get('planned_start')
    if planned_start_str:
        try:
            if isinstance(planned_start_str, str):
                planned_start = datetime.fromisoformat(planned_start_str.replace('Z', '+00:00'))
            else:
                planned_start = planned_start_str
            
            if actual_start > planned_start:
                delay_minutes = int((actual_start - planned_start).total_seconds() / 60)
        except:
            pass
    
    # Update task
    set_clauses = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [task_id]
    
    db_conn.execute(f"""
        UPDATE tasks 
        SET {set_clauses}
        WHERE id = ?
    """, values)
    db_conn.commit()
    
    # Emit event
    try:
        TaskEventService.emit(
            task_id=task_id,
            event_type=TaskEventType.TASK_STARTED,
            payload={
                'actual_start': actual_start.isoformat(),
                'planned_start': planned_start_str,
                'delay_minutes': delay_minutes,
                'gps_lat': data.get('gps_lat'),
                'gps_lng': data.get('gps_lng'),
                'gps_accuracy': data.get('gps_accuracy')
            },
            occurred_at=actual_start,
            offline=data.get('offline', False),
            source='web_app'
        )
    except:
        pass
    
    # Recalculate integrity
    try:
        TaskIntegrityService.recalculate_and_update(task_id, emit_events=False)
    except:
        pass
    
    # Get updated task
    updated_task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    updated_task_dict = task_to_dict(updated_task_row)
    
    return api_response({
        'task': updated_task_dict,
        'delay_minutes': delay_minutes
    })


@tasks_bp.route('/<int:task_id>/complete', methods=['POST'])
def complete_task(task_id):
    """
    Dokončí task.
    """
    db_conn = get_db()
    
    task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task_row:
        return api_error('Task not found', 'NOT_FOUND', status_code=404)
    
    task_dict = dict(task_row)
    
    if task_dict.get('status') != 'in_progress':
        return api_error(
            f'Cannot complete task in status {task_dict.get("status")}',
            'TASK_004',
            {'current_status': task_dict.get('status'), 'required_status': 'in_progress'}
        )
    
    try:
        schema = CompleteTaskSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return api_error('Validation failed', 'VALIDATION_ERROR', err.messages)
    
    # Set completion data
    actual_end = data.get('completed_at') or datetime.utcnow()
    if isinstance(actual_end, str):
        actual_end = datetime.fromisoformat(actual_end.replace('Z', '+00:00'))
    
    completion_state = data['completion_state']
    completion_percentage = data.get('completion_percentage', 100 if completion_state == 'done' else 50)
    
    # Calculate actual duration
    actual_duration_minutes = None
    time_deviation_minutes = 0
    actual_start_str = task_dict.get('actual_start')
    
    if actual_start_str:
        try:
            if isinstance(actual_start_str, str):
                actual_start = datetime.fromisoformat(actual_start_str.replace('Z', '+00:00'))
            else:
                actual_start = actual_start_str
            
            actual_duration_minutes = int((actual_end - actual_start).total_seconds() / 60)
            planned_duration = task_dict.get('planned_duration_minutes', 0)
            if planned_duration:
                time_deviation_minutes = actual_duration_minutes - planned_duration
        except:
            pass
    
    # Update materials
    materials_summary = {'total_items': 0, 'with_deviation': 0, 'substitutes_used': 0}
    has_material_deviation = False
    
    if data.get('materials_used'):
        for mat_update in data['materials_used']:
            material_id = mat_update.get('material_id')
            if material_id:
                material_row = db_conn.execute("""
                    SELECT * FROM task_materials 
                    WHERE task_id = ? AND material_id = ?
                """, (task_id, material_id)).fetchone()
                
                if material_row:
                    material = dict(material_row)
                    actual_qty = mat_update.get('actual_quantity')
                    
                    if actual_qty is not None:
                        db_conn.execute("""
                            UPDATE task_materials 
                            SET actual_quantity = ?, substitute_used = ?, substitute_notes = ?
                            WHERE id = ?
                        """, (
                            actual_qty,
                            1 if mat_update.get('substitute_used') else 0,
                            mat_update.get('substitute_notes'),
                            material['id']
                        ))
                        
                        materials_summary['total_items'] += 1
                        planned_qty = material.get('planned_quantity', 0)
                        if planned_qty and abs(actual_qty - planned_qty) / planned_qty > 0.1:
                            materials_summary['with_deviation'] += 1
                            has_material_deviation = True
                        
                        if mat_update.get('substitute_used'):
                            materials_summary['substitutes_used'] += 1
    
    # Update task
    updates = {
        'actual_end': actual_end.isoformat(),
        'status': 'completed',
        'completion_state': completion_state,
        'completion_percentage': completion_percentage,
        'actual_duration_minutes': actual_duration_minutes,
        'time_deviation_minutes': time_deviation_minutes,
        'has_material_deviation': 1 if has_material_deviation else 0,
        'deviation_notes': data.get('deviation_notes'),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # GPS
    if data.get('gps_lat'):
        updates['gps_lat'] = data['gps_lat']
        updates['gps_lng'] = data['gps_lng']
        
        # Create GPS checkin evidence
        db_conn.execute("""
            INSERT INTO task_evidence (
                task_id, evidence_type, gps_lat, gps_lng, captured_at, captured_offline
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            'gps_checkin',
            data['gps_lat'],
            data['gps_lng'],
            actual_end.isoformat(),
            1 if data.get('offline', False) else 0
        ))
    
    set_clauses = ', '.join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [task_id]
    
    db_conn.execute(f"""
        UPDATE tasks 
        SET {set_clauses}
        WHERE id = ?
    """, values)
    db_conn.commit()
    
    # Emit event
    try:
        event_type = TaskEventType.TASK_COMPLETED if completion_state == 'done' else TaskEventType.TASK_COMPLETED_PARTIAL
        
        planned_duration = task_dict.get('planned_duration_minutes', 0)
        time_deviation_pct = (time_deviation_minutes / planned_duration * 100) if planned_duration else 0
        
        # Count evidences
        evidence_count = db_conn.execute("SELECT COUNT(*) FROM task_evidence WHERE task_id = ?", (task_id,)).fetchone()[0]
        
        TaskEventService.emit(
            task_id=task_id,
            event_type=event_type,
            payload={
                'actual_end': actual_end.isoformat(),
                'actual_duration_minutes': actual_duration_minutes,
                'planned_duration_minutes': planned_duration,
                'completion_state': completion_state,
                'completion_percentage': completion_percentage,
                'time_deviation_minutes': time_deviation_minutes,
                'time_deviation_percentage': time_deviation_pct,
                'evidence_count': evidence_count,
                'materials_summary': materials_summary
            },
            occurred_at=actual_end,
            offline=data.get('offline', False),
            source='web_app'
        )
    except:
        pass
    
    # Update dependencies
    try:
        succ_deps = db_conn.execute("""
            SELECT id FROM task_dependencies WHERE predecessor_task_id = ?
        """, (task_id,)).fetchall()
        
        for dep_row in succ_deps:
            dep_id = dep_row[0]
            DependencyGraphService.update_dependency_status(dep_id)
    except:
        pass
    
    # Recalculate integrity
    try:
        TaskIntegrityService.recalculate_and_update(task_id, emit_events=False)
    except:
        pass
    
    # Warnings
    warnings = []
    evidence_count = db_conn.execute("SELECT COUNT(*) FROM task_evidence WHERE task_id = ?", (task_id,)).fetchone()[0]
    if evidence_count == 0:
        warnings.append('No evidence attached - consider adding photos')
    if time_deviation_minutes and time_deviation_minutes > 60:
        warnings.append(f'Significant time deviation: {time_deviation_minutes} minutes')
    
    # Get updated task
    updated_task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    updated_task_dict = task_to_dict(updated_task_row, include_relations=True)
    
    return api_response({
        'task': updated_task_dict,
        'warnings': warnings
    })


@tasks_bp.route('/<int:task_id>/block', methods=['POST'])
def block_task(task_id):
    """
    Označí task jako blokovaný.
    """
    db_conn = get_db()
    
    task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task_row:
        return api_error('Task not found', 'NOT_FOUND', status_code=404)
    
    try:
        schema = BlockTaskSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return api_error('Validation failed', 'VALIDATION_ERROR', err.messages)
    
    # Update status
    db_conn.execute("UPDATE tasks SET status = 'blocked', updated_at = ? WHERE id = ?",
               (datetime.utcnow().isoformat(), task_id))
    db_conn.commit()
    
    # Emit event
    try:
        event_type = TaskEventType.TASK_BLOCKED
        if data['block_type'] == 'material':
            event_type = TaskEventType.TASK_BLOCKED_MATERIAL
        elif data['block_type'] == 'weather':
            event_type = TaskEventType.TASK_BLOCKED_WEATHER
        elif data['block_type'] == 'dependency':
            event_type = TaskEventType.TASK_BLOCKED_DEPENDENCY
        
        TaskEventService.emit(
            task_id=task_id,
            event_type=event_type,
            payload={
                'block_reason': data['block_reason'],
                'block_type': data['block_type'],
                'blocking_entity_id': data.get('blocking_entity_id'),
                'estimated_resolution': data.get('estimated_resolution').isoformat() if data.get('estimated_resolution') else None,
                'can_workaround': data.get('can_workaround', False),
                'workaround_options': [data.get('workaround_description')] if data.get('workaround_description') else []
            },
            source='web_app'
        )
    except:
        pass
    
    # Propagate risk
    try:
        propagation = RiskPropagationService.propagate_delay(task_id, 60)
    except:
        propagation = {}
    
    # Recalculate integrity
    try:
        TaskIntegrityService.recalculate_and_update(task_id, emit_events=False)
    except:
        pass
    
    # Get updated task
    updated_task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    updated_task_dict = task_to_dict(updated_task_row)
    
    return api_response({
        'task': updated_task_dict,
        'risk_propagation': propagation
    })


@tasks_bp.route('/<int:task_id>/unblock', methods=['POST'])
def unblock_task(task_id):
    """
    Odblokuje task.
    """
    db_conn = get_db()
    
    task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task_row:
        return api_error('Task not found', 'NOT_FOUND', status_code=404)
    
    task_dict = dict(task_row)
    
    if task_dict.get('status') != 'blocked':
        return api_error('Task is not blocked', 'TASK_004')
    
    data = request.get_json() or {}
    
    # Find when blocked
    blocked_for_minutes = 0
    try:
        blocked_events = TaskEventService.get_task_history(
            task_id,
            event_types=['task_blocked', 'task_blocked_material', 'task_blocked_weather', 'task_blocked_dependency'],
            limit=1
        )
        
        if blocked_events:
            blocked_at = blocked_events[0].occurred_at
            if isinstance(blocked_at, str):
                blocked_at = datetime.fromisoformat(blocked_at.replace('Z', '+00:00'))
            blocked_for_minutes = int((datetime.utcnow() - blocked_at).total_seconds() / 60)
    except:
        pass
    
    # Update status
    new_status = 'in_progress' if task_dict.get('actual_start') else 'assigned'
    db_conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
               (new_status, datetime.utcnow().isoformat(), task_id))
    db_conn.commit()
    
    # Emit event
    try:
        TaskEventService.emit(
            task_id=task_id,
            event_type=TaskEventType.TASK_UNBLOCKED,
            payload={
                'was_blocked_for_minutes': blocked_for_minutes,
                'resolution_type': data.get('resolution_type', 'resolved'),
                'resolution_notes': data.get('resolution_notes')
            },
            source='web_app'
        )
    except:
        pass
    
    # Recalculate integrity
    try:
        TaskIntegrityService.recalculate_and_update(task_id, emit_events=False)
    except:
        pass
    
    # Get updated task
    updated_task_row = db_conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    updated_task_dict = task_to_dict(updated_task_row)
    
    return api_response({
        'task': updated_task_dict,
        'was_blocked_for_minutes': blocked_for_minutes
    })


# === QUERY ENDPOINTS ===

@tasks_bp.route('/job/<int:job_id>', methods=['GET'])
def get_job_tasks(job_id):
    """
    Vrací všechny tasky zakázky.
    """
    db_conn = get_db()
    
    query = "SELECT * FROM tasks WHERE job_id = ?"
    params = [job_id]
    
    # Filters
    status = request.args.get('status')
    if status:
        query += " AND status = ?"
        params.append(status)
    
    assigned_to = request.args.get('assigned_to', type=int)
    if assigned_to:
        query += " AND assigned_employee_id = ?"
        params.append(assigned_to)
    
    include_completed = request.args.get('include_completed', 'true').lower() == 'true'
    if not include_completed:
        query += " AND status NOT IN ('completed', 'cancelled')"
    
    integrity_below = request.args.get('integrity_below', type=float)
    if integrity_below:
        query += " AND integrity_score < ?"
        params.append(integrity_below)
    
    # Ordering
    query += " ORDER BY planned_start ASC"
    
    tasks_rows = db_conn.execute(query, params).fetchall()
    tasks = [task_to_dict(t) for t in tasks_rows]
    
    return api_response({
        'tasks': tasks,
        'count': len(tasks)
    })


@tasks_bp.route('/my-today', methods=['GET'])
def get_my_today_tasks():
    """
    Vrací tasky přihlášeného uživatele na dnešek.
    """
    db_conn = get_db()
    
    employee_id = request.args.get('employee_id', type=int)
    if not employee_id:
        return api_error('employee_id required', 'VALIDATION_ERROR')
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start.replace(hour=23, minute=59, second=59)
    
    tasks_rows = db_conn.execute("""
        SELECT * FROM tasks 
        WHERE assigned_employee_id = ? 
        AND planned_start >= ? 
        AND planned_start <= ?
        AND status != 'cancelled'
        ORDER BY planned_start ASC
    """, (employee_id, today_start.isoformat(), today_end.isoformat())).fetchall()
    
    result = []
    for task_row in tasks_rows:
        task_dict = task_to_dict(task_row)
        
        # Add can_start check
        try:
            task_dict['can_start'] = DependencyGraphService.check_can_start(task_dict['id'])
        except:
            task_dict['can_start'] = {'can_start': True}
        
        # Add materials count
        materials_count = db_conn.execute("SELECT COUNT(*) FROM task_materials WHERE task_id = ?", 
                                     (task_dict['id'],)).fetchone()[0]
        task_dict['materials_count'] = materials_count
        
        result.append(task_dict)
    
    return api_response({
        'tasks': result,
        'date': today_start.strftime('%Y-%m-%d'),
        'count': len(result)
    })
