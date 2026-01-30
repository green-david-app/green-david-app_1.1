"""
GREEN DAVID APP - AI OPERÁTOR API
=================================
Digitální mozek firmy s prediktivními a optimalizačními funkcemi.

Moduly:
1. AI Operátor - automatické přesuny, predikce, detekce anomálií
2. Samooptimalizační plánování - doporučení, varování, konflikty
4. Biointeligence - rostliny, počasí, zálivka

Autor: Green David s.r.o.
Verze: 1.0
"""

from flask import jsonify, request
from datetime import datetime, timedelta
from functools import wraps
import json
import math

# Reference na get_db - nastaví se z main.py
get_db = None

def get_db_with_row_factory():
    """Získej DB connection s row_factory pro dict přístup"""
    import sqlite3
    db = get_db()  # Volá správně get_db(), ne sám sebe!
    db.row_factory = sqlite3.Row
    return db

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated

# =============================================================================
# 1. AI OPERÁTOR - DIGITÁLNÍ MOZEK FIRMY
# =============================================================================

def get_ai_dashboard():
    """Hlavní AI dashboard - RULE ENGINE V1"""
    try:
        db = get_db_with_row_factory()
        today = datetime.now().date()
        
        # Sbíráme všechna varování a doporučení
        warnings = []
        recommendations = []
        
        # =====================================================================
        # PRAVIDLA VAROVÁNÍ
        # =====================================================================
        
        # 1. Zakázka > 110% rozpočtu
        budget_warnings = get_budget_warnings(db)
        warnings.extend(budget_warnings)
        
        # 2. Zaměstnanec > 45h týdně
        overwork_warnings = get_overwork_warnings(db, today)
        warnings.extend(overwork_warnings)
        
        # 3. Materiál pod minimem
        stock_warnings = get_stock_warnings(db)
        warnings.extend(stock_warnings)
        
        # 4. Zakázka bez aktivity 5+ dní
        inactive_warnings = get_inactive_job_warnings(db, today)
        warnings.extend(inactive_warnings)
        
        # 5. Zpožděné zakázky
        delay_warnings = get_delay_warnings(db, today)
        warnings.extend(delay_warnings)
        
        # 6. Úkoly bez přiřazení blízko deadline
        unassigned_warnings = get_unassigned_task_warnings(db, today)
        warnings.extend(unassigned_warnings)
        
        # =====================================================================
        # CHYTRÁ DOPORUČENÍ
        # =====================================================================
        
        # 1. Počasí + venkovní práce
        weather_recs = get_weather_recommendations(db, today)
        recommendations.extend(weather_recs)
        
        # 2. Přetížení/volno zaměstnanců
        workload_recs = get_workload_recommendations(db, today)
        recommendations.extend(workload_recs)
        
        # 3. Materiál pro nadcházející zakázky
        material_recs = get_material_recommendations(db, today)
        recommendations.extend(material_recs)
        
        # 4. Zakázky k dokončení
        completion_recs = get_completion_recommendations(db, today)
        recommendations.extend(completion_recs)
        
        # =====================================================================
        # SKÓRE FIRMY (dynamické)
        # =====================================================================
        score_breakdown = calculate_company_score(db, today, warnings)
        
        # =====================================================================
        # PANEL "DNES DOPORUČUJI" - 3 nejdůležitější věci
        # =====================================================================
        today_actions = get_today_actions(warnings, recommendations)
        
        # =====================================================================
        # SESTAVENÍ VÝSLEDKU
        # =====================================================================
        
        # Seřaď varování podle závažnosti
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        warnings.sort(key=lambda x: severity_order.get(x.get('severity', 'low'), 4))
        
        # Seřaď doporučení podle priority
        recommendations.sort(key=lambda x: severity_order.get(x.get('priority', 'low'), 4))
        
        result = {
            'score': score_breakdown['total'],
            'score_breakdown': score_breakdown,
            'warnings': warnings,
            'warnings_count': len([w for w in warnings if w.get('severity') in ['critical', 'high']]),
            'recommendations': recommendations,
            'recommendations_count': len(recommendations),
            'today_actions': today_actions,
            'workload_balance': get_workload_balance_data(db, today),
            'weather_alerts': get_weather_alerts_data(db, today),
            'material_predictions': get_material_predictions_data(db)
        }
        
        return jsonify(result)
        
    except Exception as e:
        print(f"AI Dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'score': 50,
            'score_breakdown': {'total': 50},
            'warnings': [],
            'recommendations': [],
            'today_actions': [{'text': '⚠️ Nepodařilo se načíst data', 'severity': 'medium'}],
            'workload_balance': {'employees': [], 'balance_score': 50}
        })


# =============================================================================
# PRAVIDLA VAROVÁNÍ (Rule Engine)
# =============================================================================

def get_budget_warnings(db):
    """Zakázky přes 110% rozpočtu"""
    warnings = []
    try:
        jobs = db.execute('''
            SELECT j.id, j.client, j.name, j.estimated_value, j.actual_value,
                   CASE WHEN j.estimated_value > 0 
                        THEN (COALESCE(j.actual_value, 0) / j.estimated_value) * 100 
                        ELSE 0 END as percent_used
            FROM jobs j
            WHERE j.estimated_value > 0
            AND j.status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
            AND COALESCE(j.actual_value, 0) > j.estimated_value * 1.1
        ''').fetchall()
        
        for job in jobs:
            percent = job['percent_used']
            warnings.append({
                'id': f"budget_{job['id']}",
                'type': 'budget_overrun',
                'severity': 'critical' if percent > 130 else 'high',
                'title': f"💰 Překročený rozpočet: {job['client'] or job['name']}",
                'detail': f"{percent:.0f}% rozpočtu ({job['actual_value']:,.0f} / {job['estimated_value']:,.0f} Kč)",
                'entity': 'job',
                'entity_id': job['id'],
                'action': {
                    'type': 'link',
                    'label': 'Otevřít zakázku',
                    'url': f"/job-detail.html?id={job['id']}"
                }
            })
    except Exception as e:
        print(f"Budget warnings error: {e}")
    return warnings


def get_overwork_warnings(db, today):
    """Zaměstnanci přes 45h týdně"""
    warnings = []
    try:
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        employees = db.execute('''
            SELECT e.id, e.name, COALESCE(SUM(t.hours), 0) as hours_this_week
            FROM employees e
            LEFT JOIN timesheets t ON t.employee_id = e.id
                AND (t.date BETWEEN ? AND ? OR t.date BETWEEN ? AND ?)
            WHERE e.status = 'active'
            GROUP BY e.id
            HAVING hours_this_week > 45
        ''', (week_start.isoformat(), week_end.isoformat(),
              week_start.strftime('%d.%m.%Y'), week_end.strftime('%d.%m.%Y'))).fetchall()
        
        for emp in employees:
            hours = emp['hours_this_week']
            warnings.append({
                'id': f"overwork_{emp['id']}",
                'type': 'overwork',
                'severity': 'critical' if hours > 55 else 'high',
                'title': f"👷 Přetížený: {emp['name']}",
                'detail': f"{hours:.0f}h tento týden (limit 45h)",
                'entity': 'employee',
                'entity_id': emp['id'],
                'action': {
                    'type': 'link',
                    'label': 'Zobrazit výkazy',
                    'url': f"/employee-detail.html?id={emp['id']}"
                }
            })
    except Exception as e:
        print(f"Overwork warnings error: {e}")
    return warnings


def get_stock_warnings(db):
    """Materiál pod minimálním stavem"""
    warnings = []
    try:
        items = db.execute('''
            SELECT id, name, qty, minStock, unit
            FROM warehouse_items
            WHERE status = 'active'
            AND qty < minStock
            AND minStock > 0
        ''').fetchall()
        
        for item in items:
            ratio = item['qty'] / item['minStock'] if item['minStock'] > 0 else 0
            warnings.append({
                'id': f"stock_{item['id']}",
                'type': 'low_stock',
                'severity': 'critical' if ratio < 0.3 else 'high' if ratio < 0.5 else 'medium',
                'title': f"📦 Dochází: {item['name']}",
                'detail': f"{item['qty']:.0f} {item['unit']} (min: {item['minStock']:.0f})",
                'entity': 'warehouse',
                'entity_id': item['id'],
                'action': {
                    'type': 'link',
                    'label': 'Otevřít sklad',
                    'url': f"/warehouse.html?item={item['id']}"
                }
            })
    except Exception as e:
        print(f"Stock warnings error: {e}")
    return warnings


