"""
Crew Control System API
API endpoints for the Team/Crew management system
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json

crew_bp = Blueprint('crew', __name__)

def get_db():
    """Get database connection - imported from main app"""
    from main import get_db as main_get_db
    return main_get_db()

# =====================================================
# EMPLOYEE SKILLS API
# =====================================================

@crew_bp.route('/api/crew/skills', methods=['GET', 'POST', 'DELETE'])
def api_crew_skills():
    """Manage employee skills"""
    db = get_db()
    
    if request.method == 'GET':
        emp_id = request.args.get('employee_id')
        
        if emp_id:
            skills = db.execute('''
                SELECT * FROM employee_skills 
                WHERE employee_id = ?
                ORDER BY level DESC, skill_name
            ''', [emp_id]).fetchall()
        else:
            skills = db.execute('''
                SELECT es.*, e.name as employee_name
                FROM employee_skills es
                LEFT JOIN employees e ON e.id = es.employee_id
                ORDER BY es.employee_id, es.level DESC
            ''').fetchall()
        
        return jsonify({
            'ok': True,
            'skills': [dict(s) for s in skills]
        })
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        
        emp_id = data.get('employee_id')
        skill_type = data.get('skill_type', '')
        skill_name = data.get('skill_name', '')
        level = data.get('level', 1)
        
        if not emp_id or not skill_name:
            return jsonify({'ok': False, 'error': 'Missing required fields'}), 400
        
        db.execute('''
            INSERT INTO employee_skills (employee_id, skill_type, skill_name, level, certified, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [emp_id, skill_type, skill_name, level, data.get('certified', 0), data.get('notes', '')])
        db.commit()
        
        return jsonify({'ok': True, 'message': 'Skill added'})
    
    elif request.method == 'DELETE':
        skill_id = request.args.get('id')
        if skill_id:
            db.execute('DELETE FROM employee_skills WHERE id = ?', [skill_id])
            db.commit()
        return jsonify({'ok': True})

# =====================================================
# EMPLOYEE CERTIFICATIONS API
# =====================================================

@crew_bp.route('/api/crew/certifications', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def api_crew_certifications():
    """Manage employee certifications"""
    db = get_db()
    
    if request.method == 'GET':
        emp_id = request.args.get('employee_id')
        
        if emp_id:
            certs = db.execute('''
                SELECT * FROM employee_certifications 
                WHERE employee_id = ?
                ORDER BY expiry_date
            ''', [emp_id]).fetchall()
        else:
            # Get all, including expiring soon
            certs = db.execute('''
                SELECT ec.*, e.name as employee_name
                FROM employee_certifications ec
                LEFT JOIN employees e ON e.id = ec.employee_id
                ORDER BY ec.expiry_date
            ''').fetchall()
        
        # Mark expired/expiring soon
        today = datetime.now().date()
        result = []
        for c in certs:
            cert = dict(c)
            if cert.get('expiry_date'):
                exp = datetime.strptime(cert['expiry_date'], '%Y-%m-%d').date()
                cert['is_expired'] = exp < today
                cert['expiring_soon'] = (exp - today).days <= 30 and exp >= today
            result.append(cert)
        
        return jsonify({'ok': True, 'certifications': result})
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        
        db.execute('''
            INSERT INTO employee_certifications 
            (employee_id, cert_name, cert_type, issued_date, expiry_date, issuer, document_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            data.get('employee_id'),
            data.get('cert_name', ''),
            data.get('cert_type', ''),
            data.get('issued_date'),
            data.get('expiry_date'),
            data.get('issuer', ''),
            data.get('document_url', ''),
            data.get('status', 'active')
        ])
        db.commit()
        
        return jsonify({'ok': True, 'message': 'Certification added'})
    
    elif request.method == 'DELETE':
        cert_id = request.args.get('id')
        if cert_id:
            db.execute('DELETE FROM employee_certifications WHERE id = ?', [cert_id])
            db.commit()
        return jsonify({'ok': True})

# =====================================================
# EMPLOYEE CAPACITY API
# =====================================================

@crew_bp.route('/api/crew/capacity', methods=['GET', 'POST', 'PATCH'])
def api_crew_capacity():
    """Manage employee capacity"""
    db = get_db()
    
    if request.method == 'GET':
        emp_id = request.args.get('employee_id')
        week = request.args.get('week')  # YYYY-MM-DD (Monday)
        
        # Default to current week
        if not week:
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            week = monday.strftime('%Y-%m-%d')
        
        if emp_id:
            capacity = db.execute('''
                SELECT * FROM employee_capacity 
                WHERE employee_id = ? AND week_start = ?
            ''', [emp_id, week]).fetchone()
            
            if capacity:
                return jsonify({'ok': True, 'capacity': dict(capacity)})
            else:
                # Return default
                return jsonify({
                    'ok': True,
                    'capacity': {
                        'employee_id': int(emp_id),
                        'week_start': week,
                        'planned_hours': 40,
                        'assigned_hours': 0,
                        'actual_hours': 0,
                        'utilization_pct': 0,
                        'status': 'available'
                    }
                })
        else:
            # Get all employees for the week
            capacities = db.execute('''
                SELECT ec.*, e.name as employee_name
                FROM employee_capacity ec
                LEFT JOIN employees e ON e.id = ec.employee_id
                WHERE ec.week_start = ?
            ''', [week]).fetchall()
            
            return jsonify({
                'ok': True,
                'week': week,
                'capacities': [dict(c) for c in capacities]
            })
    
    elif request.method == 'POST' or request.method == 'PATCH':
        data = request.get_json() or {}
        
        emp_id = data.get('employee_id')
        week = data.get('week_start')
        
        if not emp_id or not week:
            return jsonify({'ok': False, 'error': 'Missing employee_id or week_start'}), 400
        
        # Upsert
        existing = db.execute(
            'SELECT id FROM employee_capacity WHERE employee_id = ? AND week_start = ?',
            [emp_id, week]
        ).fetchone()
        
        if existing:
            db.execute('''
                UPDATE employee_capacity SET
                    planned_hours = ?,
                    assigned_hours = ?,
                    actual_hours = ?,
                    utilization_pct = ?,
                    status = ?,
                    notes = ?
                WHERE employee_id = ? AND week_start = ?
            ''', [
                data.get('planned_hours', 40),
                data.get('assigned_hours', 0),
                data.get('actual_hours', 0),
                data.get('utilization_pct', 0),
                data.get('status', 'available'),
                data.get('notes', ''),
                emp_id, week
            ])
        else:
            db.execute('''
                INSERT INTO employee_capacity 
                (employee_id, week_start, planned_hours, assigned_hours, actual_hours, utilization_pct, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', [
                emp_id, week,
                data.get('planned_hours', 40),
                data.get('assigned_hours', 0),
                data.get('actual_hours', 0),
                data.get('utilization_pct', 0),
                data.get('status', 'available'),
                data.get('notes', '')
            ])
        
        db.commit()
        return jsonify({'ok': True})

# =====================================================
# EMPLOYEE AVAILABILITY API
# =====================================================

@crew_bp.route('/api/crew/availability', methods=['GET', 'POST', 'DELETE'])
def api_crew_availability():
    """Manage employee availability (vacation, sick, etc.)"""
    db = get_db()
    
    if request.method == 'GET':
        emp_id = request.args.get('employee_id')
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        query = 'SELECT * FROM employee_availability WHERE 1=1'
        params = []
        
        if emp_id:
            query += ' AND employee_id = ?'
            params.append(emp_id)
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY date'
        
        avail = db.execute(query, params).fetchall()
        return jsonify({'ok': True, 'availability': [dict(a) for a in avail]})
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        
        db.execute('''
            INSERT INTO employee_availability 
            (employee_id, date, availability_type, start_time, end_time, all_day, notes, approved)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            data.get('employee_id'),
            data.get('date'),
            data.get('availability_type', 'vacation'),
            data.get('start_time'),
            data.get('end_time'),
            data.get('all_day', 1),
            data.get('notes', ''),
            data.get('approved', 0)
        ])
        db.commit()
        
        return jsonify({'ok': True, 'message': 'Availability recorded'})
    
    elif request.method == 'DELETE':
        avail_id = request.args.get('id')
        if avail_id:
            db.execute('DELETE FROM employee_availability WHERE id = ?', [avail_id])
            db.commit()
        return jsonify({'ok': True})

# =====================================================
# AI INSIGHTS API
# =====================================================

@crew_bp.route('/api/crew/ai-insights', methods=['GET'])
def api_crew_ai_insights():
    """Get AI-generated insights about team"""
    db = get_db()
    
    insights = []
    
    try:
        # Get all employees with their capacity data
        employees = db.execute('SELECT * FROM employees').fetchall()
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime('%Y-%m-%d')
        week_end = (monday + timedelta(days=6)).strftime('%Y-%m-%d')
        
        for emp in employees:
            emp_dict = dict(emp)
            emp_id = emp_dict['id']
            
            # Calculate utilization from timesheets
            ts_result = db.execute('''
                SELECT COALESCE(SUM(hours), 0) as total
                FROM timesheets
                WHERE employee_id = ? AND date >= ? AND date <= ?
            ''', [emp_id, week_start, week_end]).fetchone()
            
            hours = ts_result['total'] if ts_result else 0
            utilization = (hours / 40) * 100 if hours else 0
            
            # Check for overload
            if utilization > 100:
                insights.append({
                    'type': 'warning',
                    'priority': 'high',
                    'employee_id': emp_id,
                    'employee_name': emp_dict['name'],
                    'message': f"{emp_dict['name']} je přetížen/a ({utilization:.0f}% kapacity). Zvažte přerozdělit úkoly.",
                    'metric': 'utilization',
                    'value': utilization
                })
            elif utilization > 90:
                insights.append({
                    'type': 'warning',
                    'priority': 'medium',
                    'employee_id': emp_id,
                    'employee_name': emp_dict['name'],
                    'message': f"{emp_dict['name']} se blíží limitu kapacity ({utilization:.0f}%).",
                    'metric': 'utilization',
                    'value': utilization
                })
            elif utilization < 30 and utilization > 0:
                insights.append({
                    'type': 'info',
                    'priority': 'low',
                    'employee_id': emp_id,
                    'employee_name': emp_dict['name'],
                    'message': f"{emp_dict['name']} má volnou kapacitu ({100-utilization:.0f}% k dispozici). Ideální pro nové projekty.",
                    'metric': 'availability',
                    'value': 100 - utilization
                })
        
        # Check for expiring certifications
        certs = db.execute('''
            SELECT ec.*, e.name as employee_name
            FROM employee_certifications ec
            LEFT JOIN employees e ON e.id = ec.employee_id
            WHERE ec.expiry_date IS NOT NULL
            AND ec.expiry_date >= date('now')
            AND ec.expiry_date <= date('now', '+30 days')
        ''').fetchall()
        
        for cert in certs:
            cert_dict = dict(cert)
            insights.append({
                'type': 'warning',
                'priority': 'medium',
                'employee_id': cert_dict['employee_id'],
                'employee_name': cert_dict['employee_name'],
                'message': f"Certifikace '{cert_dict['cert_name']}' pro {cert_dict['employee_name']} vyprší {cert_dict['expiry_date']}.",
                'metric': 'certification',
                'value': cert_dict['expiry_date']
            })
        
        # General balance insight
        if len(employees) > 0:
            avg_util = sum([
                (db.execute('''
                    SELECT COALESCE(SUM(hours), 0) / 40.0 * 100 as util
                    FROM timesheets
                    WHERE employee_id = ? AND date >= ? AND date <= ?
                ''', [dict(e)['id'], week_start, week_end]).fetchone()['util'] or 0)
                for e in employees
            ]) / len(employees)
            
            if 60 <= avg_util <= 85:
                insights.append({
                    'type': 'success',
                    'priority': 'low',
                    'message': f'Tým je v optimální rovnováze (průměrné vytížení {avg_util:.0f}%).',
                    'metric': 'balance',
                    'value': avg_util
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        insights.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 2))
        
    except Exception as e:
        print(f"[ERROR] AI Insights: {e}")
        insights.append({
            'type': 'info',
            'priority': 'low',
            'message': 'Analýza týmu probíhá...'
        })
    
    return jsonify({
        'ok': True,
        'insights': insights,
        'generated_at': datetime.now().isoformat()
    })

# =====================================================
# TEAM DASHBOARD API
# =====================================================

@crew_bp.route('/api/crew/dashboard', methods=['GET'])
def api_crew_dashboard():
    """Get team dashboard data"""
    db = get_db()
    
    try:
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime('%Y-%m-%d')
        week_end = (monday + timedelta(days=6)).strftime('%Y-%m-%d')
        
        # Get employees with calculated metrics
        employees = db.execute('SELECT * FROM employees WHERE status != "inactive"').fetchall()
        
        team_data = []
        total_utilization = 0
        overloaded_count = 0
        underutilized_count = 0
        
        for emp in employees:
            emp_dict = dict(emp)
            emp_id = emp_dict['id']
            
            # Weekly hours
            ts = db.execute('''
                SELECT COALESCE(SUM(hours), 0) as total
                FROM timesheets
                WHERE employee_id = ? AND date >= ? AND date <= ?
            ''', [emp_id, week_start, week_end]).fetchone()
            
            weekly_hours = ts['total'] if ts else 0
            utilization = (weekly_hours / 40) * 100
            
            total_utilization += utilization
            if utilization > 100:
                overloaded_count += 1
            elif utilization < 50:
                underutilized_count += 1
            
            # Active jobs count
            jobs_count = db.execute('''
                SELECT COUNT(*) as cnt FROM job_employees 
                WHERE employee_id = ?
            ''', [emp_id]).fetchone()['cnt']
            
            emp_dict['weekly_hours'] = weekly_hours
            emp_dict['utilization'] = utilization
            emp_dict['active_jobs'] = jobs_count
            emp_dict['status_color'] = (
                'red' if utilization > 100 else
                'orange' if utilization > 85 else
                'blue' if utilization < 50 else
                'green'
            )
            
            team_data.append(emp_dict)
        
        avg_utilization = total_utilization / len(employees) if employees else 0
        
        # AI Balance score
        optimal_count = sum(1 for e in team_data if 60 <= e['utilization'] <= 85)
        ai_score = (optimal_count / len(employees)) * 100 if employees else 0
        
        return jsonify({
            'ok': True,
            'stats': {
                'total_members': len(employees),
                'active_today': len([e for e in team_data if e.get('status') != 'vacation']),
                'avg_utilization': round(avg_utilization),
                'overloaded': overloaded_count,
                'underutilized': underutilized_count,
                'ai_balance_score': round(ai_score)
            },
            'team': team_data,
            'week': {
                'start': week_start,
                'end': week_end
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Crew Dashboard: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


def register_crew_api(app):
    """Register the crew blueprint with the Flask app"""
    app.register_blueprint(crew_bp)
