from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from marshmallow import ValidationError
import sys
import os as os_module
import importlib.util

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import services
_task_event_service_path = os_module.path.join(os_module.path.dirname(__file__), '..', '..', 'services', 'task_event_service.py')
spec = importlib.util.spec_from_file_location("task_event_service", _task_event_service_path)
event_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_service_module)
TaskEventService = event_service_module.TaskEventService

_task_integrity_service_path = os_module.path.join(os_module.path.dirname(__file__), '..', '..', 'services', 'task_integrity_service.py')
spec = importlib.util.spec_from_file_location("task_integrity_service", _task_integrity_service_path)
integrity_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity_service_module)
TaskIntegrityService = integrity_service_module.TaskIntegrityService

_event_types_path = os_module.path.join(os_module.path.dirname(__file__), '..', '..', 'utils', 'event_types.py')
spec = importlib.util.spec_from_file_location("event_types", _event_types_path)
event_types_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_types_module)
TaskEventType = event_types_module.TaskEventType

_schemas_path = os_module.path.join(os_module.path.dirname(__file__), '..', '..', 'schemas', 'task_schemas.py')
spec = importlib.util.spec_from_file_location("task_schemas", _schemas_path)
schemas_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schemas_module)
AddEvidenceSchema = schemas_module.AddEvidenceSchema

evidence_bp = Blueprint('evidence_api', __name__, url_prefix='/api/tasks')

UPLOAD_FOLDER = 'uploads/evidence'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@evidence_bp.route('/<int:task_id>/evidence', methods=['POST'])
def add_evidence(task_id):
    """
    Přidá evidenci k tasku (foto nebo poznámku).
    """
    db = get_db()
    
    task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task_row:
        return jsonify({'success': False, 'error': 'Task not found'}), 404
    
    # Rozliš mezi file upload a JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        # File upload
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{task_id}_{timestamp}_{filename}"
        
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Get form data
        evidence_type = request.form.get('evidence_type', 'photo')
        captured_at_str = request.form.get('captured_at', datetime.utcnow().isoformat())
        try:
            captured_at = datetime.fromisoformat(captured_at_str.replace('Z', '+00:00'))
        except:
            captured_at = datetime.utcnow()
        
        # Create evidence
        db.execute("""
            INSERT INTO task_evidence (
                task_id, evidence_type, file_path, file_name,
                captured_at, gps_lat, gps_lng, captured_offline
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            evidence_type,
            file_path,
            filename,
            captured_at.isoformat(),
            float(request.form.get('gps_lat')) if request.form.get('gps_lat') else None,
            float(request.form.get('gps_lng')) if request.form.get('gps_lng') else None,
            1 if request.form.get('captured_offline', 'false').lower() == 'true' else 0
        ))
        db.commit()
        
        evidence_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        evidence_row = db.execute("SELECT * FROM task_evidence WHERE id = ?", (evidence_id,)).fetchone()
        evidence = dict(evidence_row)
        
    else:
        # JSON data (note, measurement)
        try:
            schema = AddEvidenceSchema()
            data = schema.load(request.get_json())
        except ValidationError as err:
            return jsonify({'success': False, 'error': err.messages}), 400
        
        captured_at = data['captured_at']
        if isinstance(captured_at, str):
            captured_at = datetime.fromisoformat(captured_at.replace('Z', '+00:00'))
        
        # Create evidence
        db.execute("""
            INSERT INTO task_evidence (
                task_id, evidence_type, note_text, measurement_value, measurement_unit,
                captured_at, gps_lat, gps_lng, captured_offline
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            data['evidence_type'],
            data.get('note_text'),
            data.get('measurement_value'),
            data.get('measurement_unit'),
            captured_at.isoformat(),
            data.get('gps_lat'),
            data.get('gps_lng'),
            1 if data.get('captured_offline', False) else 0
        ))
        db.commit()
        
        evidence_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        evidence_row = db.execute("SELECT * FROM task_evidence WHERE id = ?", (evidence_id,)).fetchone()
        evidence = dict(evidence_row)
    
    # Emit event
    try:
        TaskEventService.emit(
            task_id=task_id,
            event_type=TaskEventType.TASK_EVIDENCE_ADDED,
            payload={
                'evidence_id': evidence_id,
                'evidence_type': evidence.get('evidence_type'),
                'has_file': evidence.get('file_path') is not None,
                'has_gps': evidence.get('gps_lat') is not None,
                'captured_offline': bool(evidence.get('captured_offline', False))
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
    
    # Get updated integrity score
    task_row = db.execute("SELECT integrity_score FROM tasks WHERE id = ?", (task_id,)).fetchone()
    integrity_score = task_row[0] if task_row else 100.0
    
    return jsonify({
        'success': True,
        'evidence': evidence,
        'new_integrity_score': integrity_score
    }), 201


@evidence_bp.route('/<int:task_id>/evidence/<int:evidence_id>/validate', methods=['POST'])
def validate_evidence(task_id, evidence_id):
    """
    Validuje evidenci (leader/management action).
    """
    db = get_db()
    
    evidence_row = db.execute("""
        SELECT * FROM task_evidence WHERE id = ? AND task_id = ?
    """, (evidence_id, task_id)).fetchone()
    
    if not evidence_row:
        return jsonify({'success': False, 'error': 'Evidence not found'}), 404
    
    data = request.get_json() or {}
    
    # Update evidence
    db.execute("""
        UPDATE task_evidence 
        SET is_validated = 1, validated_at = ?, validation_notes = ?
        WHERE id = ?
    """, (
        datetime.utcnow().isoformat(),
        data.get('notes'),
        evidence_id
    ))
    db.commit()
    
    # Emit event
    try:
        TaskEventService.emit(
            task_id=task_id,
            event_type=TaskEventType.TASK_EVIDENCE_VALIDATED,
            payload={
                'evidence_id': evidence_id,
                'validated_by': getattr(request, 'current_user_id', None)
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
    
    # Get updated evidence
    updated_evidence_row = db.execute("SELECT * FROM task_evidence WHERE id = ?", (evidence_id,)).fetchone()
    evidence = dict(updated_evidence_row)
    
    return jsonify({
        'success': True,
        'evidence': evidence
    })