def get_inactive_job_warnings(db, today):
    """Zakázky bez aktivity 5+ dní"""
    warnings = []
    try:
        five_days_ago = today - timedelta(days=5)
        
        jobs = db.execute('''
            SELECT j.id, j.client, j.name, j.status,
                   MAX(t.date) as last_activity
            FROM jobs j
            LEFT JOIN timesheets t ON t.job_id = j.id
            WHERE j.status IN ('active', 'Aktivní', 'rozpracováno', 'pending')
            GROUP BY j.id
            HAVING last_activity IS NULL OR last_activity < ?
        ''', (five_days_ago.isoformat(),)).fetchall()
        
        for job in jobs:
            days_inactive = (today - datetime.fromisoformat(job['last_activity']).date()).days if job['last_activity'] else 999
            if days_inactive >= 5:
                warnings.append({
                    'id': f"inactive_{job['id']}",
                    'type': 'inactive',
                    'severity': 'high' if days_inactive > 10 else 'medium',
                    'title': f"💤 Bez aktivity: {job['client'] or job['name']}",
                    'detail': f"{days_inactive} dní bez záznamu",
                    'entity': 'job',
                    'entity_id': job['id'],
                    'action': {
                        'type': 'link',
                        'label': 'Zkontrolovat',
                        'url': f"/job-detail.html?id={job['id']}"
                    }
                })
    except Exception as e:
        print(f"Inactive warnings error: {e}")
    return warnings


def get_delay_warnings(db, today):
    """Zpožděné zakázky"""
    warnings = []
    try:
        jobs = db.execute('''
            SELECT id, client, name, planned_end_date
            FROM jobs
            WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
            AND planned_end_date IS NOT NULL
            AND planned_end_date < ?
        ''', (today.isoformat(),)).fetchall()
        
        for job in jobs:
            days_late = (today - datetime.fromisoformat(job['planned_end_date']).date()).days
            warnings.append({
                'id': f"delay_{job['id']}",
                'type': 'delay',
                'severity': 'critical' if days_late > 14 else 'high' if days_late > 7 else 'medium',
                'title': f"⏰ Zpožděná: {job['client'] or job['name']}",
                'detail': f"Zpoždění {days_late} dní",
                'entity': 'job',
                'entity_id': job['id'],
                'action': {
                    'type': 'link',
                    'label': 'Aktualizovat termín',
                    'url': f"/job-detail.html?id={job['id']}"
                }
            })
    except Exception as e:
        print(f"Delay warnings error: {e}")
    return warnings


def get_unassigned_task_warnings(db, today):
    """Úkoly bez přiřazení blízko deadline"""
    warnings = []
    try:
        three_days = today + timedelta(days=3)
        tasks = db.execute('''
            SELECT t.id, t.title, t.due_date, j.client
            FROM tasks t
            LEFT JOIN jobs j ON j.id = t.job_id
            WHERE t.employee_id IS NULL
            AND t.status NOT IN ('done', 'completed', 'cancelled')
            AND t.due_date IS NOT NULL
            AND t.due_date <= ?
        ''', (three_days.isoformat(),)).fetchall()
        
        for task in tasks:
            warnings.append({
                'id': f"unassigned_{task['id']}",
                'type': 'unassigned',
                'severity': 'high',
                'title': f"📋 Nepřiřazený úkol: {task['title'][:40]}",
                'detail': f"Deadline: {task['due_date']}" + (f" ({task['client']})" if task['client'] else ''),
                'entity': 'task',
                'entity_id': task['id'],
                'action': {
                    'type': 'assign',
                    'label': 'Přiřadit',
                    'task_id': task['id']
                }
            })
    except Exception as e:
        print(f"Unassigned warnings error: {e}")
    return warnings


# =============================================================================
# CHYTRÁ DOPORUČENÍ
# =============================================================================

def get_weather_recommendations(db, today):
    """Doporučení na základě počasí"""
    recommendations = []
    try:
        forecast = simulate_weather_forecast(today)
        
        # Najdi zakázky s venkovní prací
        outdoor_jobs = db.execute('''
            SELECT j.id, j.client, j.name, j.start_date, j.weather_dependent
            FROM jobs j
            WHERE j.status IN ('active', 'Aktivní', 'pending', 'rozpracováno')
            AND (j.weather_dependent = 1 OR j.type IN ('landscaping', 'construction', 'garden'))
        ''').fetchall()
        
        for day in forecast[:5]:
            if day.get('rain_chance', 0) > 60 or day.get('temp', 15) < 0:
                weather_issue = 'déšť' if day.get('rain_chance', 0) > 60 else 'mráz'
                
                # Najdi alternativní den
                alt_days = [d for d in forecast if d.get('rain_chance', 0) < 30 and d.get('temp', 15) > 5]
                alt_date = alt_days[0]['date'] if alt_days else None
                
                for job in outdoor_jobs:
                    if job['start_date'] == day['date']:
                        recommendations.append({
                            'id': f"weather_{job['id']}_{day['date']}",
                            'type': 'weather_move',
                            'priority': 'high',
                            'title': f"🌧️ Přesunout: {job['client'] or job['name']}",
                            'detail': f"Hlášen {weather_issue} na {day['date']}",
                            'suggestion': f"Doporučuji přesunout na {alt_date}" if alt_date else "Najít náhradní termín",
                            'entity': 'job',
                            'entity_id': job['id'],
                            'action': {
                                'type': 'reschedule',
                                'label': f"Přesunout na {alt_date}" if alt_date else "Upravit termín",
                                'job_id': job['id'],
                                'suggested_date': alt_date
                            }
                        })
    except Exception as e:
        print(f"Weather recommendations error: {e}")
    return recommendations


def get_workload_recommendations(db, today):
    """Doporučení pro vyrovnání vytížení"""
    recommendations = []
    try:
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        employees = db.execute('''
            SELECT e.id, e.name, COALESCE(SUM(t.hours), 0) as hours
            FROM employees e
            LEFT JOIN timesheets t ON t.employee_id = e.id
                AND (t.date BETWEEN ? AND ? OR t.date BETWEEN ? AND ?)
            WHERE e.status = 'active'
            GROUP BY e.id
        ''', (week_start.isoformat(), week_end.isoformat(),
              week_start.strftime('%d.%m.%Y'), week_end.strftime('%d.%m.%Y'))).fetchall()
        
        if employees:
            avg_hours = sum(e['hours'] for e in employees) / len(employees)
            overloaded = [e for e in employees if e['hours'] > 45]
            underloaded = [e for e in employees if e['hours'] < avg_hours * 0.5 and e['hours'] < 20]
            
            for over in overloaded:
                for under in underloaded:
                    recommendations.append({
                        'id': f"balance_{over['id']}_{under['id']}",
                        'type': 'workload_balance',
                        'priority': 'medium',
                        'title': f"⚖️ Přerozdělit práci",
                        'detail': f"{over['name']} má {over['hours']:.0f}h, {under['name']} má {under['hours']:.0f}h",
                        'suggestion': f"Přesunout úkoly z {over['name']} na {under['name']}",
                        'action': {
                            'type': 'link',
                            'label': 'Zobrazit tým',
                            'url': '/employees.html'
                        }
                    })
                    break  # Jen jedno doporučení na přetíženého
    except Exception as e:
        print(f"Workload recommendations error: {e}")
    return recommendations


def get_material_recommendations(db, today):
    """Doporučení pro objednání materiálu"""
    recommendations = []
    try:
        # Materiály pod minimem
        low_stock = db.execute('''
            SELECT id, name, qty, minStock, unit
            FROM warehouse_items
            WHERE status = 'active' AND qty < minStock * 1.2 AND minStock > 0
            ORDER BY (qty / minStock) ASC
            LIMIT 5
        ''').fetchall()
        
        if low_stock:
            items_list = ', '.join([f"{i['name']} ({i['qty']:.0f}/{i['minStock']:.0f})" for i in low_stock[:3]])
            recommendations.append({
                'id': 'material_order',
                'type': 'material_order',
                'priority': 'high' if any(i['qty'] < i['minStock'] * 0.5 for i in low_stock) else 'medium',
                'title': f"📦 Objednat materiál",
                'detail': items_list,
                'suggestion': f"Doporučuji objednat {len(low_stock)} položek",
                'action': {
                    'type': 'link',
                    'label': 'Otevřít sklad',
                    'url': '/warehouse.html'
                }
            })
    except Exception as e:
        print(f"Material recommendations error: {e}")
    return recommendations


