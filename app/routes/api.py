# Green David App
from flask import Blueprint, jsonify, request, send_from_directory, send_file, render_template
from datetime import datetime
import os, io, json
from app.database import get_db
from app.utils.permissions import require_auth, require_role, requires_role
from app.config import UPLOAD_FOLDER

api_bp = Blueprint('api', __name__)


# Miscellaneous API routes from main.py
@api_bp.route("/trainings.html")
def page_trainings():
    return render_template("trainings.html")

@api_bp.route("/api/admin/export-all", methods=["GET"])
@requires_role('owner', 'admin')
def api_admin_export_all():
    """Export všech tabulek do JSON (pouze owner/admin)."""
    db = get_db()
    tables = [r["name"] for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()]
    export = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "db_path": os.environ.get("DB_PATH") or "/var/data/app.db",
        "tables": {},
    }
    for t in tables:
        rows = db.execute(f"SELECT * FROM {t}").fetchall()
        export["tables"][t] = [dict(r) for r in rows]
    payload = json.dumps(export, ensure_ascii=False, indent=2)
    buf = io.BytesIO(payload.encode("utf-8"))
    filename = f"green-david-export-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name=filename)






# Additional routes from main.py
@api_bp.route('/ai')
@api_bp.route('/ai-operator')
def ai_operator_page():
    return send_from_directory('.', 'ai-operator.html')

print("✅ AI Operátor Module loaded")

# ================================================================
# VELITELSKÝ PANEL - Command Reports 🛰️
# ================================================================

