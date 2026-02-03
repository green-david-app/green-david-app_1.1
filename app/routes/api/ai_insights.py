from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import sys
import os
import importlib.util

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import services
_ai_interface_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'ai_operator_task_interface.py')
spec = importlib.util.spec_from_file_location("ai_operator_task_interface", _ai_interface_path)
ai_interface_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_interface_module)
AIOperatorTaskInterface = ai_interface_module.AIOperatorTaskInterface

_ai_explainability_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'ai_explainability.py')
spec = importlib.util.spec_from_file_location("ai_explainability", _ai_explainability_path)
explainability_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(explainability_module)
AIExplainabilityService = explainability_module.AIExplainabilityService

ai_bp = Blueprint('ai_api', __name__, url_prefix='/api/ai')


def alert_to_dict(alert_row):
    """Convert alert row to dict."""
    alert = dict(alert_row)
    
    # Parse JSON fields
    detail_data_str = alert.get('detail_data', '{}')
    try:
        alert['detail_data'] = json.loads(detail_data_str) if isinstance(detail_data_str, str) else detail_data_str
    except:
        alert['detail_data'] = {}
    
    recommended_actions_str = alert.get('recommended_actions', '[]')
    try:
        alert['recommended_actions'] = json.loads(recommended_actions_str) if isinstance(recommended_actions_str, str) else recommended_actions_str
    except:
        alert['recommended_actions'] = []
    
    return alert


def briefing_to_dict(briefing_row):
    """Convert briefing row to dict."""
    briefing = dict(briefing_row)
    
    # Parse JSON fields
    full_data_str = briefing.get('full_data', '{}')
    try:
        briefing['full_data'] = json.loads(full_data_str) if isinstance(full_data_str, str) else full_data_str
    except:
        briefing['full_data'] = {}
    
    return briefing


@ai_bp.route('/job/<int:job_id>/situation', methods=['GET'])
def get_job_situation(job_id):
    """
    Kompletní situační report zakázky.
    """
    report = AIOperatorTaskInterface.get_job_situation_report(job_id)
    return jsonify({'success': True, 'data': report})


@ai_bp.route('/employee/<int:employee_id>/context', methods=['GET'])
def get_employee_context(employee_id):
    """
    Performance kontext zaměstnance.
    """
    days = request.args.get('days', 30, type=int)
    context = AIOperatorTaskInterface.get_employee_performance_context(employee_id, days)
    return jsonify({'success': True, 'data': context})


@ai_bp.route('/bottlenecks', methods=['GET'])
def get_bottlenecks():
    """
    Aktuální bottlenecky v systému.
    """
    job_id = request.args.get('job_id', type=int)
    scope = {'job_id': job_id} if job_id else {'all': True}
    
    bottlenecks = AIOperatorTaskInterface.detect_bottlenecks(scope)
    
    # Add explanations
    for bn in bottlenecks:
        bn['explanation'] = AIExplainabilityService.explain_bottleneck_detection(bn)
    
    return jsonify({'success': True, 'data': bottlenecks})


@ai_bp.route('/patterns', methods=['GET'])
def get_patterns():
    """
    Detekované vzorce.
    """
    job_id = request.args.get('job_id', type=int)
    employee_id = request.args.get('employee_id', type=int)
    min_occurrences = request.args.get('min_occurrences', 3, type=int)
    
    scope = {}
    if job_id:
        scope['job_id'] = job_id
    if employee_id:
        scope['employee_id'] = employee_id
    
    patterns = AIOperatorTaskInterface.analyze_deviation_patterns(scope, min_occurrences)
    
    # Add explanations
    for p in patterns:
        p['explanation'] = AIExplainabilityService.explain_pattern_detection(p)
    
    return jsonify({'success': True, 'data': patterns})


@ai_bp.route('/briefing', methods=['GET'])
def get_daily_briefing():
    """
    Denní briefing.
    """
    db = get_db()
    
    date_str = request.args.get('date')
    
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            date = datetime.utcnow().date()
    else:
        date = datetime.utcnow().date()
    
    briefing_row = db.execute("SELECT * FROM daily_briefings WHERE briefing_date = ?", (date.isoformat(),)).fetchone()
    
    if briefing_row:
        briefing = briefing_to_dict(briefing_row)
        return jsonify({'success': True, 'data': briefing})
    
    # Generate on-the-fly
    briefing_data = AIOperatorTaskInterface.generate_daily_briefing(datetime.combine(date, datetime.min.time()))
    return jsonify({'success': True, 'data': briefing_data, 'generated': True})


@ai_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Aktivní AI alerty.
    """
    db = get_db()
    
    status = request.args.get('status', 'active')
    severity = request.args.get('severity')
    job_id = request.args.get('job_id', type=int)
    
    query = "SELECT * FROM ai_alerts WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if job_id:
        query += " AND job_id = ?"
        params.append(job_id)
    
    query += " ORDER BY created_at DESC LIMIT 50"
    
    alerts_rows = db.execute(query, params).fetchall()
    alerts = [alert_to_dict(a) for a in alerts_rows]
    
    return jsonify({
        'success': True,
        'data': alerts
    })


@ai_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """
    Potvrdí alert.
    """
    db = get_db()
    
    alert_row = db.execute("SELECT * FROM ai_alerts WHERE id = ?", (alert_id,)).fetchone()
    if not alert_row:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
    
    db.execute("""
        UPDATE ai_alerts 
        SET status = 'acknowledged', acknowledged_at = ?
        WHERE id = ?
    """, (datetime.utcnow().isoformat(), alert_id))
    db.commit()
    
    updated_alert_row = db.execute("SELECT * FROM ai_alerts WHERE id = ?", (alert_id,)).fetchone()
    alert = alert_to_dict(updated_alert_row)
    
    return jsonify({'success': True, 'data': alert})


@ai_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """
    Vyřeší alert.
    """
    db = get_db()
    
    alert_row = db.execute("SELECT * FROM ai_alerts WHERE id = ?", (alert_id,)).fetchone()
    if not alert_row:
        return jsonify({'success': False, 'error': 'Alert not found'}), 404
    
    data = request.get_json() or {}
    action_taken = data.get('action_taken', '')
    
    db.execute("""
        UPDATE ai_alerts 
        SET status = 'resolved', resolved_at = ?, action_taken = ?
        WHERE id = ?
    """, (datetime.utcnow().isoformat(), action_taken, alert_id))
    db.commit()
    
    updated_alert_row = db.execute("SELECT * FROM ai_alerts WHERE id = ?", (alert_id,)).fetchone()
    alert = alert_to_dict(updated_alert_row)
    
    return jsonify({'success': True, 'data': alert})