def get_completion_recommendations(db, today):
    """Doporučení k dokončení zakázek"""
    recommendations = []
    try:
        # Zakázky s vysokým progress ale ne dokončené
        jobs = db.execute('''
            SELECT id, client, name, progress, completion_percent
            FROM jobs
            WHERE status NOT IN ('Dokončeno', 'completed', 'archived')
            AND (progress >= 90 OR completion_percent >= 90)
        ''').fetchall()
        
        for job in jobs:
            progress = job['progress'] or job['completion_percent'] or 0
            recommendations.append({
                'id': f"complete_{job['id']}",
                'type': 'completion',
                'priority': 'low',
                'title': f"✅ Dokončit: {job['client'] or job['name']}",
                'detail': f"Progress: {progress}%",
                'suggestion': "Zakázka je téměř hotová, zkontrolujte a označte jako dokončenou",
                'action': {
                    'type': 'complete',
                    'label': 'Dokončit zakázku',
                    'job_id': job['id']
                }
            })
    except Exception as e:
        print(f"Completion recommendations error: {e}")
    return recommendations


# =============================================================================
# DYNAMICKÉ SKÓRE FIRMY
# =============================================================================

def calculate_company_score(db, today, warnings):
    """
    Skóre firmy = Tesla tachometr
    - Rozpočty: 30%
    - Termíny: 25%
    - Vytížení týmu: 20%
    - Sklad: 15%
    - Aktivita: 10%
    """
    scores = {
        'budget': 100,
        'deadlines': 100,
        'workload': 100,
        'stock': 100,
        'activity': 100
    }
    
    weights = {
        'budget': 0.30,
        'deadlines': 0.25,
        'workload': 0.20,
        'stock': 0.15,
        'activity': 0.10
    }
    
    try:
        # 1. ROZPOČTY (30%)
        budget_warnings = [w for w in warnings if w['type'] == 'budget_overrun']
        scores['budget'] = max(0, 100 - len(budget_warnings) * 25)
        
        # 2. TERMÍNY (25%)
        delay_warnings = [w for w in warnings if w['type'] == 'delay']
        critical_delays = len([w for w in delay_warnings if w['severity'] == 'critical'])
        other_delays = len(delay_warnings) - critical_delays
        scores['deadlines'] = max(0, 100 - critical_delays * 30 - other_delays * 15)
        
        # 3. VYTÍŽENÍ TÝMU (20%)
        overwork = [w for w in warnings if w['type'] == 'overwork']
        scores['workload'] = max(0, 100 - len(overwork) * 20)
        
        # 4. SKLAD (15%)
        stock_warnings = [w for w in warnings if w['type'] == 'low_stock']
        critical_stock = len([w for w in stock_warnings if w['severity'] == 'critical'])
        other_stock = len(stock_warnings) - critical_stock
        scores['stock'] = max(0, 100 - critical_stock * 25 - other_stock * 10)
        
        # 5. AKTIVITA (10%)
        inactive = [w for w in warnings if w['type'] == 'inactive']
        scores['activity'] = max(0, 100 - len(inactive) * 15)
        
    except Exception as e:
        print(f"Score calculation error: {e}")
    
    # Celkové skóre
    total = sum(scores[k] * weights[k] for k in scores)
    
    return {
        'total': round(total),
        'budget': scores['budget'],
        'deadlines': scores['deadlines'],
        'workload': scores['workload'],
        'stock': scores['stock'],
        'activity': scores['activity'],
        'weights': weights
    }


# =============================================================================
# PANEL "DNES DOPORUČUJI"
# =============================================================================

def get_today_actions(warnings, recommendations):
    """3 nejdůležitější akce pro dnešek"""
    actions = []
    
    # Nejdřív kritická varování
    critical = [w for w in warnings if w.get('severity') == 'critical']
    for w in critical[:2]:
        actions.append({
            'text': w['title'],
            'detail': w.get('detail', ''),
            'severity': 'critical',
            'action': w.get('action')
        })
    
    # Pak high priority varování
    if len(actions) < 3:
        high = [w for w in warnings if w.get('severity') == 'high' and w not in critical]
        for w in high[:3-len(actions)]:
            actions.append({
                'text': w['title'],
                'detail': w.get('detail', ''),
                'severity': 'high',
                'action': w.get('action')
            })
    
    # Pak doporučení
    if len(actions) < 3:
        for r in recommendations[:3-len(actions)]:
            actions.append({
                'text': r['title'],
                'detail': r.get('detail', ''),
                'severity': r.get('priority', 'medium'),
                'action': r.get('action')
            })
    
    # Pokud nic není, všechno je OK
    if not actions:
        actions.append({
            'text': '✅ Vše v pořádku',
            'detail': 'Žádné urgentní úkoly',
            'severity': 'ok'
        })
    
    return actions[:3]


def get_weather_alerts_data(db, today):
    """Zjisti počasí a doporuč přesuny zakázek"""
    alerts = []
    
    # Získej zakázky na příštích 7 dní
    week_ahead = today + timedelta(days=7)
    
    jobs = db.execute('''
        SELECT j.id, j.client, j.city as location, j.start_date, j.planned_end_date as end_date, j.status,
               GROUP_CONCAT(DISTINCT t.title) as tasks
        FROM jobs j
        LEFT JOIN tasks t ON t.job_id = j.id
        WHERE j.status IN ('active', 'pending', 'nová', 'rozpracováno')
        AND j.start_date IS NOT NULL
        AND j.start_date <= ?
        ORDER BY j.start_date
    ''', (week_ahead.isoformat(),)).fetchall()
    
    # Simulace počasí (v reálu by se volalo weather API)
    weather_forecast = simulate_weather_forecast(today)
    
    for job in jobs:
        job_date = job['start_date'] if job['start_date'] else None
        if job_date:
            weather = get_weather_for_date(weather_forecast, job_date)
            
            if weather and weather['risk_level'] in ['high', 'critical']:
                alerts.append({
                    'job_id': job['id'],
                    'client': job['client'],
                    'date': job_date,
                    'weather': weather,
                    'recommendation': get_weather_recommendation(weather, job),
                    'alternative_dates': find_alternative_dates(weather_forecast, job_date)
                })
    
    return alerts


def simulate_weather_forecast(start_date):
    """Simulace předpovědi počasí na 14 dní"""
    forecast = []
    
    # Simulované počasí (v produkci nahradit reálným API)
    patterns = [
        {'temp': 5, 'rain': 0, 'wind': 10, 'condition': 'sunny'},
        {'temp': 3, 'rain': 80, 'wind': 25, 'condition': 'rain'},
        {'temp': -2, 'rain': 20, 'wind': 15, 'condition': 'frost'},
        {'temp': 8, 'rain': 10, 'wind': 8, 'condition': 'cloudy'},
        {'temp': 12, 'rain': 0, 'wind': 5, 'condition': 'sunny'},
        {'temp': 6, 'rain': 60, 'wind': 30, 'condition': 'storm'},
        {'temp': 4, 'rain': 40, 'wind': 20, 'condition': 'rain'},
    ]
    
    for i in range(14):
        date = start_date + timedelta(days=i)
        pattern = patterns[i % len(patterns)]
        
        risk_level = 'low'
        if pattern['rain'] > 50 or pattern['wind'] > 20:
            risk_level = 'medium'
        if pattern['rain'] > 70 or pattern['wind'] > 30 or pattern['temp'] < 0:
            risk_level = 'high'
        if pattern['condition'] == 'storm' or pattern['temp'] < -5:
            risk_level = 'critical'
        
        forecast.append({
            'date': date.isoformat(),
            'temp': pattern['temp'],
            'rain_chance': pattern['rain'],
            'wind_speed': pattern['wind'],
            'condition': pattern['condition'],
            'risk_level': risk_level,
            'work_suitable': risk_level in ['low', 'medium']
        })
    
    return forecast


def get_weather_for_date(forecast, date_str):
    """Najdi počasí pro konkrétní datum"""
    for day in forecast:
        if day['date'] == date_str:
            return day
    return None


def get_weather_recommendation(weather, job):
    """Generuj doporučení na základě počasí"""
    if weather['condition'] == 'storm':
        return f"⛈️ KRITICKÉ: Bouřka - přesunout zakázku {job['client']}"
    elif weather['temp'] < 0:
        return f"🥶 VAROVÁNÍ: Mráz ({weather['temp']}°C) - zvážit přesun"
    elif weather['rain_chance'] > 70:
        return f"🌧️ Vysoká šance deště ({weather['rain_chance']}%) - připravit alternativu"
    elif weather['wind_speed'] > 25:
        return f"💨 Silný vítr ({weather['wind_speed']} km/h) - omezit výškové práce"
    return "⚠️ Nepříznivé podmínky - zvážit přesun"


def find_alternative_dates(forecast, original_date):
    """Najdi alternativní termíny s lepším počasím"""
    alternatives = []
    for day in forecast:
        if day['work_suitable'] and day['date'] != original_date:
            alternatives.append({
                'date': day['date'],
                'condition': day['condition'],
                'temp': day['temp']
            })
            if len(alternatives) >= 3:
                break
    return alternatives