@api_bp.route('/reports')
@api_bp.route('/api/ai/estimate', methods=['POST'])
def api_ai_estimate():
    """Generate AI estimate for a job based on description/photo."""
    user, err = require_auth()
    if err:
        return err
    
    try:
        data = request.get_json() or {}
        description = data.get('description', '')
        photo_base64 = data.get('photo')
        job_type = data.get('type', 'general')
        
        # Simple rule-based estimates (can be replaced with actual AI)
        estimates = {
            'plot': {'days': 3, 'material': 12000, 'price': 35000},
            'zahrada': {'days': 5, 'material': 8000, 'price': 45000},
            'terasa': {'days': 4, 'material': 15000, 'price': 50000},
            'general': {'days': 2, 'material': 5000, 'price': 20000}
        }
        
        # Parse description for keywords
        desc_lower = description.lower()
        estimate_type = 'general'
        
        for keyword in ['plot', 'oplocení', 'plotov']:
            if keyword in desc_lower:
                estimate_type = 'plot'
                break
        for keyword in ['zahrad', 'trávník', 'vysázení']:
            if keyword in desc_lower:
                estimate_type = 'zahrada'
                break
        for keyword in ['teras', 'dlažb', 'dřev']:
            if keyword in desc_lower:
                estimate_type = 'terasa'
                break
        
        # Extract numbers from description (e.g., "50m plot")
        import re
        numbers = re.findall(r'(\d+)\s*m', desc_lower)
        multiplier = 1
        if numbers:
            meters = int(numbers[0])
            multiplier = max(1, meters / 20)  # Base estimate is for ~20m
        
        base = estimates[estimate_type]
        
        result = {
            'type': estimate_type,
            'estimated_days': round(base['days'] * multiplier),
            'estimated_material': round(base['material'] * multiplier),
            'estimated_price': round(base['price'] * multiplier),
            'confidence': 0.7,
            'note': f'Odhad pro typ "{estimate_type}" na základě popisu'
        }
        
        return jsonify(result)
    except Exception as e:
        print(f"[ERROR] api_ai_estimate: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# CREW CONTROL SYSTEM API
# ============================================================

@api_bp.route('/api/team/<int:employee_id>/ai-analysis', methods=['GET'])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_team_member_ai_analysis(employee_id):
    """AI analýza člena týmu"""
    u, err = require_auth()
    if err:
        return err
    
    db = get_db()
    try:
        from datetime import datetime, timedelta
        
        # Získej zaměstnance
        employee = db.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if not employee:
            return jsonify({'ok': False, 'error': 'employee_not_found'}), 404
        
        employee_dict = dict(employee)
        
        # Získej nebo vytvoř profil
        profile = db.execute(
            "SELECT * FROM team_member_profile WHERE employee_id = ?",
            (employee_id,)
        ).fetchone()
        
        if not profile:
            # Vytvoř defaultní profil
            db.execute("""
                INSERT INTO team_member_profile (employee_id, weekly_capacity_hours)
                VALUES (?, 40.0)
            """, (employee_id,))
            db.commit()
            profile = db.execute(
                "SELECT * FROM team_member_profile WHERE employee_id = ?",
                (employee_id,)
            ).fetchone()
        
        profile_dict = dict(profile)
        
        # Parse JSON fields
        import json as json_lib
        try:
            profile_dict['skills'] = json_lib.loads(profile_dict.get('skills') or '[]')
            profile_dict['certifications'] = json_lib.loads(profile_dict.get('certifications') or '[]')
            profile_dict['preferred_work_types'] = json_lib.loads(profile_dict.get('preferred_work_types') or '[]')
        except:
            profile_dict['skills'] = []
            profile_dict['certifications'] = []
            profile_dict['preferred_work_types'] = []
        
        # Shromáždě data pro analýzu
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime("%Y-%m-%d")
        week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        
        # Aktuální hodiny tento týden
        timesheet_rows = db.execute(
            "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
            (employee_id, week_start, week_end)
        ).fetchone()
        current_hours = round(timesheet_rows["total"] or 0, 1)
        
        # Počet týdnů přetížení (posledních 4 týdny)
        weeks_overloaded = 0
        for i in range(4):
            week_start_check = (monday - timedelta(weeks=i)).strftime("%Y-%m-%d")
            week_end_check = (monday - timedelta(weeks=i) + timedelta(days=6)).strftime("%Y-%m-%d")
            week_hours = db.execute(
                "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
                (employee_id, week_start_check, week_end_check)
            ).fetchone()
            week_total = round(week_hours["total"] or 0, 1)
            weekly_capacity = profile_dict.get('weekly_capacity_hours', 40.0)
            if (week_total / weekly_capacity * 100) > 90:
                weeks_overloaded += 1
        
        capacity_percent = calculate_capacity_percent(profile_dict, current_hours)
        capacity_status = calculate_capacity_status(capacity_percent)
        burnout_risk = calculate_burnout_risk(profile_dict, capacity_percent, weeks_overloaded)
        
        # Aktuální aktivní zakázky
        active_jobs = db.execute(
            "SELECT COUNT(DISTINCT job_id) as count FROM job_assignments WHERE employee_id=?",
            (employee_id,)
        ).fetchone()
        current_active_jobs = active_jobs["count"] or 0
        
        # Generuj doporučení
        recommendations = []
        warnings = []
        
        if burnout_risk in ['high', 'critical']:
            warnings.append({
                'type': 'burnout_warning',
                'priority': 'high',
                'message': f'{employee_dict.get("name", "Zaměstnanec")} je {weeks_overloaded} týdny přetížený/á. Doporučuji snížit zátěž.'
            })
        
        if capacity_status == 'underutilized' and weeks_overloaded == 0:
            recommendations.append({
                'type': 'underutilized',
                'priority': 'low',
                'message': f'{employee_dict.get("name", "Zaměstnanec")} má volnou kapacitu. Vhodný/á pro nové zakázky.'
            })
        
        if current_active_jobs > 5:
            warnings.append({
                'type': 'too_many_jobs',
                'priority': 'medium',
                'message': f'{employee_dict.get("name", "Zaměstnanec")} má {current_active_jobs} aktivních zakázek. Zvažte redistribuci.'
            })
        
        analysis_data = {
            'employee_id': employee_id,
            'name': employee_dict.get('name', ''),
            'current_hours': current_hours,
            'weekly_capacity': profile_dict.get('weekly_capacity_hours', 40.0),
            'capacity_percent': round(capacity_percent, 1),
            'capacity_status': capacity_status,
            'weeks_overloaded': weeks_overloaded,
            'burnout_risk_level': burnout_risk,
            'current_active_jobs': current_active_jobs,
            'performance_stability_score': profile_dict.get('performance_stability_score', 0.5),
            'ai_balance_score': profile_dict.get('ai_balance_score', 0.5),
            'skills': profile_dict['skills'],
            'certifications': profile_dict['certifications']
        }
        
        return jsonify({
            'ok': True,
            'employee_id': employee_id,
            'analysis': analysis_data,
            'recommendations': recommendations,
            'warnings': warnings
        })
    except Exception as e:
        print(f"[ERROR] api_team_member_ai_analysis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@api_bp.route('/api/team/ai-crew-assistant', methods=['GET'])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_ai_crew_assistant():
    """AI Crew Assistant - celkový přehled a doporučení"""
    u, err = require_auth()
    if err:
        return err
    
    db = get_db()
    try:
        from datetime import datetime, timedelta
        
        employees = db.execute("SELECT * FROM employees WHERE status = 'active' OR status IS NULL ORDER BY name").fetchall()
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime("%Y-%m-%d")
        week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        
        insights = []
        warnings = []
        recommendations = []
        
        # Celková kapacita a plánované hodiny
        total_capacity = 0
        total_planned = 0
        
        for emp in employees:
            emp_dict = dict(emp)
            emp_id = emp_dict['id']
            emp_name = emp_dict.get('name', 'Zaměstnanec')
            
            # Získej profil
            profile = db.execute(
                "SELECT * FROM team_member_profile WHERE employee_id = ?",
                (emp_id,)
            ).fetchone()
            
            if not profile:
                weekly_capacity = 40.0
                skills = []
            else:
                profile_dict = dict(profile)
                weekly_capacity = profile_dict.get('weekly_capacity_hours', 40.0)
                skills_json = profile_dict.get('skills', '[]')
                try:
                    import json
                    skills = json.loads(skills_json) if isinstance(skills_json, str) else (skills_json or [])
                except:
                    skills = []
            
            total_capacity += weekly_capacity
            
            # Aktuální hodiny tento týden
            timesheet_result = db.execute(
                "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
                (emp_id, week_start, week_end)
            ).fetchone()
            worked_hours = round(timesheet_result["total"] or 0, 1)
            total_planned += worked_hours
            
            utilization = (worked_hours / weekly_capacity * 100) if weekly_capacity > 0 else 0
            
            # === PRAVIDLO 1: Přetížení (> 100%) ===
            if utilization > 100:
                warnings.append({
                    'type': 'alert',
                    'priority': 'high',
                    'icon': 'warning',
                    'member_id': emp_id,
                    'member_name': emp_name,
                    'message': f'{emp_name} je přetížen/a ({utilization:.0f}% kapacity)',
                    'suggestion': 'Přerozdělit úkoly nebo odložit termíny',
                    'action': 'redistribute_tasks'
                })
            
            # === PRAVIDLO 2: Vysoké vytížení (85-100%) ===
            elif utilization > 85:
                warnings.append({
                    'type': 'warning',
                    'priority': 'medium',
                    'icon': 'attention',
                    'member_id': emp_id,
                    'member_name': emp_name,
                    'message': f'{emp_name} má vysoké vytížení ({utilization:.0f}%)',
                    'suggestion': 'Sledovat a nepřidávat další úkoly',
                    'action': 'monitor'
                })
            
            # === PRAVIDLO 3: Nevyužitá kapacita (< 30%) ===
            elif utilization < 30:
                recommendations.append({
                    'type': 'info',
                    'priority': 'low',
                    'icon': 'opportunity',
                    'member_id': emp_id,
                    'member_name': emp_name,
                    'message': f'{emp_name} má volnou kapacitu ({100-utilization:.0f}% volno)',
                    'suggestion': 'Vhodný/á pro nové zakázky nebo pomoc kolegům',
                    'action': 'assign_more'
                })
            
            # === PRAVIDLO 4: Dlouhodobé přetížení (burnout risk) ===
            weeks_overloaded = 0
            for week_i in range(4):
                week_start_check = (monday - timedelta(weeks=week_i)).strftime("%Y-%m-%d")
                week_end_check = (monday - timedelta(weeks=week_i) + timedelta(days=6)).strftime("%Y-%m-%d")
                week_hours_result = db.execute(
                    "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
                    (emp_id, week_start_check, week_end_check)
                ).fetchone()
                week_total = round(week_hours_result["total"] or 0, 1)
                if weekly_capacity > 0 and (week_total / weekly_capacity * 100) > 90:
                    weeks_overloaded += 1
            if weeks_overloaded >= 2:
                warnings.append({
                    'type': 'alert',
                    'priority': 'high',
                    'icon': 'burnout',
                    'member_id': emp_id,
                    'member_name': emp_name,
                    'message': f'{emp_name} je přetížen/a už {weeks_overloaded} týdny',
                    'suggestion': 'Riziko vyhoření - zvážit volno nebo snížení zátěže',
                    'action': 'prevent_burnout'
                })
        
        # === PRAVIDLO 5: Kapacitní mezera tento týden ===
        if total_planned > total_capacity:
            gap = total_planned - total_capacity
            warnings.append({
                'type': 'alert',
                'priority': 'high',
                'icon': 'capacity_gap',
                'message': f'Tento týden chybí {gap:.0f} hodin kapacity',
                'suggestion': 'Zvážit přesun termínů nebo externí pomoc',
                'action': 'resolve_capacity'
            })
        
        # === PRAVIDLO 6: Nerovnoměrné rozdělení ===
        # Calculate balance score (simplified)
        utilizations = []
        for emp in employees:
            emp_id = emp['id']
            profile = db.execute("SELECT weekly_capacity_hours FROM team_member_profile WHERE employee_id = ?", (emp_id,)).fetchone()
            capacity = profile['weekly_capacity_hours'] if profile else 40.0
            if capacity > 0:
                timesheet_result = db.execute(
                    "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
                    (emp_id, week_start, week_end)
                ).fetchone()
                worked = round(timesheet_result["total"] or 0, 1)
                utilizations.append((worked / capacity * 100) if capacity > 0 else 0)
        
        balance_score = None
        if len(utilizations) >= 2:
            import statistics
            try:
                std_dev = statistics.stdev(utilizations)
                balance_score = max(0, min(100, round(100 - (std_dev * 2))))
            except:
                pass
        if balance_score is not None and balance_score < 50:
            warnings.append({
                'type': 'warning',
                'priority': 'medium',
                'icon': 'imbalance',
                'message': 'Práce je nerovnoměrně rozdělena v týmu',
                'suggestion': 'Některé členy přetěžujete, jiní mají volno',
                'action': 'rebalance_team'
            })
        
        # Seřadit podle priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        all_recommendations = warnings + recommendations
        all_recommendations.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 99))
        
        return jsonify({
            'ok': True,
            'insights': insights,
            'warnings': [r for r in all_recommendations if r.get('type') in ('alert', 'warning')],
            'recommendations': [r for r in all_recommendations if r.get('type') in ('info', 'suggestion')],
            'capacity_forecast': {
                'total_capacity': total_capacity,
                'total_planned': total_planned,
                'utilization_percent': round((total_planned / total_capacity * 100) if total_capacity > 0 else 0, 1)
            }
        })
    except Exception as e:
        print(f"[ERROR] api_ai_crew_assistant: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@api_bp.route('/api/team/ai-recommendations', methods=['GET'])
@requires_role('owner', 'admin', 'manager', 'lander')
def api_team_ai_recommendations():
    """AI doporučení pro tým (alias pro ai-crew-assistant s jiným formátem)"""
    u, err = require_auth()
    if err:
        return err
    
    db = get_db()
    try:
        from datetime import datetime, timedelta
        
        employees = db.execute("SELECT * FROM employees ORDER BY name").fetchall()
        recommendations = []
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        week_start = monday.strftime("%Y-%m-%d")
        week_end = (monday + timedelta(days=6)).strftime("%Y-%m-%d")
        
        for emp in employees:
            emp_dict = dict(emp)
            emp_id = emp_dict['id']
            
            # Získej profil
            profile = db.execute(
                "SELECT * FROM team_member_profile WHERE employee_id = ?",
                (emp_id,)
            ).fetchone()
            
            if not profile:
                continue
            
            profile_dict = dict(profile)
            
            # Aktuální hodiny
            timesheet_rows = db.execute(
                "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
                (emp_id, week_start, week_end)
            ).fetchone()
            current_hours = round(timesheet_rows["total"] or 0, 1)
            
            weekly_capacity = profile_dict.get('weekly_capacity_hours', 40.0)
            capacity_percent = min(100, (current_hours / weekly_capacity * 100)) if weekly_capacity > 0 else 0
            
            # Počet týdnů přetížení
            weeks_overloaded = 0
            for week_i in range(4):
                week_start_check = (monday - timedelta(weeks=week_i)).strftime("%Y-%m-%d")
                week_end_check = (monday - timedelta(weeks=week_i) + timedelta(days=6)).strftime("%Y-%m-%d")
                week_hours_result = db.execute(
                    "SELECT SUM(COALESCE(duration_minutes, CAST(hours * 60 AS INTEGER))) / 60.0 as total FROM timesheets WHERE employee_id=? AND date >= ? AND date <= ?",
                    (emp_id, week_start_check, week_end_check)
                ).fetchone()
                week_total = round(week_hours_result["total"] or 0, 1)
                if weekly_capacity > 0 and (week_total / weekly_capacity * 100) > 90:
                    weeks_overloaded += 1
            
            # Pravidlo 1: Přetížení
            if capacity_percent > 90:
                recommendations.append({
                    'type': 'warning',
                    'priority': 'high',
                    'employee_id': emp_id,
                    'employee_name': emp_dict.get('name', ''),
                    'message': f'{emp_dict.get("name", "Zaměstnanec")} je přetížen/a ({int(capacity_percent)}% kapacity)',
                    'suggestion': 'Doporučuji přerozdělit úkoly'
                })
            
            # Pravidlo 2: Burnout risk
            burnout_risk = profile_dict.get('burnout_risk_level', 'normal')
            if burnout_risk in ['high', 'critical']:
                recommendations.append({
                    'type': 'alert',
                    'priority': 'high',
                    'employee_id': emp_id,
                    'employee_name': emp_dict.get('name', ''),
                    'message': f'{emp_dict.get("name", "Zaměstnanec")} má vysoké riziko vyhoření',
                    'suggestion': 'Zvažte snížení zátěže nebo volno'
                })
            
            # Pravidlo 3: Nevyužitý
            if capacity_percent < 40:
                recommendations.append({
                    'type': 'info',
                    'priority': 'low',
                    'employee_id': emp_id,
                    'employee_name': emp_dict.get('name', ''),
                    'message': f'{emp_dict.get("name", "Zaměstnanec")} má volnou kapacitu ({int(capacity_percent)}%)',
                    'suggestion': 'Vhodný/á pro nové zakázky'
                })
        
        # Seřadit podle priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 99))
        
        return jsonify({'ok': True, 'recommendations': recommendations})
    except Exception as e:
        print(f"[ERROR] api_team_ai_recommendations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

# Additional routes from main.py
@api_bp.route('/api/weather', methods=['GET'])
def api_weather():
    """Získá aktuální počasí pro zadané město (default: Příbram)"""
    u, err = require_auth()
    if err: return err
    
    city = request.args.get('city', 'Příbram')
    
    # Open-Meteo API - free, no API key required
    # Koordináty pro Příbram, CZ
    locations = {
        'Příbram': {'lat': 49.6897, 'lon': 14.0101},
        'Praha': {'lat': 50.0755, 'lon': 14.4378},
        'Brno': {'lat': 49.1951, 'lon': 16.6068},
        'Ostrava': {'lat': 49.8209, 'lon': 18.2625},
        'Plzeň': {'lat': 49.7384, 'lon': 13.3736},
    }
    
    coords = locations.get(city, locations['Příbram'])
    
    try:
        import urllib.request
        import urllib.error
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=Europe%2FPrague&forecast_days=5"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'GreenDavidApp/1.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Weather code to description and icon
        weather_codes = {
            0: {'desc': 'Jasno', 'icon': '☀️'},
            1: {'desc': 'Převážně jasno', 'icon': '🌤️'},
            2: {'desc': 'Polojasno', 'icon': '⛅'},
            3: {'desc': 'Zataženo', 'icon': '☁️'},
            45: {'desc': 'Mlha', 'icon': '🌫️'},
            48: {'desc': 'Mrznoucí mlha', 'icon': '🌫️'},
            51: {'desc': 'Mrholení', 'icon': '🌧️'},
            53: {'desc': 'Mrholení', 'icon': '🌧️'},
            55: {'desc': 'Mrholení', 'icon': '🌧️'},
            61: {'desc': 'Déšť', 'icon': '🌧️'},
            63: {'desc': 'Déšť', 'icon': '🌧️'},
            65: {'desc': 'Silný déšť', 'icon': '🌧️'},
            71: {'desc': 'Sněžení', 'icon': '🌨️'},
            73: {'desc': 'Sněžení', 'icon': '🌨️'},
            75: {'desc': 'Husté sněžení', 'icon': '🌨️'},
            80: {'desc': 'Přeháňky', 'icon': '🌦️'},
            81: {'desc': 'Přeháňky', 'icon': '🌦️'},
            82: {'desc': 'Silné přeháňky', 'icon': '🌦️'},
            95: {'desc': 'Bouřka', 'icon': '⛈️'},
            96: {'desc': 'Bouřka s krupobitím', 'icon': '⛈️'},
            99: {'desc': 'Bouřka s krupobitím', 'icon': '⛈️'},
        }
        
        current = data.get('current', {})
        daily = data.get('daily', {})
        
        weather_code = current.get('weather_code', 0)
        weather_info = weather_codes.get(weather_code, {'desc': 'Neznámo', 'icon': '❓'})
        
        # Forecast for next days
        forecast = []
        if daily:
            for i in range(min(5, len(daily.get('time', [])))):
                day_code = daily['weather_code'][i] if i < len(daily.get('weather_code', [])) else 0
                day_info = weather_codes.get(day_code, {'desc': 'Neznámo', 'icon': '❓'})
                forecast.append({
                    'date': daily['time'][i],
                    'temp_max': daily['temperature_2m_max'][i] if i < len(daily.get('temperature_2m_max', [])) else None,
                    'temp_min': daily['temperature_2m_min'][i] if i < len(daily.get('temperature_2m_min', [])) else None,
                    'precipitation_prob': daily['precipitation_probability_max'][i] if i < len(daily.get('precipitation_probability_max', [])) else 0,
                    'description': day_info['desc'],
                    'icon': day_info['icon']
                })
        
        # Gardening advice based on weather
        advice = []
        temp = current.get('temperature_2m', 15)
        humidity = current.get('relative_humidity_2m', 50)
        wind = current.get('wind_speed_10m', 0)
        
        if weather_code in [61, 63, 65, 80, 81, 82]:
            advice.append("🌧️ Dnes prší - ideální den pro práci ve skleníku")
        elif weather_code in [71, 73, 75]:
            advice.append("🌨️ Sněží - pozor na mráz, zkontrolujte ochranu rostlin")
        elif weather_code in [0, 1] and temp > 20:
            advice.append("☀️ Horký den - nezapomeňte zavlažovat")
        
        if temp < 5:
            advice.append("🥶 Nízká teplota - pozor na mráz citlivých rostlin")
        elif temp > 30:
            advice.append("🌡️ Tropické teploty - ranní nebo večerní práce doporučena")
        
        if wind > 30:
            advice.append("💨 Silný vítr - odložte postřiky a mulčování")
        
        if humidity > 80 and temp > 15:
            advice.append("💧 Vysoká vlhkost - sledujte plísňové choroby")
        
        return jsonify({
            'success': True,
            'city': city,
            'current': {
                'temperature': current.get('temperature_2m'),
                'humidity': current.get('relative_humidity_2m'),
                'wind_speed': current.get('wind_speed_10m'),
                'weather_code': weather_code,
                'description': weather_info['desc'],
                'icon': weather_info['icon']
            },
            'forecast': forecast,
            'advice': advice
        })
        
    except urllib.error.URLError as e:
        print(f"[WARNING] Weather API network error: {e}")
        return jsonify({
            'success': False,
            'message': 'Nelze načíst počasí - zkontrolujte připojení',
            'offline': True
        }), 503
    except Exception as e:
        print(f"[ERROR] api_weather: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba při načítání počasí: {str(e)}'
        }), 500


# ==================== DASHBOARD STATS API ====================
@api_bp.route('/api/dashboard/stats', methods=['GET'])
def api_dashboard_stats():
    """Rychlé statistiky pro dashboard"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        today = date.today().isoformat()
        week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()
        
        # Active jobs
        active_jobs = db.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE status IN ('Plán', 'Probíhá')"
        ).fetchone()['cnt']
        
        # Pending tasks
        pending_tasks = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status IN ('open', 'in-progress')"
        ).fetchone()['cnt']
        
        # Urgent tasks (due today)
        urgent_tasks = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE due_date = ? AND status != 'completed'",
            (today,)
        ).fetchone()['cnt']
        
        # Hours this week
        hours_week = db.execute(
            "SELECT COALESCE(SUM(hours), 0) as total FROM timesheets WHERE date >= ?",
            (week_start,)
        ).fetchone()['total']
        
        # Employees count
        emp_count = db.execute("SELECT COUNT(*) as cnt FROM employees").fetchone()['cnt']
        
        # Low stock items
        low_stock = db.execute(
            "SELECT COUNT(*) as cnt FROM warehouse_items WHERE quantity <= min_quantity AND min_quantity > 0"
        ).fetchone()['cnt']
        
        return jsonify({
            'success': True,
            'stats': {
                'active_jobs': active_jobs,
                'pending_tasks': pending_tasks,
                'urgent_tasks': urgent_tasks,
                'hours_week': round(hours_week, 1),
                'employee_count': emp_count,
                'low_stock_items': low_stock
            }
        })
        
    except Exception as e:
        print(f"[ERROR] api_dashboard_stats: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


# ==================== DEADLINE CHECK & NOTIFICATIONS ====================
@api_bp.route('/api/check-deadlines', methods=['POST'])
def api_check_deadlines():
    """Check for upcoming deadlines and create notifications.
    Can be called periodically (e.g., once per day via cron or manual trigger).
    """
    u, err = require_auth()
    if err: return err
    
    # Only admin/owner can trigger this
    if normalize_role(u.get("role")) not in ("owner", "admin"):
        return jsonify({"ok": False, "error": "forbidden"}), 403
    
    try:
        db = get_db()
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        notifications_created = 0
        
        # Tasks due today
        tasks_today = db.execute("""
            SELECT t.id, t.title, t.employee_id, ta.employee_id as assigned_emp
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            WHERE t.due_date = ? AND t.status != 'completed'
        """, (today.isoformat(),)).fetchall()
        
        for task in tasks_today:
            emp_id = task['assigned_emp'] or task['employee_id']
            if emp_id:
                create_notification(
                    employee_id=emp_id,
                    kind="deadline",
                    title="⏰ Deadline dnes!",
                    body=f"Úkol '{task['title']}' má deadline dnes",
                    entity_type="task",
                    entity_id=task['id']
                )
                notifications_created += 1
        
        # Tasks due tomorrow
        tasks_tomorrow = db.execute("""
            SELECT t.id, t.title, t.employee_id, ta.employee_id as assigned_emp
            FROM tasks t
            LEFT JOIN task_assignees ta ON t.id = ta.task_id
            WHERE t.due_date = ? AND t.status != 'completed'
        """, (tomorrow.isoformat(),)).fetchall()
        
        for task in tasks_tomorrow:
            emp_id = task['assigned_emp'] or task['employee_id']
            if emp_id:
                create_notification(
                    employee_id=emp_id,
                    kind="deadline",
                    title="📅 Deadline zítra",
                    body=f"Úkol '{task['title']}' má deadline zítra",
                    entity_type="task",
                    entity_id=task['id']
                )
                notifications_created += 1
        
        # Jobs ending soon (within 3 days)
        soon = today + timedelta(days=3)
        jobs_soon = db.execute("""
            SELECT id, title, date FROM jobs
            WHERE date BETWEEN ? AND ? AND status != 'Dokončeno'
        """, (today.isoformat(), soon.isoformat())).fetchall()
        
        # Notify all admins about jobs ending soon
        admins = db.execute("SELECT id FROM users WHERE role IN ('owner', 'admin')").fetchall()
        for job in jobs_soon:
            for admin in admins:
                create_notification(
                    user_id=admin['id'],
                    kind="job",
                    title="🏗️ Zakázka končí brzy",
                    body=f"Zakázka '{job['title']}' má termín {job['date']}",
                    entity_type="job",
                    entity_id=job['id']
                )
                notifications_created += 1
        
        # Low stock alerts
        low_stock = db.execute("""
            SELECT id, name, quantity, min_quantity FROM warehouse_items
            WHERE quantity <= min_quantity AND min_quantity > 0
        """).fetchall()
        
        for item in low_stock:
            for admin in admins:
                create_notification(
                    user_id=admin['id'],
                    kind="stock",
                    title="📦 Nízký stav skladu",
                    body=f"'{item['name']}' - zbývá {item['quantity']} ks (min: {item['min_quantity']})",
                    entity_type="warehouse",
                    entity_id=item['id']
                )
                notifications_created += 1
        
        return jsonify({
            'ok': True,
            'notifications_created': notifications_created
        })
        
    except Exception as e:
        print(f"[ERROR] api_check_deadlines: {e}")
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


# ==================== QUICK ACTIONS API ====================
@api_bp.route('/api/quick-add', methods=['POST'])
def api_quick_add():
    """Rychlé přidání položky (task, note, timesheet) z dashboardu"""
    u, err = require_auth()
    if err: return err
    
    try:
        data = request.get_json(force=True, silent=True) or {}
        item_type = data.get('type', 'task')
        
        db = get_db()
        
        if item_type == 'task':
            title = (data.get('title') or '').strip()
            if not title:
                return jsonify({'ok': False, 'error': 'Zadejte název úkolu'}), 400
            
            db.execute("""
                INSERT INTO tasks(title, status, created_by, created_at, updated_at)
                VALUES (?, 'open', ?, datetime('now'), datetime('now'))
            """, (title, u['id']))
            db.commit()
            task_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            return jsonify({'ok': True, 'id': task_id, 'type': 'task'})
        
        elif item_type == 'timesheet':
            hours = data.get('hours')
            job_id = data.get('job_id')
            
            if not hours:
                return jsonify({'ok': False, 'error': 'Zadejte počet hodin'}), 400
            
            # Get employee_id for current user
            emp = db.execute("SELECT id FROM employees WHERE user_id = ?", (u['id'],)).fetchone()
            emp_id = emp['id'] if emp else None
            
            db.execute("""
                INSERT INTO timesheets(employee_id, job_id, date, hours, note, created_by)
                VALUES (?, ?, date('now'), ?, ?, ?)
            """, (emp_id, job_id, float(hours), data.get('note', ''), u['id']))
            db.commit()
            
            return jsonify({'ok': True, 'type': 'timesheet'})
        
        return jsonify({'ok': False, 'error': 'Neznámý typ'}), 400
        
    except Exception as e:
        print(f"[ERROR] api_quick_add: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============================================================
# GPS CHECK-IN/OUT API
# ============================================================

@api_bp.route('/api/gps/checkin', methods=['POST'])
def api_gps_checkin():
    """Record GPS check-in to a job."""
    user, err = require_auth()
    if err:
        return err
    
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')
        check_in_time = data.get('check_in_time')
        lat = data.get('lat')
        lng = data.get('lng')
        
        if not job_id:
            return jsonify({'ok': False, 'error': 'job_id required'}), 400
        
        db = get_db()
        
        # Create gps_logs table if not exists
        db.execute('''CREATE TABLE IF NOT EXISTS gps_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_id INTEGER,
            check_in_time TEXT,
            check_out_time TEXT,
            check_in_lat REAL,
            check_in_lng REAL,
            check_out_lat REAL,
            check_out_lng REAL,
            hours_worked REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )''')
        
        db.execute('''
            INSERT INTO gps_logs (user_id, job_id, check_in_time, check_in_lat, check_in_lng)
            VALUES (?, ?, ?, ?, ?)
        ''', [session.get('user_id'), job_id, check_in_time, lat, lng])
        db.commit()
        
        return jsonify({'ok': True, 'message': 'Check-in recorded'})
    except Exception as e:
        print(f"[ERROR] api_gps_checkin: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@api_bp.route('/api/gps/checkout', methods=['POST'])
def api_gps_checkout():
    """Record GPS check-out and create timesheet entry."""
    user, err = require_auth()
    if err:
        return err
    
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')
        check_in_time = data.get('check_in_time')
        check_out_time = data.get('check_out_time')
        hours_worked = data.get('hours_worked', 0)
        lat = data.get('lat')
        lng = data.get('lng')
        
        db = get_db()
        
        # Update GPS log
        db.execute('''
            UPDATE gps_logs 
            SET check_out_time = ?, check_out_lat = ?, check_out_lng = ?, hours_worked = ?
            WHERE job_id = ? AND user_id = ? AND check_out_time IS NULL
            ORDER BY id DESC LIMIT 1
        ''', [check_out_time, lat, lng, hours_worked, job_id, session.get('user_id')])
        
        # Auto-create timesheet entry
        if hours_worked > 0:
            today = check_out_time.split('T')[0] if check_out_time else None
            db.execute('''
                INSERT INTO timesheets (job_id, employee_id, date, hours, description)
                VALUES (?, ?, ?, ?, ?)
            ''', [job_id, session.get('user_id'), today, round(hours_worked, 2), 'GPS auto-záznam'])
        
        db.commit()
        
        return jsonify({'ok': True, 'hours_logged': round(hours_worked, 2)})
    except Exception as e:
        print(f"[ERROR] api_gps_checkout: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


# ============================================================
# CLIENT PORTAL API
# ============================================================


# ============================================================
# AI OPERATOR API STUBS
# ============================================================

@api_bp.route('/api/ai/brain/analysis')
def api_ai_brain_analysis():
    """AI Brain analysis - returns empty analysis when module not loaded"""
    u, err = require_auth()
    if err: return err
    try:
        import ai_operator_api
        from app.database import get_db as app_get_db
        # Nastav get_db před použitím
        ai_operator_api.get_db = app_get_db
        data = ai_operator_api.get_ai_dashboard()
        return jsonify(data) if isinstance(data, dict) else data
    except Exception as e:
        print(f"AI Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'score': 75,
            'insights': [],
            'warnings': [],
            'recommendations': [],
            'status': 'ok',
            'message': 'AI modul se načítá...'
        })

@api_bp.route('/api/ai/dashboard')
def api_ai_dashboard():
    """AI Dashboard data"""
    u, err = require_auth()
    if err: return err
    try:
        import ai_operator_api
        from app.database import get_db as app_get_db
        # Nastav get_db před použitím
        ai_operator_api.get_db = app_get_db
        data = ai_operator_api.get_ai_dashboard()
        return jsonify(data) if isinstance(data, dict) else data
    except Exception as e:
        print(f"AI Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'score': 75,
            'warnings': [],
            'recommendations': [],
            'actions': [],
            'status': 'ok'
        })

@api_bp.route('/api/ai/drafts', methods=['GET', 'POST'])
def api_ai_drafts():
    u, err = require_auth()
    if err: return err
    try:
        import ai_operator_api
        from app.database import get_db as app_get_db
        # Nastav get_db před použitím
        ai_operator_api.get_db = app_get_db
        
        # Zkus použít funkci z ai_operator_api pokud existuje
        if hasattr(ai_operator_api, 'api_drafts'):
            return ai_operator_api.api_drafts()
    except Exception as e:
        print(f"AI Drafts error: {e}")
    
    return jsonify({'drafts': [], 'ok': True})

@api_bp.route('/api/ai/drafts/<int:draft_id>/approve', methods=['POST'])
def api_ai_draft_approve(draft_id):
    u, err = require_auth()
    if err: return err
    return jsonify({'ok': True})

@api_bp.route('/api/ai/drafts/<int:draft_id>/reject', methods=['POST'])
def api_ai_draft_reject(draft_id):
    u, err = require_auth()
    if err: return err
    return jsonify({'ok': True})

@api_bp.route('/api/ai/brain/learn', methods=['POST'])
def api_ai_brain_learn():
    u, err = require_auth()
    if err: return err
    return jsonify({'ok': True})

@api_bp.route('/api/ai/insight/<int:insight_id>/snooze', methods=['POST'])
def api_ai_insight_snooze(insight_id):
    u, err = require_auth()
    if err: return err
    return jsonify({'ok': True})

@api_bp.route('/api/ai/insight/<int:insight_id>/dismiss', methods=['POST'])
def api_ai_insight_dismiss(insight_id):
    u, err = require_auth()
    if err: return err
    return jsonify({'ok': True})

@api_bp.route('/api/ai/all-job-indicators')
def api_ai_all_job_indicators():
    """Indikátory pro všechny aktivní zakázky"""
    u, err = require_auth()
    if err: return err
    try:
        import ai_operator_api
        from app.database import get_db as app_get_db
        ai_operator_api.get_db = app_get_db
        
        # Zavolej funkci z ai_operator_api
        db = ai_operator_api.get_db_with_row_factory()
        from datetime import datetime, timedelta
        today = datetime.now().date()
        result = {}
        
        jobs = db.execute('''
            SELECT id, client, name, estimated_value, actual_value, 
                   planned_end_date, status, tags
            FROM jobs 
            WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
        ''').fetchall()
        
        for job in jobs:
            indicators = []
            
            # Budget
            if job['estimated_value'] and job['actual_value'] and job['estimated_value'] > 0:
                pct = (job['actual_value'] / job['estimated_value']) * 100
                if pct > 110:
                    indicators.append({'type': 'budget', 'severity': 'critical' if pct > 130 else 'warn'})
            
            # Deadline
            if job['planned_end_date']:
                try:
                    deadline = datetime.strptime(str(job['planned_end_date']), '%Y-%m-%d').date()
                    if deadline < today:
                        indicators.append({'type': 'deadline', 'severity': 'critical'})
                    elif deadline <= today + timedelta(days=3):
                        indicators.append({'type': 'deadline', 'severity': 'warn'})
                except:
                    pass
            
            # Tags (outdoor, etc)
            if job['tags'] and 'outdoor' in str(job['tags']).lower():
                indicators.append({'type': 'weather', 'severity': 'info'})
            
            if indicators:
                result[job['id']] = indicators
        
        return jsonify({'indicators': result})
    except Exception as e:
        print(f"All job indicators error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'indicators': {}})

@api_bp.route('/api/ai/task-indicators')
def api_ai_task_indicators():
    """Indikátory pro úkoly"""
    u, err = require_auth()
    if err: return err
    # Stub - vrať prázdný objekt
    return jsonify({'indicators': {}})
