from flask import Blueprint, request, jsonify
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

# Import schemas
_schemas_path = os.path.join(os.path.dirname(__file__), '..', '..', 'schemas', 'task_schemas.py')
spec = importlib.util.spec_from_file_location("task_schemas", _schemas_path)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)
SyncRequestSchema = schemas_module.SyncRequestSchema

sync_bp = Blueprint('sync_api', __name__, url_prefix='/api/tasks')


@sync_bp.route('/sync', methods=['POST'])
def sync_tasks():
    """
    Bulk sync pro offline-first mobilní app.
    """
    db = get_db()
    
    try:
        schema = SyncRequestSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({'success': False, 'error': err.messages}), 400
    
    device_id = data['device_id']
    last_sync = data['last_sync_at']
    if isinstance(last_sync, str):
        last_sync = datetime.fromisoformat(last_sync.replace('Z', '+00:00'))
    
    offline_changes = data.get('offline_changes', [])
    
    synced = []
    conflicts = []
    
    # Process offline changes
    for change in offline_changes:
        action = change.get('action')
        change_data = change.get('data', {})
        occurred_at_str = change.get('occurred_at')
        
        try:
            if action == 'create':
                # Check for duplicate by offline_uuid
                offline_uuid = change_data.get('offline_uuid')
                if offline_uuid:
                    existing = db.execute("SELECT id FROM tasks WHERE uuid = ?", (offline_uuid,)).fetchone()
                    if existing:
                        synced.append({
                            'offline_uuid': offline_uuid,
                            'status': 'duplicate',
                            'server_id': existing[0]
                        })
                        continue
                
                # Create task (simplified)
                task_uuid = offline_uuid or str(uuid_lib.uuid4())
                planned_start = change_data.get('planned_start')
                planned_end = change_data.get('planned_end')
                
                if isinstance(planned_start, str):
                    planned_start = datetime.fromisoformat(planned_start.replace('Z', '+00:00'))
                if isinstance(planned_end, str):
                    planned_end = datetime.fromisoformat(planned_end.replace('Z', '+00:00'))
                
                duration_minutes = int((planned_end - planned_start).total_seconds() / 60) if planned_start and planned_end else 0
                
                db.execute("""
                    INSERT INTO tasks (
                        uuid, job_id, title, task_type, assigned_employee_id, created_by_id,
                        planned_start, planned_end, planned_duration_minutes, location_type,
                        expected_outcome, created_offline, last_synced_at, integrity_score, integrity_flags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_uuid,
                    change_data.get('job_id', 1),
                    change_data.get('title', 'Offline Task'),
                    change_data.get('task_type', 'work'),
                    change_data.get('assigned_employee_id', 1),
                    change_data.get('assigned_employee_id', 1),
                    planned_start.isoformat() if planned_start else datetime.utcnow().isoformat(),
                    planned_end.isoformat() if planned_end else datetime.utcnow().isoformat(),
                    duration_minutes,
                    change_data.get('location_type', 'job_site'),
                    change_data.get('expected_outcome', 'Complete task'),
                    1,  # created_offline
                    datetime.utcnow().isoformat(),
                    100.0,
                    '[]'
                ))
                db.commit()
                
                task_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                
                synced.append({
                    'offline_uuid': offline_uuid,
                    'status': 'created',
                    'server_id': task_id
                })
            
            elif action == 'update':
                task_id = change_data.get('task_id')
                task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                
                if not task_row:
                    conflicts.append({
                        'change': change,
                        'conflict_type': 'not_found'
                    })
                    continue
                
                task_dict = dict(task_row)
                
                # Version check
                if change_data.get('version') != task_dict.get('version', 1):
                    conflicts.append({
                        'change': change,
                        'conflict_type': 'version_mismatch',
                        'server_data': task_dict
                    })
                    continue
                
                # Apply changes (simplified - only update allowed fields)
                updates = {}
                allowed_fields = ['title', 'description', 'status', 'completion_state', 'completion_percentage']
                
                for key, value in change_data.items():
                    if key in allowed_fields and hasattr(task_dict, key) if hasattr(task_dict, 'keys') else key in task_dict:
                        updates[key] = value
                
                if updates:
                    updates['version'] = task_dict.get('version', 1) + 1
                    updates['last_synced_at'] = datetime.utcnow().isoformat()
                    updates['updated_at'] = datetime.utcnow().isoformat()
                    
                    set_clauses = ', '.join([f"{k} = ?" for k in updates.keys()])
                    values = list(updates.values()) + [task_id]
                    
                    db.execute(f"""
                        UPDATE tasks 
                        SET {set_clauses}
                        WHERE id = ?
                    """, values)
                    db.commit()
                
                synced.append({
                    'task_id': task_id,
                    'status': 'updated'
                })
            
            elif action == 'start':
                task_id = change_data.get('task_id')
                task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                
                if task_row:
                    task_dict = dict(task_row)
                    if task_dict.get('status') in ['planned', 'assigned']:
                        started_at_str = change_data.get('started_at', datetime.utcnow().isoformat())
                        if isinstance(started_at_str, str):
                            started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
                        else:
                            started_at = started_at_str
                        
                        db.execute("""
                            UPDATE tasks 
                            SET status = 'in_progress', actual_start = ?, last_synced_at = ?, updated_at = ?
                            WHERE id = ?
                        """, (started_at.isoformat(), datetime.utcnow().isoformat(), datetime.utcnow().isoformat(), task_id))
                        db.commit()
                        
                        synced.append({
                            'task_id': task_id,
                            'status': 'started'
                        })
            
            elif action == 'complete':
                task_id = change_data.get('task_id')
                task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                
                if task_row:
                    task_dict = dict(task_row)
                    if task_dict.get('status') == 'in_progress':
                        completed_at_str = change_data.get('completed_at', datetime.utcnow().isoformat())
                        if isinstance(completed_at_str, str):
                            completed_at = datetime.fromisoformat(completed_at_str.replace('Z', '+00:00'))
                        else:
                            completed_at = completed_at_str
                        
                        db.execute("""
                            UPDATE tasks 
                            SET status = 'completed', completion_state = ?, actual_end = ?, last_synced_at = ?, updated_at = ?
                            WHERE id = ?
                        """, (
                            change_data.get('completion_state', 'done'),
                            completed_at.isoformat(),
                            datetime.utcnow().isoformat(),
                            datetime.utcnow().isoformat(),
                            task_id
                        ))
                        db.commit()
                        
                        synced.append({
                            'task_id': task_id,
                            'status': 'completed'
                        })
            
            elif action == 'evidence':
                task_id = change_data.get('task_id')
                captured_at_str = change_data.get('captured_at', datetime.utcnow().isoformat())
                if isinstance(captured_at_str, str):
                    captured_at = datetime.fromisoformat(captured_at_str.replace('Z', '+00:00'))
                else:
                    captured_at = captured_at_str
                
                db.execute("""
                    INSERT INTO task_evidence (
                        task_id, evidence_type, note_text, captured_at, captured_offline
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    task_id,
                    change_data.get('evidence_type', 'note'),
                    change_data.get('note_text'),
                    captured_at.isoformat(),
                    1  # captured_offline
                ))
                db.commit()
                
                synced.append({
                    'task_id': task_id,
                    'status': 'evidence_added'
                })
        
        except Exception as e:
            conflicts.append({
                'change': change,
                'conflict_type': 'error',
                'error': str(e)
            })
    
    # Get server updates since last_sync
    server_updates_rows = db.execute("""
        SELECT * FROM tasks 
        WHERE updated_at > ? OR created_at > ?
        ORDER BY updated_at DESC
        LIMIT 100
    """, (last_sync.isoformat(), last_sync.isoformat())).fetchall()
    
    server_updates = [dict(t) for t in server_updates_rows]
    
    return jsonify({
        'success': True,
        'synced': synced,
        'conflicts': conflicts,
        'server_updates': server_updates,
        'sync_timestamp': datetime.utcnow().isoformat()
    })