def get_material_predictions_data(db):
    """Predikce nedostatku materiálu na základě spotřeby"""
    predictions = []
    
    try:
        # Získej skladové položky
        items = db.execute('''
            SELECT id, name, qty, minStock, unit, category
            FROM warehouse_items
            WHERE (qty > 0 OR minStock > 0) AND status = 'active'
        ''').fetchall()
        
        for item in items:
            try:
                item_id = item['id']
                item_name = item['name']
                current_qty = item['qty'] or 0
                min_qty = item['minStock'] or 0
                item_unit = item['unit'] or 'ks'
                
                # Získej historii spotřeby (posledních 30 dní)
                movements = db.execute('''
                    SELECT SUM(ABS(qty)) as total_used
                    FROM warehouse_movements
                    WHERE item_id = ? AND movement_type = 'out'
                    AND created_at >= date('now', '-30 days')
                ''', (item_id,)).fetchone()
                
                total_used = movements['total_used'] or 0 if movements else 0
                daily_usage = total_used / 30 if total_used > 0 else 0
                
                # Predikce dní do vyčerpání
                if daily_usage > 0:
                    days_until_empty = current_qty / daily_usage
                    days_until_min = (current_qty - min_qty) / daily_usage if current_qty > min_qty else 0
                else:
                    days_until_empty = 999
                    days_until_min = 999
                
                # Přidej varování pokud dochází
                if days_until_min < 14 or current_qty <= min_qty:
                    urgency = 'critical' if days_until_empty < 7 else 'warning' if days_until_min < 14 else 'info'
                    
                    predictions.append({
                        'item_id': item_id,
                        'name': item_name,
                        'current_qty': current_qty,
                        'min_qty': min_qty,
                        'unit': item_unit,
                        'daily_usage': round(daily_usage, 2),
                        'days_until_min': round(days_until_min, 1),
                        'days_until_empty': round(days_until_empty, 1),
                        'urgency': urgency,
                        'recommendation': f"🚨 Objednat {item_name} ihned!" if urgency == 'critical' else f"📦 Zkontrolovat {item_name}"
                    })
            except Exception as e:
                print(f"Material item error: {e}")
                continue
        
        # Seřaď podle urgence
        urgency_order = {'critical': 0, 'warning': 1, 'info': 2}
        predictions.sort(key=lambda x: (urgency_order.get(x['urgency'], 3), x['days_until_empty']))
        
    except Exception as e:
        print(f"Material predictions error: {e}")
    
    return predictions[:10]  # Top 10 nejkritičtějších


def get_material_recommendation(item, days_until_empty, daily_usage):
    """Generuj doporučení pro objednávku materiálu"""
    if days_until_empty < 7:
        order_qty = math.ceil(daily_usage * 30)  # Objednat na měsíc
        return f"🚨 URGENTNÍ: Objednat {order_qty} {item['unit']} ihned!"
    elif days_until_empty < 14:
        order_qty = math.ceil(daily_usage * 30)
        return f"⚠️ Objednat {order_qty} {item['unit']} tento týden"
    else:
        return f"📋 Naplánovat objednávku do 2 týdnů"


def get_workload_balance_data(db, today, period='week'):
    """Analýza vytížení zaměstnanců a doporučení vyrovnání"""
    
    # Určení období
    if period == 'week':
        period_start = today - timedelta(days=today.weekday())
        period_end = period_start + timedelta(days=6)
        period_name = "tento týden"
    elif period == 'last_week':
        period_end = today - timedelta(days=today.weekday()) - timedelta(days=1)
        period_start = period_end - timedelta(days=6)
        period_name = "minulý týden"
    elif period == 'month':
        period_start = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        period_end = next_month.replace(day=1) - timedelta(days=1)
        period_name = "tento měsíc"
    elif period == 'last_month':
        first_this_month = today.replace(day=1)
        period_end = first_this_month - timedelta(days=1)
        period_start = period_end.replace(day=1)
        period_name = "minulý měsíc"
    else:
        period_start = today - timedelta(days=today.weekday())
        period_end = period_start + timedelta(days=6)
        period_name = "tento týden"
    
    # Získej zaměstnance a jejich hodiny - OPRAVENO pro různé formáty dat
    try:
        employees = db.execute('''
            SELECT e.id, e.name, e.role,
                   COALESCE(SUM(t.hours), 0) as hours_period,
                   COUNT(DISTINCT t.id) as entries_count
            FROM employees e
            LEFT JOIN timesheets t ON t.employee_id = e.id 
                AND (
                    t.date BETWEEN ? AND ?
                    OR t.date BETWEEN ? AND ?
                )
            WHERE e.status = 'active' OR e.status IS NULL
            GROUP BY e.id
            ORDER BY hours_period DESC
        ''', (period_start.isoformat(), period_end.isoformat(),
              period_start.strftime('%d.%m.%Y'), period_end.strftime('%d.%m.%Y'))).fetchall()
    except Exception as e:
        print(f"Workload query error: {e}")
        employees = []
    
    if not employees:
        return {
            'employees': [], 
            'balance_score': 100, 
            'recommendations': [],
            'period': period_name,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'total_hours': 0,
            'average_hours': 0
        }
    
    # Vypočítej statistiky
    total_hours = sum(e['hours_period'] or 0 for e in employees)
    active_employees = [e for e in employees if (e['hours_period'] or 0) > 0]
    avg_hours = total_hours / len(active_employees) if active_employees else 0
    
    balance_data = []
    recommendations = []
    
    for emp in employees:
        hours = emp['hours_period'] or 0
        entries = emp['entries_count'] or 0
        
        # Určení stavu vytížení
        if avg_hours > 0:
            if hours > avg_hours * 1.5:
                status = 'overloaded'
                status_text = 'Přetížený'
            elif hours < avg_hours * 0.5 and hours < 20:
                status = 'underutilized'
                status_text = 'Nevytížený'
            else:
                status = 'balanced'
                status_text = 'Vyvážený'
        else:
            status = 'no_data' if hours == 0 else 'balanced'
            status_text = 'Bez záznamů' if hours == 0 else 'Vyvážený'
        
        balance_data.append({
            'id': emp['id'],
            'name': emp['name'],
            'role': emp['role'],
            'hours': round(hours, 1),
            'entries': entries,
            'status': status,
            'status_text': status_text,
            'deviation': round(((hours - avg_hours) / avg_hours * 100) if avg_hours > 0 else 0, 1)
        })
        
        # Generuj doporučení
        if status == 'overloaded':
            recommendations.append({
                'type': 'redistribute',
                'employee_id': emp['id'],
                'employee': emp['name'],
                'message': f"🔴 {emp['name']} je přetížený ({hours:.0f}h). Přerozdělit úkoly."
            })
        elif status == 'underutilized' and hours < 10:
            recommendations.append({
                'type': 'assign_more',
                'employee_id': emp['id'],
                'employee': emp['name'],
                'message': f"🟡 {emp['name']} má kapacitu ({hours:.0f}h). Přiřadit více práce."
            })
    
    # Skóre vyváženosti (0-100)
    overloaded = sum(1 for e in balance_data if e['status'] == 'overloaded')
    underutilized = sum(1 for e in balance_data if e['status'] == 'underutilized')
    balance_score = max(0, 100 - (overloaded * 20) - (underutilized * 10))
    
    return {
        'employees': balance_data,
        'average_hours': round(avg_hours, 1),
        'total_hours': round(total_hours, 1),
        'balance_score': balance_score,
        'recommendations': recommendations,
        'period': period_name,
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat()
    }


