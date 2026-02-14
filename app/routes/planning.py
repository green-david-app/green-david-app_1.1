# Green David App
from flask import Blueprint, jsonify, request, send_from_directory, render_template
from datetime import datetime, timedelta
from app.database import get_db
from app.utils.permissions import require_auth, require_role

try:
    import planning_api
    planning_api.get_db = get_db
except ImportError:
    planning_api = None

try:
    import planning_extended_api as ext_api
    ext_api.get_db = get_db
except ImportError:
    ext_api = None

planning_bp = Blueprint('planning', __name__)


# Planning routes from main.py
@planning_bp.route("/api/planning/timeline")
def api_planning_timeline():
    return planning_api.get_planning_timeline()

@planning_bp.route("/api/planning/daily")
@planning_bp.route("/api/planning/daily/<target_date>")
def api_planning_daily(target_date=None):
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.get_planning_daily(target_date)

@planning_bp.route("/api/planning/week")
def api_planning_week():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.get_planning_week()

@planning_bp.route("/api/planning/costs")
@planning_bp.route("/api/planning/costs/<int:job_id>")
def api_planning_costs(job_id=None):
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.get_planning_costs(job_id)

@planning_bp.route("/api/action-items", methods=["POST"])
def api_create_action_item():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.create_action_item()

@planning_bp.route("/api/planning/actions/my")
def api_my_action_items():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.get_my_action_items()

@planning_bp.route("/api/material-delivery", methods=["POST"])
def api_create_material_delivery():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.create_material_delivery()

@planning_bp.route("/api/planning/assign", methods=["POST"])
def api_assign_employee():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.assign_employee_to_day()

@planning_bp.route("/api/planning/employee/<int:employee_id>")
def api_employee_dashboard(employee_id):
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.get_employee_dashboard(employee_id)

@planning_bp.route("/api/planning/notifications")
def api_planning_notifications():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.get_planning_notifications()

@planning_bp.route("/api/planning/action-items/<int:id>/complete", methods=["POST"])
def api_complete_action_item(id):
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    request.view_args = {'id': id}
    return planning_api.quick_complete_action_item()

@planning_bp.route("/api/planning/tasks/<int:id>/reschedule", methods=["POST"])
def api_reschedule_task(id):
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    request.view_args = {'id': id}
    return planning_api.reschedule_task()

@planning_bp.route("/api/planning/suggestions")
def api_planning_suggestions():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.get_smart_suggestions()

# Day Planning routes (must be before /api/planning/day-plans/<int:plan_id>)
@planning_bp.route("/api/planning/day-plans/confirm", methods=["POST"])
def api_confirm_day_plans():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.confirm_day_plans()

@planning_bp.route("/api/planning/day-plans/copy", methods=["POST"])
def api_copy_day_plans():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.copy_day_plans()

@planning_bp.route("/api/planning/day-plans", methods=["GET", "POST"])
@planning_bp.route("/api/planning/day-plans/<target_date>", methods=["GET"])
def api_day_plans(target_date=None):
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    if request.method == "POST":
        return planning_api.create_day_plan()
    return planning_api.get_day_plans(target_date)

@planning_bp.route("/api/planning/day-plans/<int:plan_id>", methods=["PATCH"])
def api_update_day_plan(plan_id):
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.update_day_plan(plan_id)

@planning_bp.route("/api/planning/day-plans/<int:plan_id>", methods=["DELETE"])
def api_delete_day_plan(plan_id):
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.delete_day_plan(plan_id)

@planning_bp.route("/api/timesheets/delete-by-day", methods=["POST"])
def api_delete_timesheet_by_day():
    if not planning_api:
        return jsonify({"ok": False, "error": "planning_api not available"}), 500
    return planning_api.delete_timesheet_by_day()

# Planning HTML pages
@planning_bp.route("/planning/timeline")
def planning_timeline_page():
    return send_from_directory(".", "planning-timeline.html")

# Alias pro /timeline
@planning_bp.route("/timeline")
def timeline_alias():
    return send_from_directory(".", "planning-timeline.html")

