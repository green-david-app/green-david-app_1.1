from flask import Blueprint, request, jsonify
import sys
import os
import importlib.util

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import service
_qr_service_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'qr_service.py')
spec = importlib.util.spec_from_file_location("qr_service", _qr_service_path)
qr_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qr_service_module)
QRService = qr_service_module.QRService

qr_bp = Blueprint('qr_api', __name__, url_prefix='/api/qr')


@qr_bp.route('/scan', methods=['POST'])
def scan_qr():
    """Zpracuje naskenovaný QR kód a vrátí kontext + akce."""
    data = request.get_json()
    qr_string = data.get('qr_code')
    employee_id = data.get('employee_id')
    
    if not qr_string:
        return jsonify({'success': False, 'error': 'QR code required'}), 400
    
    # Parse QR
    parsed = QRService.parse_qr(qr_string)
    if not parsed.get('valid'):
        return jsonify({'success': False, 'error': parsed.get('error')}), 400
    
    # Get context
    context = QRService.get_scan_context(
        parsed['entity_type'],
        parsed['entity_id'],
        employee_id
    )
    
    if 'error' in context:
        return jsonify({'success': False, 'error': context['error']}), 404
    
    return jsonify({'success': True, 'data': context})


@qr_bp.route('/action', methods=['POST'])
def execute_action():
    """Provede akci z QR kontextu."""
    data = request.get_json()
    
    if not data.get('action') or not data.get('entity_type') or not data.get('entity_id'):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    result = QRService.execute_quick_action(
        action=data.get('action'),
        entity_type=data.get('entity_type'),
        entity_id=data.get('entity_id'),
        employee_id=data.get('employee_id'),
        data=data.get('action_data', {})
    )
    
    if not result.get('success'):
        return jsonify(result), 400
    
    return jsonify(result)


@qr_bp.route('/generate/<entity_type>/<int:entity_id>', methods=['GET'])
def generate_qr(entity_type, entity_id):
    """Vygeneruje QR kód pro entitu."""
    data = QRService.generate_qr_payload(entity_type, entity_id)
    return jsonify({'success': True, 'data': data})