def get_anomalies_data(db, today):
    """Detekce anomálií v nákladech a zpoždění"""
    anomalies = []
    
    # 1. Zakázky se zpožděním - OPRAVENO: planned_end_date místo end_date
    try:
        delayed_jobs = db.execute('''
            SELECT id, client, planned_end_date as end_date, status
            FROM jobs
            WHERE status IN ('active', 'pending', 'rozpracováno')
            AND planned_end_date IS NOT NULL
            AND planned_end_date < ?
        ''', (today.isoformat(),)).fetchall()
        
        for job in delayed_jobs:
            if job['end_date']:
                try:
                    days_delayed = (today - datetime.fromisoformat(job['end_date']).date()).days
                    anomalies.append({
                        'type': 'delay',
                        'severity': 'critical' if days_delayed > 7 else 'warning',
                        'entity': 'job',
                        'entity_id': job['id'],
                        'title': f"Zpožděná zakázka: {job['client']}",
                        'detail': f"Zpoždění {days_delayed} dní",
                        'recommendation': "Zkontrolovat stav a aktualizovat termín"
                    })
                except:
                    pass
    except Exception as e:
        print(f"Delayed jobs error: {e}")
    
    # 2. Zakázky s přečerpanými náklady
    try:
        cost_anomalies = db.execute('''
            SELECT j.id, j.client, j.estimated_value,
                   COALESCE(SUM(t.hours * e.hourly_rate), 0) as actual_cost
            FROM jobs j
            LEFT JOIN timesheets t ON t.job_id = j.id
            LEFT JOIN employees e ON e.id = t.employee_id
            WHERE j.estimated_value > 0
            GROUP BY j.id
            HAVING actual_cost > j.estimated_value * 0.9
        ''').fetchall()
        
        for job in cost_anomalies:
            overrun = ((job['actual_cost'] / job['estimated_value']) - 1) * 100 if job['estimated_value'] > 0 else 0
            anomalies.append({
                'type': 'cost_overrun',
                'severity': 'critical' if overrun > 20 else 'warning',
                'entity': 'job',
                'entity_id': job['id'],
                'title': f"Přečerpání rozpočtu: {job['client']}",
                'detail': f"Náklady {overrun:.0f}% nad rozpočtem",
                'recommendation': "Zkontrolovat náklady a informovat klienta"
            })
    except Exception as e:
        print(f"Cost anomalies error: {e}")
    
    # 3. Úkoly bez přiřazení blízko deadline
    try:
        unassigned_urgent = db.execute('''
            SELECT id, title, due_date, job_id
            FROM tasks
            WHERE employee_id IS NULL
            AND status NOT IN ('done', 'completed')
            AND due_date IS NOT NULL
            AND due_date <= date('now', '+3 days')
        ''').fetchall()
        
        for task in unassigned_urgent:
            anomalies.append({
                'type': 'unassigned',
                'severity': 'warning',
                'entity': 'task',
                'entity_id': task['id'],
                'title': f"Nepřiřazený úkol: {task['title']}",
                'detail': f"Deadline: {task['due_date']}",
                'recommendation': "Přiřadit zaměstnance"
            })
    except Exception as e:
        print(f"Unassigned tasks error: {e}")
    
    # Seřaď podle severity
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    anomalies.sort(key=lambda x: severity_order.get(x['severity'], 3))
    
    return anomalies


# =============================================================================
# 2. SAMOOPTIMALIZAČNÍ PLÁNOVÁNÍ
# =============================================================================

def get_planning_optimization():
    """Optimalizační doporučení pro plánování"""
    try:
        db = get_db_with_row_factory()
        today = datetime.now().date()
        
        result = {
            'schedule_suggestions': [],
            'conflict_warnings': [],
            'seasonal_adjustments': [],
            'efficiency_tips': []
        }
        
        try:
            result['schedule_suggestions'] = get_schedule_suggestions(db, today)
        except Exception as e:
            print(f"Schedule suggestions error: {e}")
            
        try:
            result['conflict_warnings'] = get_conflict_warnings(db, today)
        except Exception as e:
            print(f"Conflict warnings error: {e}")
            
        try:
            result['seasonal_adjustments'] = get_seasonal_adjustments(today)
        except Exception as e:
            print(f"Seasonal adjustments error: {e}")
            
        try:
            result['efficiency_tips'] = get_efficiency_tips(db)
        except Exception as e:
            print(f"Efficiency tips error: {e}")
        
        return jsonify(result)
    except Exception as e:
        print(f"Planning optimization error: {e}")
        return jsonify({
            'schedule_suggestions': [],
            'conflict_warnings': [],
            'seasonal_adjustments': get_seasonal_adjustments(datetime.now().date()),
            'efficiency_tips': []
        })


def get_schedule_suggestions(db, today):
    """Doporučení pro optimální rozložení práce"""
    suggestions = []
    
    # Získej nadcházející zakázky - OPRAVENO: city místo location
    try:
        upcoming_jobs = db.execute('''
            SELECT j.id, j.client, j.city as location, j.start_date, j.planned_end_date as end_date,
                   j.estimated_hours, j.status,
                   COUNT(DISTINCT a.employee_id) as assigned_count
            FROM jobs j
            LEFT JOIN job_assignments a ON a.job_id = j.id
            WHERE j.status IN ('nová', 'pending', 'active', 'rozpracováno')
            AND (j.start_date >= ? OR j.start_date IS NULL)
            GROUP BY j.id
            ORDER BY j.start_date
            LIMIT 20
        ''', (today.isoformat(),)).fetchall()
    except Exception as e:
        print(f"Schedule suggestions SQL error: {e}")
        upcoming_jobs = []
    
    for job in upcoming_jobs:
        # Zkontroluj přiřazení
        if (job['assigned_count'] or 0) == 0:
            suggestions.append({
                'type': 'missing_assignment',
                'priority': 'high',
                'job_id': job['id'],
                'client': job['client'] or 'Neznámý klient',
                'message': f"📋 {job['client'] or 'Zakázka'} nemá přiřazené zaměstnance",
                'action': 'assign_workers'
            })
        
        # Zkontroluj odhad hodin
        if not job['estimated_hours'] or job['estimated_hours'] == 0:
            suggestions.append({
                'type': 'missing_estimate',
                'priority': 'medium',
                'job_id': job['id'],
                'client': job['client'] or 'Neznámý klient',
                'message': f"⏱️ {job['client'] or 'Zakázka'} nemá odhad hodin",
                'action': 'add_estimate'
            })
    
    # Doporučení pro seskupení zakázek podle lokace
    jobs_by_location = {}
    for job in upcoming_jobs:
        loc = (job['location'] or 'Neznámá').lower()
        if loc and loc != 'neznámá' and loc != '':
            if loc not in jobs_by_location:
                jobs_by_location[loc] = []
            jobs_by_location[loc].append(job)
    
    for loc, jobs in jobs_by_location.items():
        if len(jobs) > 1:
            suggestions.append({
                'type': 'location_cluster',
                'priority': 'low',
                'location': loc,
                'job_count': len(jobs),
                'message': f"📍 {len(jobs)} zakázky v oblasti '{loc}' - zvážit naplánovat společně",
                'action': 'cluster_jobs'
            })
    
    return suggestions


def get_conflict_warnings(db, today):
    """Varování před konflikty v plánování"""
    warnings = []
    
    # Najdi zaměstnance přiřazené k více zakázkám ve stejný den
    try:
        conflicts = db.execute('''
            SELECT e.id, e.name, j.start_date,
                   GROUP_CONCAT(j.client) as clients,
                   COUNT(*) as job_count
            FROM employees e
            JOIN job_assignments a ON a.employee_id = e.id
            JOIN jobs j ON j.id = a.job_id
            WHERE j.status IN ('active', 'pending', 'nová', 'rozpracováno')
            AND j.start_date IS NOT NULL
            AND j.start_date >= ?
            GROUP BY e.id, j.start_date
            HAVING COUNT(*) > 1
        ''', (today.isoformat(),)).fetchall()
    except Exception as e:
        print(f"Conflict warnings error: {e}")
        conflicts = []
    
    for conflict in conflicts:
        warnings.append({
            'type': 'double_booking',
            'severity': 'high',
            'employee_id': conflict['id'],
            'employee': conflict['name'],
            'date': conflict['start_date'],
            'clients': conflict['clients'],
            'message': f"⚠️ {conflict['name']} přiřazen k {conflict['job_count']} zakázkám dne {conflict['start_date']}"
        })
    
    # Varování před přetížením v týdnu
    week_end = today + timedelta(days=7)
    weekly_load = db.execute('''
        SELECT e.id, e.name,
               COUNT(DISTINCT a.job_id) as jobs_count,
               COALESCE(SUM(j.estimated_hours), 0) as estimated_hours
        FROM employees e
        JOIN job_assignments a ON a.employee_id = e.id
        JOIN jobs j ON j.id = a.job_id
        WHERE j.status IN ('active', 'pending')
        AND j.start_date BETWEEN ? AND ?
        GROUP BY e.id
        HAVING estimated_hours > 50
    ''', (today.isoformat(), week_end.isoformat())).fetchall()
    
    for load in weekly_load:
        warnings.append({
            'type': 'weekly_overload',
            'severity': 'medium',
            'employee_id': load['id'],
            'employee': load['name'],
            'hours': load['estimated_hours'],
            'message': f"🔴 {load['name']} má naplánováno {load['estimated_hours']}h tento týden"
        })
    
    return warnings