@planning_bp.route("/planning/scenarios")
def planning_scenarios_page():
    return send_from_directory(".", "planning-scenarios.html")

@planning_bp.route("/planning/daily")
def planning_daily_page():
    return send_from_directory(".", "planning-daily.html")

@planning_bp.route("/planning/week")
def planning_week_page():
    return send_from_directory(".", "planning-week.html")

@planning_bp.route("/planning/costs")
def planning_costs_page():
    return send_from_directory(".", "planning-costs.html")

print("✅ Planning Module loaded")

# Additional routes from main.py
@planning_bp.route('/recurring-tasks')
def recurring_tasks_page():
    return send_from_directory('.', 'recurring-tasks.html')

@planning_bp.route('/api/recurring/templates')
def api_recurring_templates():
    return ext_api.get_recurring_templates()

@planning_bp.route('/api/recurring/templates', methods=['POST'])
def api_create_recurring_template():
    return ext_api.create_recurring_template()

@planning_bp.route('/api/recurring/generate', methods=['POST'])
def api_generate_recurring():
    return ext_api.generate_recurring_tasks()

# Materials 📦  
@planning_bp.route('/materials')
@planning_bp.route('/warehouse.html')
@planning_bp.route('/warehouse')
def materials_page():
    return send_from_directory('.', 'warehouse.html')


# Additional routes from main.py
@planning_bp.route('/api/contracts')
def api_contracts():
    return ext_api.get_maintenance_contracts()

# Seasonal planner 🌱
@planning_bp.route('/api/seasonal-tasks')
def api_seasonal():
    return ext_api.get_seasonal_tasks()

print("✅ Planning Extended Routes loaded")

# WAREHOUSE EXTENDED - Nadčasové rozšíření skladu
# ================================================================

# Import warehouse extended module
import warehouse_extended

# Set get_db reference
warehouse_extended.get_db = get_db

# Apply warehouse migrations on startup
@planning_bp.route('/api/planner/morning')
def api_morning_planner():
    """Get smart morning planning data."""
    user, err = require_auth()
    if err:
        return err
    
    try:
        db = get_db()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Zkontroluj existenci sloupce deadline
        task_cols = [r[1] for r in db.execute("PRAGMA table_info(tasks)").fetchall()]
        deadline_col = "COALESCE(t.deadline, t.due_date)" if "deadline" in task_cols else "t.due_date"
        
        # Today's tasks
        tasks = db.execute(f'''
            SELECT t.*, j.client as job_name
            FROM tasks t
            LEFT JOIN jobs j ON t.job_id = j.id
            WHERE {deadline_col} = ? AND t.status != 'done'
            ORDER BY t.id DESC
        ''', [today]).fetchall()
        
        # Urgent tasks
        urgent = db.execute(f'''
            SELECT t.*, j.client as job_name
            FROM tasks t
            LEFT JOIN jobs j ON t.job_id = j.id
            WHERE t.status NOT IN ('done', 'completed') AND {deadline_col} < ?
        ''', [today]).fetchall()
        
        # Active jobs
        jobs = db.execute('''
            SELECT * FROM jobs 
            WHERE status IN ('active', 'in_progress')
        ''').fetchall()
        
        # Overdue
        overdue = db.execute(f'''
            SELECT t.*, j.client as job_name
            FROM tasks t
            LEFT JOIN jobs j ON t.job_id = j.id
            WHERE {deadline_col} < ? AND t.status != 'done'
        ''', [today]).fetchall()
        
        return jsonify({
            'today_tasks': [dict(t) for t in tasks],
            'urgent_tasks': [dict(t) for t in urgent],
            'active_jobs': [dict(j) for j in jobs],
            'overdue_tasks': [dict(t) for t in overdue]
        })
    except Exception as e:
        print(f"[ERROR] api_morning_planner: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    # Pro lokální vývoj použij 127.0.0.1, pro Render použij 0.0.0.0
    is_render = os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME")
    host = "0.0.0.0" if is_render else "127.0.0.1"
    port = int(os.environ.get("PORT", 5000))
    debug = not is_render  # Debug mode jen lokálně
    
    print(f"[Server] Starting Flask app on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