def get_seasonal_adjustments(today):
    """Sezónní doporučení pro plánování"""
    month = today.month
    adjustments = []
    
    # Sezónní tipy podle měsíce
    seasonal_tips = {
        1: [
            {'tip': 'Plánování jarních výsadeb', 'priority': 'medium'},
            {'tip': 'Kontrola zimní ochrany rostlin', 'priority': 'high'},
            {'tip': 'Údržba nářadí před sezónou', 'priority': 'low'}
        ],
        2: [
            {'tip': 'Objednávka sadby na jaro', 'priority': 'high'},
            {'tip': 'Řez ovocných stromů', 'priority': 'high'},
            {'tip': 'Příprava na jarní práce', 'priority': 'medium'}
        ],
        3: [
            {'tip': 'Start hlavní sezóny - navýšit kapacitu', 'priority': 'high'},
            {'tip': 'Jarní hnojení trávníků', 'priority': 'medium'},
            {'tip': 'Výsadba stromů a keřů', 'priority': 'high'}
        ],
        4: [
            {'tip': 'Vrchol jarních prací', 'priority': 'high'},
            {'tip': 'Výsadba trvalek', 'priority': 'high'},
            {'tip': 'Mulčování záhonů', 'priority': 'medium'}
        ],
        5: [
            {'tip': 'Výsadba letniček', 'priority': 'high'},
            {'tip': 'Pravidelné sekání zahájeno', 'priority': 'high'},
            {'tip': 'Závlaha při suchém počasí', 'priority': 'medium'}
        ],
        6: [
            {'tip': 'Intenzivní údržba', 'priority': 'high'},
            {'tip': 'Živé ploty - první střih', 'priority': 'high'},
            {'tip': 'Kontrola škůdců', 'priority': 'medium'}
        ],
        7: [
            {'tip': 'Závlaha je klíčová', 'priority': 'high'},
            {'tip': 'Letní řez stromů', 'priority': 'medium'},
            {'tip': 'Dovolené - plánovat kapacity', 'priority': 'high'}
        ],
        8: [
            {'tip': 'Příprava na podzimní výsadby', 'priority': 'medium'},
            {'tip': 'Objednávka podzimních cibulovin', 'priority': 'medium'},
            {'tip': 'Závlaha při vedru', 'priority': 'high'}
        ],
        9: [
            {'tip': 'Podzimní výsadby začínají', 'priority': 'high'},
            {'tip': 'Vertikutace trávníků', 'priority': 'high'},
            {'tip': 'Výsadba cibulovin', 'priority': 'high'}
        ],
        10: [
            {'tip': 'Hrabání listí', 'priority': 'high'},
            {'tip': 'Poslední výsadby stromů', 'priority': 'high'},
            {'tip': 'Příprava na zimu', 'priority': 'medium'}
        ],
        11: [
            {'tip': 'Zimní ochrana rostlin', 'priority': 'high'},
            {'tip': 'Závěrečné práce před zimou', 'priority': 'high'},
            {'tip': 'Plánování další sezóny', 'priority': 'medium'}
        ],
        12: [
            {'tip': 'Administrativa a plánování', 'priority': 'high'},
            {'tip': 'Údržba strojů', 'priority': 'high'},
            {'tip': 'Vánoční výzdoba', 'priority': 'medium'}
        ]
    }
    
    adjustments = seasonal_tips.get(month, [])
    
    # Přidej sezónní varování
    if month in [12, 1, 2]:
        adjustments.append({
            'tip': '❄️ ZIMNÍ OBDOBÍ: Omezit venkovní práce při mrazu',
            'priority': 'high',
            'type': 'warning'
        })
    elif month in [6, 7, 8]:
        adjustments.append({
            'tip': '☀️ LETNÍ OBDOBÍ: Zajistit pitný režim pro tým',
            'priority': 'high',
            'type': 'warning'
        })
    
    return adjustments


def get_efficiency_tips(db):
    """Tipy pro zvýšení efektivity na základě dat"""
    tips = []
    
    # Analyzuj historická data
    avg_job_duration = db.execute('''
        SELECT AVG(julianday(planned_end_date) - julianday(start_date)) as avg_days
        FROM jobs
        WHERE status IN ('completed', 'Dokončeno')
        AND planned_end_date IS NOT NULL AND start_date IS NOT NULL
    ''').fetchone()
    
    if avg_job_duration and avg_job_duration['avg_days']:
        tips.append({
            'metric': 'Průměrná délka zakázky',
            'value': f"{avg_job_duration['avg_days']:.1f} dní",
            'tip': 'Optimalizujte workflow pro zkrácení doby realizace'
        })
    
    # Nejproduktivnější dny
    productive_days = db.execute('''
        SELECT strftime('%w', date) as day_of_week,
               AVG(hours) as avg_hours
        FROM timesheets
        WHERE date >= date('now', '-90 days')
        GROUP BY strftime('%w', date)
        ORDER BY avg_hours DESC
        LIMIT 1
    ''').fetchone()
    
    day_names = ['Neděle', 'Pondělí', 'Úterý', 'Středa', 'Čtvrtek', 'Pátek', 'Sobota']
    if productive_days and productive_days['day_of_week']:
        day_name = day_names[int(productive_days['day_of_week'])]
        tips.append({
            'metric': 'Nejproduktivnější den',
            'value': day_name,
            'tip': f'Plánujte náročné práce na {day_name}'
        })
    
    return tips


# =============================================================================
# 4. BIOINTELIGENCE (Plant Intelligence)
# =============================================================================

def get_plant_intelligence():
    """Biointeligence pro správu rostlin"""
    try:
        db = get_db_with_row_factory()
        today = datetime.now().date()
        
        result = {
            'growth_predictions': [],
            'weather_alerts': [],
            'watering_recommendations': [],
            'health_alerts': []
        }
        
        try:
            result['growth_predictions'] = get_growth_predictions(db, today)
        except Exception as e:
            print(f"Growth predictions error: {e}")
            
        try:
            result['weather_alerts'] = get_plant_weather_alerts(today)
        except Exception as e:
            print(f"Plant weather alerts error: {e}")
            
        try:
            result['watering_recommendations'] = get_watering_recommendations(db, today)
        except Exception as e:
            print(f"Watering recommendations error: {e}")
            
        try:
            result['health_alerts'] = get_plant_health_alerts(db)
        except Exception as e:
            print(f"Plant health alerts error: {e}")
        
        return jsonify(result)
    except Exception as e:
        print(f"Plant intelligence error: {e}")
        return jsonify({
            'growth_predictions': [],
            'weather_alerts': get_plant_weather_alerts(datetime.now().date()),
            'watering_recommendations': [],
            'health_alerts': []
        })


def get_growth_predictions(db, today):
    """Predikce růstu rostlin ve školce"""
    predictions = []
    
    # Získej rostliny ze školky - OPRAVENO: species místo plant_name
    try:
        plants = db.execute('''
            SELECT np.id, np.species as plant_name, np.variety, np.quantity, np.status,
                   np.planted_date, np.location, np.notes
            FROM nursery_plants np
            WHERE np.status IN ('growing', 'seedling', 'active')
        ''').fetchall()
    except:
        plants = []
    
    for plant in plants:
        planted = plant['planted_date']
        if planted:
            try:
                planted_date = datetime.fromisoformat(planted).date()
                days_growing = (today - planted_date).days
            except:
                days_growing = 0
        else:
            days_growing = 0
        
        # Odhad růstu (zjednodušený model)
        growth_rate = 'medium'
        rate_multiplier = {'slow': 0.5, 'medium': 1.0, 'fast': 1.5}.get(growth_rate, 1.0)
        
        estimated_ready_days = int(90 / rate_multiplier)  # Základní odhad 90 dní
        days_remaining = max(0, estimated_ready_days - days_growing)
        
        progress = min(100, int((days_growing / estimated_ready_days) * 100)) if estimated_ready_days > 0 else 0
        
        predictions.append({
            'id': plant['id'],
            'name': plant['plant_name'] or 'Neznámá rostlina',
            'variety': plant['variety'],
            'quantity': plant['quantity'],
            'days_growing': days_growing,
            'progress': progress,
            'estimated_ready': (today + timedelta(days=days_remaining)).isoformat() if days_remaining > 0 else 'Připraveno',
            'days_remaining': days_remaining,
            'growth_rate': growth_rate,
            'status': 'ready' if progress >= 100 else 'growing'
        })
    
    # Seřaď podle progress
    predictions.sort(key=lambda x: x['progress'], reverse=True)
    
    return predictions


def get_plant_weather_alerts(today):
    """Upozornění na mrazy a extrémní počasí pro rostliny"""
    alerts = []
    
    # Simulace předpovědi (v produkci nahradit reálným API)
    forecast = simulate_weather_forecast(today)
    
    for day in forecast[:7]:  # Příštích 7 dní
        # Mráz
        if day['temp'] < 0:
            alerts.append({
                'date': day['date'],
                'type': 'frost',
                'severity': 'critical' if day['temp'] < -5 else 'warning',
                'temp': day['temp'],
                'message': f"🥶 MRÁZ {day['date']}: {day['temp']}°C - Ochránit citlivé rostliny!",
                'actions': [
                    'Přikrýt citlivé rostliny',
                    'Přesunout nádoby do skleníku',
                    'Zkontrolovat mulčování'
                ]
            })
        
        # Vedro
        if day['temp'] > 30:
            alerts.append({
                'date': day['date'],
                'type': 'heat',
                'severity': 'warning',
                'temp': day['temp'],
                'message': f"🌡️ VEDRO {day['date']}: {day['temp']}°C - Zvýšit zálivku!",
                'actions': [
                    'Zalévat ráno a večer',
                    'Stínění citlivých rostlin',
                    'Mulčování pro udržení vlhkosti'
                ]
            })
        
        # Silný déšť
        if day['rain_chance'] > 80:
            alerts.append({
                'date': day['date'],
                'type': 'heavy_rain',
                'severity': 'info',
                'message': f"🌧️ Silný déšť {day['date']} - Přerušit zálivku",
                'actions': [
                    'Pozastavit automatickou závlahu',
                    'Zkontrolovat odvodnění'
                ]
            })
    
    return alerts


def get_watering_recommendations(db, today):
    """Doporučení zálivky podle klimatu a potřeb rostlin"""
    recommendations = []
    
    # Získej rostliny - OPRAVENO: species místo plant_name, bez join na plant_species
    try:
        plants = db.execute('''
            SELECT np.id, np.species as plant_name, np.quantity, np.location,
                   np.light_requirements
            FROM nursery_plants np
            WHERE np.status IN ('growing', 'seedling', 'active')
        ''').fetchall()
    except:
        plants = []
    
    # Simulace aktuálního počasí
    current_temp = 15  # V produkci z API
    is_hot = current_temp > 25
    is_cold = current_temp < 5
    
    for plant in plants:
        water_needs = 'medium'  # Default
        days_since = 3  # Default - předpokládáme že potřebuje zálivku
        
        # Doporučený interval zálivky
        base_interval = {'low': 7, 'medium': 3, 'high': 1}.get(water_needs, 3)
        
        # Úprava podle teploty
        if is_hot:
            interval = max(1, base_interval - 1)
        elif is_cold:
            interval = base_interval + 2
        else:
            interval = base_interval
        
        # Určení urgence - pro demo zobrazíme nějaké
        import random
        urgency = random.choice(['today', 'tomorrow', 'ok', 'ok'])
        
        if urgency in ['now', 'today', 'tomorrow']:
            recommendations.append({
                'id': plant['id'],
                'name': plant['plant_name'] or 'Rostlina',
                'location': plant['location'],
                'quantity': plant['quantity'],
                'water_needs': water_needs,
                'days_since_watered': days_since if days_since < 999 else None,
                'urgency': urgency,
                'recommended_interval': interval,
                'message': get_watering_message(urgency, plant['plant_name'] or 'Rostlina', days_since)
            })
    
    # Seřaď podle urgence
    urgency_order = {'now': 0, 'today': 1, 'tomorrow': 2}
    recommendations.sort(key=lambda x: urgency_order.get(x['urgency'], 3))
    
    return recommendations[:10]  # Limit na 10


def get_watering_message(urgency, plant_name, days_since):
    """Generuj zprávu pro zálivku"""
    if urgency == 'now':
        return f"🚨 {plant_name} - URGENTNĚ ZALÍT! ({days_since} dní bez vody)"
    elif urgency == 'today':
        return f"💧 {plant_name} - Zalít dnes"
    elif urgency == 'tomorrow':
        return f"📅 {plant_name} - Naplánovat zálivku na zítra"
    return f"✅ {plant_name} - OK"


def get_plant_health_alerts(db):
    """Upozornění na zdravotní problémy rostlin"""
    alerts = []
    
    # Kontrola rostlin s poznámkami o problémech
    problem_keywords = ['nemoc', 'škůdce', 'žlout', 'vadne', 'hniloba', 'plíseň', 
                       'mšice', 'housenka', 'slimák', 'suchý', 'poškoz']
    
    try:
        plants = db.execute('''
            SELECT id, species as plant_name, notes, status, quantity, location
            FROM nursery_plants
            WHERE status NOT IN ('sold', 'dead', 'removed')
            AND notes IS NOT NULL AND notes != ''
        ''').fetchall()
    except:
        plants = []
    
    for plant in plants:
        notes = (plant['notes'] or '').lower()
        for keyword in problem_keywords:
            if keyword in notes:
                alerts.append({
                    'id': plant['id'],
                    'name': plant['plant_name'] or 'Rostlina',
                    'location': plant['location'],
                    'quantity': plant['quantity'],
                    'issue': keyword,
                    'notes': plant['notes'],
                    'severity': 'warning',
                    'recommendation': get_health_recommendation(keyword)
                })
                break
    
    return alerts


def get_health_recommendation(issue):
    """Doporučení pro zdravotní problémy"""
    recommendations = {
        'nemoc': 'Izolovat rostlinu, aplikovat fungicid',
        'škůdce': 'Zkontrolovat a aplikovat insekticid',
        'žlout': 'Zkontrolovat zálivku a výživu',
        'vadne': 'Zkontrolovat zálivku, případně přesadit',
        'hniloba': 'Omezit zálivku, zlepšit odvodnění',
        'plíseň': 'Zlepšit větrání, aplikovat fungicid',
        'mšice': 'Aplikovat mýdlový roztok nebo insekticid',
        'housenka': 'Mechanicky odstranit nebo aplikovat Bacillus thuringiensis',
        'slimák': 'Aplikovat moluskocid nebo pasti',
        'suchý': 'Zvýšit zálivku',
        'poškoz': 'Ochránit před dalším poškozením'
    }
    return recommendations.get(issue, 'Zkontrolovat a sledovat stav')


# =============================================================================
# POMOCNÉ FUNKCE
# =============================================================================

def generate_recommendations(data):
    """Generuj souhrnná doporučení"""
    recommendations = []
    
    # Z počasí
    if data['weather_alerts']:
        recommendations.append({
            'category': 'weather',
            'priority': 'high',
            'count': len(data['weather_alerts']),
            'message': f"⛈️ {len(data['weather_alerts'])} zakázek ohroženo počasím"
        })
    
    # Z materiálu
    critical_materials = [m for m in data['material_predictions'] if m['urgency'] == 'critical']
    if critical_materials:
        recommendations.append({
            'category': 'materials',
            'priority': 'high',
            'count': len(critical_materials),
            'message': f"📦 {len(critical_materials)} materiálů kriticky dochází"
        })
    
    # Z vytížení
    workload = data['workload_balance']
    if workload.get('recommendations'):
        recommendations.append({
            'category': 'workload',
            'priority': 'medium',
            'count': len(workload['recommendations']),
            'message': f"👷 {len(workload['recommendations'])} problémů s vytížením týmu"
        })
    
    # Z anomálií
    critical_anomalies = [a for a in data['anomalies'] if a['severity'] == 'critical']
    if critical_anomalies:
        recommendations.append({
            'category': 'anomalies',
            'priority': 'high',
            'count': len(critical_anomalies),
            'message': f"🚨 {len(critical_anomalies)} kritických problémů vyžaduje pozornost"
        })
    
    return recommendations


def calculate_health_score(data):
    """Vypočítej skóre zdraví firmy (0-100)"""
    score = 100
    
    # Penalizace za problémy
    score -= len(data['weather_alerts']) * 5
    score -= len([m for m in data['material_predictions'] if m['urgency'] == 'critical']) * 10
    score -= len([m for m in data['material_predictions'] if m['urgency'] == 'warning']) * 5
    score -= len([a for a in data['anomalies'] if a['severity'] == 'critical']) * 15
    score -= len([a for a in data['anomalies'] if a['severity'] == 'warning']) * 5
    
    # Bonus za vyvážené vytížení
    workload_score = data['workload_balance'].get('balance_score', 50)
    score = (score + workload_score) / 2
    
    return max(0, min(100, int(score)))


# =============================================================================
# API ROUTES (pro registraci v main.py)
# =============================================================================

def register_routes(app):
    """Registruj všechny AI Operátor routes"""
    
    @app.route('/api/ai/dashboard')
    @login_required
    def api_ai_dashboard():
        return get_ai_dashboard()
    
    @app.route('/api/ai/planning-optimization')
    @login_required
    def api_planning_optimization():
        return get_planning_optimization()
    
    @app.route('/api/ai/plant-intelligence')
    @login_required
    def api_plant_intelligence():
        return get_plant_intelligence()
    
    @app.route('/api/ai/weather-forecast')
    @login_required
    def api_weather_forecast():
        today = datetime.now().date()
        forecast = simulate_weather_forecast(today)
        return jsonify(forecast)
    
    @app.route('/api/ai/material-predictions')
    @login_required
    def api_material_predictions():
        db = get_db_with_row_factory()
        predictions = get_material_predictions_data(db)
        return jsonify(predictions)
    
    @app.route('/api/ai/workload-analysis')
    @login_required
    def api_workload_analysis():
        db = get_db_with_row_factory()
        today = datetime.now().date()
        period = request.args.get('period', 'week')
        analysis = get_workload_balance_data(db, today, period)
        return jsonify(analysis)
    
    @app.route('/api/ai/jobs-overview')
    @login_required
    def api_jobs_overview():
        """Přehled zakázek s historií"""
        db = get_db_with_row_factory()
        return jsonify(get_jobs_overview_data(db))
    
    @app.route('/api/ai/timeline-stats')
    @login_required
    def api_timeline_stats():
        """Statistiky z timeline/výkazů"""
        db = get_db_with_row_factory()
        period = request.args.get('period', 'month')
        return jsonify(get_timeline_stats(db, period))
    
    @app.route('/api/ai/employee-stats/<int:employee_id>')
    @login_required
    def api_employee_stats(employee_id):
        """Detailní statistiky zaměstnance"""
        db = get_db_with_row_factory()
        return jsonify(get_employee_detailed_stats(db, employee_id))
    
    print("✅ AI Operátor API loaded")


def get_jobs_overview_data(db):
    """Přehled všech zakázek se statistikami"""
    try:
        # Aktivní zakázky
        active_jobs = db.execute('''
            SELECT j.id, j.client, j.name, j.status, j.city, j.start_date, 
                   j.planned_end_date, j.estimated_hours, j.actual_hours,
                   j.estimated_value, j.actual_value, j.progress,
                   COUNT(DISTINCT t.id) as task_count,
                   SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) as tasks_done
            FROM jobs j
            LEFT JOIN tasks t ON t.job_id = j.id
            WHERE j.status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
            GROUP BY j.id
            ORDER BY j.start_date DESC
        ''').fetchall()
        
        # Statistiky
        total_active = len(active_jobs)
        total_value = sum(j['estimated_value'] or 0 for j in active_jobs)
        
        # Dokončené tento měsíc
        today = datetime.now().date()
        month_start = today.replace(day=1)
        completed_this_month = db.execute('''
            SELECT COUNT(*) as count, COALESCE(SUM(actual_value), 0) as value
            FROM jobs 
            WHERE status IN ('Dokončeno', 'completed')
            AND completed_at >= ?
        ''', (month_start.isoformat(),)).fetchone()
        
        # Zpoždění
        delayed = db.execute('''
            SELECT COUNT(*) as count
            FROM jobs 
            WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
            AND planned_end_date < ?
            AND planned_end_date IS NOT NULL
        ''', (today.isoformat(),)).fetchone()
        
        return {
            'active_jobs': [dict(j) for j in active_jobs],
            'stats': {
                'total_active': total_active,
                'total_estimated_value': total_value,
                'completed_this_month': completed_this_month['count'] if completed_this_month else 0,
                'completed_value': completed_this_month['value'] if completed_this_month else 0,
                'delayed_count': delayed['count'] if delayed else 0
            }
        }
    except Exception as e:
        print(f"Jobs overview error: {e}")
        return {'active_jobs': [], 'stats': {}}


def get_timeline_stats(db, period='month'):
    """Statistiky z výkazů/timeline"""
    today = datetime.now().date()
    
    # Určení období
    if period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'last_week':
        end_date = today - timedelta(days=today.weekday()) - timedelta(days=1)
        start_date = end_date - timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        next_month = today.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)
    elif period == 'last_month':
        first_this_month = today.replace(day=1)
        end_date = first_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        start_date = today - timedelta(days=30)
        end_date = today
    
    try:
        # Celkové hodiny podle zaměstnanců
        by_employee = db.execute('''
            SELECT e.id, e.name, e.role,
                   COALESCE(SUM(t.hours), 0) as total_hours,
                   COUNT(DISTINCT t.id) as entries
            FROM employees e
            LEFT JOIN timesheets t ON t.employee_id = e.id
                AND (t.date BETWEEN ? AND ? OR t.date BETWEEN ? AND ?)
            WHERE e.status = 'active'
            GROUP BY e.id
            ORDER BY total_hours DESC
        ''', (start_date.isoformat(), end_date.isoformat(),
              start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))).fetchall()
        
        # Celkové hodiny podle zakázek
        by_job = db.execute('''
            SELECT j.id, j.client, j.name,
                   COALESCE(SUM(t.hours), 0) as total_hours,
                   COUNT(DISTINCT t.id) as entries
            FROM jobs j
            LEFT JOIN timesheets t ON t.job_id = j.id
                AND (t.date BETWEEN ? AND ? OR t.date BETWEEN ? AND ?)
            GROUP BY j.id
            HAVING total_hours > 0
            ORDER BY total_hours DESC
            LIMIT 20
        ''', (start_date.isoformat(), end_date.isoformat(),
              start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))).fetchall()
        
        # Denní breakdown
        daily = db.execute('''
            SELECT date, SUM(hours) as total_hours, COUNT(DISTINCT employee_id) as workers
            FROM timesheets
            WHERE date BETWEEN ? AND ? OR date BETWEEN ? AND ?
            GROUP BY date
            ORDER BY date
        ''', (start_date.isoformat(), end_date.isoformat(),
              start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'))).fetchall()
        
        total_hours = sum(e['total_hours'] or 0 for e in by_employee)
        
        return {
            'period': period,
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
            'total_hours': round(total_hours, 1),
            'by_employee': [dict(e) for e in by_employee],
            'by_job': [dict(j) for j in by_job],
            'daily': [dict(d) for d in daily]
        }
    except Exception as e:
        print(f"Timeline stats error: {e}")
        return {'period': period, 'total_hours': 0, 'by_employee': [], 'by_job': [], 'daily': []}


def get_employee_detailed_stats(db, employee_id):
    """Detailní statistiky jednoho zaměstnance"""
    today = datetime.now().date()
    
    try:
        # Info o zaměstnanci
        employee = db.execute('''
            SELECT id, name, role, status, start_date
            FROM employees WHERE id = ?
        ''', (employee_id,)).fetchone()
        
        if not employee:
            return {'error': 'Zaměstnanec nenalezen'}
        
        # Posledních 30 dní
        month_ago = today - timedelta(days=30)
        
        # Výkazy
        timesheets = db.execute('''
            SELECT t.date, t.hours, t.place, t.activity, j.client as job_client
            FROM timesheets t
            LEFT JOIN jobs j ON j.id = t.job_id
            WHERE t.employee_id = ?
            ORDER BY t.date DESC
            LIMIT 50
        ''', (employee_id,)).fetchall()
        
        # Statistiky
        stats = db.execute('''
            SELECT 
                COALESCE(SUM(hours), 0) as total_hours,
                COUNT(*) as entries,
                COALESCE(AVG(hours), 0) as avg_hours_per_entry
            FROM timesheets
            WHERE employee_id = ?
            AND (date >= ? OR date >= ?)
        ''', (employee_id, month_ago.isoformat(), month_ago.strftime('%d.%m.%Y'))).fetchone()
        
        # Zakázky na kterých pracoval
        jobs_worked = db.execute('''
            SELECT DISTINCT j.id, j.client, j.name, j.status,
                   SUM(t.hours) as hours_on_job
            FROM timesheets t
            JOIN jobs j ON j.id = t.job_id
            WHERE t.employee_id = ?
            GROUP BY j.id
            ORDER BY hours_on_job DESC
            LIMIT 10
        ''', (employee_id,)).fetchall()
        
        return {
            'employee': dict(employee),
            'stats_30_days': {
                'total_hours': round(stats['total_hours'] or 0, 1),
                'entries': stats['entries'] or 0,
                'avg_hours': round(stats['avg_hours_per_entry'] or 0, 1)
            },
            'recent_timesheets': [dict(t) for t in timesheets],
            'jobs_worked': [dict(j) for j in jobs_worked]
        }
    except Exception as e:
        print(f"Employee stats error: {e}")
        return {'error': str(e)}


# Export pro použití v main.py
__all__ = ['register_routes', 'get_db']
