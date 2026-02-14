"""
GREEN DAVID APP - AI OPERÁTOR RULE ENGINE
==========================================
Deterministický rule engine podle PRD specifikace.
15 pravidel pro detekci problémů a generování insightů.

Autor: Green David s.r.o.
Verze: 2.0 (PRD compliant)
"""

from flask import jsonify, request
from datetime import datetime, timedelta
from functools import wraps
import json
import sqlite3

# Reference na get_db - nastaví se z main.py
get_db = None

def get_db_with_row_factory():
    """Získej DB connection s row_factory pro dict přístup"""
    db = get_db()
    db.row_factory = sqlite3.Row
    return db

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# RULE ENGINE - HLAVNÍ TŘÍDA
# =============================================================================

class RuleEngine:
    """Deterministický rule engine pro generování insightů"""
    
    def __init__(self, db):
        self.db = db
        self.insights_generated = []
    
    def run_all_rules(self):
        """Spusť všechna pravidla a vrať seznam nových insightů"""
        self.insights_generated = []
        today = datetime.now().date()
        
        # R1: Budget overrun - labor
        self._rule_budget_overrun_labor()
        
        # R2: Budget overrun - material
        self._rule_budget_overrun_material()
        
        # R3: Job behind schedule
        self._rule_job_behind_schedule(today)
        
        # R4: Task overdue
        self._rule_task_overdue(today)
        
        # R5: No activity on job
        self._rule_no_activity_on_job(today)
        
        # R6: Employee overload
        self._rule_employee_overload(today)
        
        # R7: Employee idle
        self._rule_employee_idle(today)
        
        # R8: Low stock
        self._rule_low_stock()
        
        # R9: Reservation exceeds stock
        self._rule_reservation_exceeds_stock()
        
        # R10: Missing location
        self._rule_missing_location()
        
        # R11: Missing estimates
        self._rule_missing_estimates()
        
        # R12: Missing photo documentation
        self._rule_missing_photo_doc()
        
        # R13: Completed not invoiced
        self._rule_completed_not_invoiced()
        
        # R14: Weather risk outdoor
        self._rule_weather_risk_outdoor(today)
        
        # R15: Inventory variance
        self._rule_inventory_variance()
        
        return self.insights_generated
    
    def _create_or_update_insight(self, key, insight_type, severity, title, summary, 
                                   evidence, actions, entity_type=None, entity_id=None,
                                   confidence='HIGH'):
        """Vytvoř nebo aktualizuj insight (idempotentní)"""
        
        # Zkontroluj jestli insight s tímto klíčem už existuje
        existing = self.db.execute(
            'SELECT id, status FROM insight WHERE insight_key = ?', (key,)
        ).fetchone()
        
        if existing:
            # Pokud je resolved/dismissed a problém stále trvá, znovu otevři
            if existing['status'] in ('resolved', 'dismissed'):
                self.db.execute('''
                    UPDATE insight SET 
                        status = 'open',
                        severity = ?,
                        title = ?,
                        summary = ?,
                        evidence_json = ?,
                        actions_json = ?,
                        updated_at = datetime('now'),
                        resolved_at = NULL
                    WHERE id = ?
                ''', (severity, title, summary, json.dumps(evidence), 
                      json.dumps(actions), existing['id']))
                self.db.commit()
            return existing['id']
        
        # Vytvoř nový insight
        cursor = self.db.execute('''
            INSERT INTO insight (insight_key, type, severity, status, title, summary,
                                evidence_json, actions_json, entity_type, entity_id, confidence)
            VALUES (?, ?, ?, 'open', ?, ?, ?, ?, ?, ?, ?)
        ''', (key, insight_type, severity, title, summary, 
              json.dumps(evidence), json.dumps(actions),
              entity_type, entity_id, confidence))
        self.db.commit()
        
        insight_id = cursor.lastrowid
        self.insights_generated.append({
            'id': insight_id,
            'key': key,
            'type': insight_type,
            'severity': severity,
            'title': title
        })
        
        return insight_id
    
    # =========================================================================
    # PRAVIDLA R1-R15
    # =========================================================================
    
    def _rule_budget_overrun_labor(self):
        """R1: Překročení rozpočtu práce > 110%"""
        try:
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.name, j.budget_labor, j.actual_labor_cost,
                       j.estimated_hours, j.actual_hours
                FROM jobs j
                WHERE j.status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND j.budget_labor > 0
                AND j.actual_labor_cost > j.budget_labor * 1.1
            ''').fetchall()
            
            for job in jobs:
                percent = (job['actual_labor_cost'] / job['budget_labor']) * 100
                key = f"R1_BUDGET_LABOR_{job['id']}"
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='BUDGET_OVERRUN_LABOR',
                    severity='CRITICAL',
                    title=f"💰 Překročený rozpočet práce: {job['client'] or job['name']}",
                    summary=f"Náklady na práci dosáhly {percent:.0f}% rozpočtu ({job['actual_labor_cost']:,.0f} / {job['budget_labor']:,.0f} Kč)",
                    evidence={
                        'budget_labor': job['budget_labor'],
                        'actual_labor_cost': job['actual_labor_cost'],
                        'percent': round(percent, 1),
                        'estimated_hours': job['estimated_hours'],
                        'actual_hours': job['actual_hours']
                    },
                    actions=[
                        {'type': 'ESCALATE_BUDGET_OVERRUN', 'label': 'Eskalovat', 'payload': {'job_id': job['id']}},
                        {'type': 'link', 'label': 'Otevřít zakázku', 'url': f"/job-detail.html?id={job['id']}"}
                    ],
                    entity_type='job',
                    entity_id=job['id']
                )
        except Exception as e:
            print(f"R1 error: {e}")
    
    def _rule_budget_overrun_material(self):
        """R2: Překročení rozpočtu materiálu > 110%"""
        try:
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.name, j.budget_materials, j.actual_material_cost
                FROM jobs j
                WHERE j.status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND j.budget_materials > 0
                AND j.actual_material_cost > j.budget_materials * 1.1
            ''').fetchall()
            
            for job in jobs:
                percent = (job['actual_material_cost'] / job['budget_materials']) * 100
                key = f"R2_BUDGET_MATERIAL_{job['id']}"
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='BUDGET_OVERRUN_MATERIAL',
                    severity='CRITICAL',
                    title=f"📦 Překročený rozpočet materiálu: {job['client'] or job['name']}",
                    summary=f"Náklady na materiál dosáhly {percent:.0f}% rozpočtu",
                    evidence={
                        'budget_materials': job['budget_materials'],
                        'actual_material_cost': job['actual_material_cost'],
                        'percent': round(percent, 1)
                    },
                    actions=[
                        {'type': 'REVIEW_MATERIAL_USAGE', 'label': 'Kontrola výdejů', 'payload': {'job_id': job['id']}},
                        {'type': 'link', 'label': 'Otevřít zakázku', 'url': f"/job-detail.html?id={job['id']}"}
                    ],
                    entity_type='job',
                    entity_id=job['id']
                )
        except Exception as e:
            print(f"R2 error: {e}")
    
    def _rule_job_behind_schedule(self, today):
        """R3: Zakázka ve skluzu - deadline < 7 dní a nízký progress"""
        try:
            deadline_soon = today + timedelta(days=7)
            
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.name, j.planned_end_date, j.deadline,
                       j.progress, j.completion_percent
                FROM jobs j
                WHERE j.status IN ('active', 'Aktivní', 'rozpracováno', 'pending')
                AND (j.planned_end_date IS NOT NULL OR j.deadline IS NOT NULL)
                AND (j.planned_end_date <= ? OR j.deadline <= ?)
            ''', (deadline_soon.isoformat(), deadline_soon.isoformat())).fetchall()
            
            for job in jobs:
                progress = job['progress'] or job['completion_percent'] or 0
                deadline = job['deadline'] or job['planned_end_date']
                
                # Očekávaný progress na základě zbývajícího času
                if deadline:
                    try:
                        deadline_date = datetime.fromisoformat(deadline).date()
                        days_left = (deadline_date - today).days
                        
                        # Pokud zbývá málo času a progress je nízký
                        if days_left <= 7 and progress < 70:
                            key = f"R3_BEHIND_SCHEDULE_{job['id']}"
                            
                            self._create_or_update_insight(
                                key=key,
                                insight_type='JOB_BEHIND_SCHEDULE',
                                severity='WARN' if days_left > 3 else 'CRITICAL',
                                title=f"⏰ Ve skluzu: {job['client'] or job['name']}",
                                summary=f"Deadline za {days_left} dní, progress pouze {progress}%",
                                evidence={
                                    'deadline': deadline,
                                    'days_left': days_left,
                                    'progress': progress,
                                    'expected_progress': min(100, 100 - (days_left * 10))
                                },
                                actions=[
                                    {'type': 'MOVE_JOB', 'label': 'Přeplánovat', 'payload': {'job_id': job['id']}},
                                    {'type': 'REASSIGN_EMPLOYEES', 'label': 'Přidat kapacitu', 'payload': {'job_id': job['id']}},
                                    {'type': 'link', 'label': 'Detail', 'url': f"/job-detail.html?id={job['id']}"}
                                ],
                                entity_type='job',
                                entity_id=job['id']
                            )
                    except:
                        pass
        except Exception as e:
            print(f"R3 error: {e}")
    
    def _rule_task_overdue(self, today):
        """R4: Úkol po termínu"""
        try:
            tasks = self.db.execute('''
                SELECT t.id, t.title, t.due_date, t.status, t.employee_id,
                       j.client, j.name as job_name, e.name as employee_name
                FROM tasks t
                LEFT JOIN jobs j ON j.id = t.job_id
                LEFT JOIN employees e ON e.id = t.employee_id
                WHERE t.status NOT IN ('done', 'completed', 'cancelled')
                AND t.due_date IS NOT NULL
                AND t.due_date < ?
            ''', (today.isoformat(),)).fetchall()
            
            for task in tasks:
                try:
                    due_date = datetime.fromisoformat(task['due_date']).date()
                    days_overdue = (today - due_date).days
                    
                    key = f"R4_TASK_OVERDUE_{task['id']}"
                    
                    self._create_or_update_insight(
                        key=key,
                        insight_type='TASK_OVERDUE',
                        severity='WARN' if days_overdue <= 3 else 'CRITICAL',
                        title=f"📋 Úkol po termínu: {task['title'][:50]}",
                        summary=f"Zpoždění {days_overdue} dní" + (f" ({task['client']})" if task['client'] else ""),
                        evidence={
                            'task_id': task['id'],
                            'due_date': task['due_date'],
                            'days_overdue': days_overdue,
                            'assigned_to': task['employee_name'],
                            'job': task['client'] or task['job_name']
                        },
                        actions=[
                            {'type': 'REASSIGN_TASK', 'label': 'Přeřadit', 'payload': {'task_id': task['id']}},
                            {'type': 'EXTEND_DEADLINE', 'label': 'Posunout termín', 'payload': {'task_id': task['id']}},
                            {'type': 'link', 'label': 'Detail úkolu', 'url': f"/tasks.html?id={task['id']}"}
                        ],
                        entity_type='task',
                        entity_id=task['id']
                    )
                except:
                    pass
        except Exception as e:
            print(f"R4 error: {e}")
    
    def _rule_no_activity_on_job(self, today):
        """R5: Zakázka bez aktivity 5+ dní"""
        try:
            five_days_ago = today - timedelta(days=5)
            
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.name, j.status,
                       MAX(t.date) as last_activity,
                       j.project_manager_id
                FROM jobs j
                LEFT JOIN timesheets t ON t.job_id = j.id
                WHERE j.status IN ('active', 'Aktivní', 'rozpracováno', 'pending')
                GROUP BY j.id
            ''').fetchall()
            
            for job in jobs:
                last_activity = job['last_activity']
                
                if last_activity:
                    try:
                        # Zkus různé formáty datumu
                        try:
                            last_date = datetime.fromisoformat(last_activity).date()
                        except:
                            last_date = datetime.strptime(last_activity, '%d.%m.%Y').date()
                        
                        days_inactive = (today - last_date).days
                    except:
                        days_inactive = 999
                else:
                    days_inactive = 999
                
                if days_inactive >= 5:
                    key = f"R5_NO_ACTIVITY_{job['id']}"
                    
                    self._create_or_update_insight(
                        key=key,
                        insight_type='NO_ACTIVITY_ON_JOB',
                        severity='WARN',
                        title=f"💤 Bez aktivity: {job['client'] or job['name']}",
                        summary=f"{days_inactive} dní bez záznamu v timesheetu",
                        evidence={
                            'job_id': job['id'],
                            'last_activity': last_activity,
                            'days_inactive': days_inactive
                        },
                        actions=[
                            {'type': 'PING_MANAGER', 'label': 'Kontaktovat vedoucího', 'payload': {'job_id': job['id']}},
                            {'type': 'link', 'label': 'Zkontrolovat', 'url': f"/job-detail.html?id={job['id']}"}
                        ],
                        entity_type='job',
                        entity_id=job['id']
                    )
        except Exception as e:
            print(f"R5 error: {e}")
    
    def _rule_employee_overload(self, today):
        """R6: Zaměstnanec přetížený > 45h/týden"""
        try:
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            employees = self.db.execute('''
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
                key = f"R6_OVERLOAD_{emp['id']}_{week_start.isoformat()}"
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='EMPLOYEE_OVERLOAD',
                    severity='WARN' if hours <= 50 else 'CRITICAL',
                    title=f"👷 Přetížený: {emp['name']}",
                    summary=f"{hours:.0f}h tento týden (limit 45h)",
                    evidence={
                        'employee_id': emp['id'],
                        'employee_name': emp['name'],
                        'hours_this_week': hours,
                        'week_start': week_start.isoformat(),
                        'overtime': hours - 40
                    },
                    actions=[
                        {'type': 'REASSIGN_EMPLOYEES', 'label': 'Přerozdělit práci', 'payload': {'employee_id': emp['id']}},
                        {'type': 'link', 'label': 'Výkazy', 'url': f"/employee-detail.html?id={emp['id']}"}
                    ],
                    entity_type='employee',
                    entity_id=emp['id']
                )
        except Exception as e:
            print(f"R6 error: {e}")
    
    def _rule_employee_idle(self, today):
        """R7: Zaměstnanec bez práce další 2 dny"""
        try:
            two_days = today + timedelta(days=2)
            
            # Najdi zaměstnance bez přiřazených úkolů na příští 2 dny
            employees = self.db.execute('''
                SELECT e.id, e.name
                FROM employees e
                WHERE e.status = 'active'
                AND e.id NOT IN (
                    SELECT DISTINCT t.employee_id 
                    FROM tasks t 
                    WHERE t.employee_id IS NOT NULL
                    AND t.status NOT IN ('done', 'completed', 'cancelled')
                    AND (t.due_date >= ? OR t.due_date IS NULL)
                )
            ''', (today.isoformat(),)).fetchall()
            
            for emp in employees:
                key = f"R7_IDLE_{emp['id']}_{today.isoformat()}"
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='EMPLOYEE_IDLE',
                    severity='INFO',
                    title=f"📭 Volná kapacita: {emp['name']}",
                    summary=f"Žádné přiřazené úkoly na příští dny",
                    evidence={
                        'employee_id': emp['id'],
                        'employee_name': emp['name']
                    },
                    actions=[
                        {'type': 'ASSIGN_TASKS', 'label': 'Přidělit úkoly', 'payload': {'employee_id': emp['id']}},
                        {'type': 'link', 'label': 'Detail', 'url': f"/employee-detail.html?id={emp['id']}"}
                    ],
                    entity_type='employee',
                    entity_id=emp['id']
                )
        except Exception as e:
            print(f"R7 error: {e}")
    
    def _rule_low_stock(self):
        """R8: Materiál pod minimálním stavem"""
        try:
            items = self.db.execute('''
                SELECT id, name, qty, minStock, unit
                FROM warehouse_items
                WHERE status = 'active'
                AND qty < minStock
                AND minStock > 0
            ''').fetchall()
            
            for item in items:
                key = f"R8_LOW_STOCK_{item['id']}"
                ratio = item['qty'] / item['minStock'] if item['minStock'] > 0 else 0
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='LOW_STOCK',
                    severity='CRITICAL' if ratio < 0.3 else 'WARN',
                    title=f"📦 Dochází: {item['name']}",
                    summary=f"{item['qty']:.0f} {item['unit']} (min: {item['minStock']:.0f})",
                    evidence={
                        'item_id': item['id'],
                        'item_name': item['name'],
                        'current_qty': item['qty'],
                        'min_qty': item['minStock'],
                        'unit': item['unit'],
                        'ratio': round(ratio, 2)
                    },
                    actions=[
                        {'type': 'GENERATE_PURCHASE_LIST', 'label': 'Přidat do nákupu', 'payload': {'item_id': item['id']}},
                        {'type': 'link', 'label': 'Sklad', 'url': f"/warehouse.html?item={item['id']}"}
                    ],
                    entity_type='warehouse_item',
                    entity_id=item['id']
                )
        except Exception as e:
            print(f"R8 error: {e}")
    
    def _rule_reservation_exceeds_stock(self):
        """R9: Rezervace přesahuje dostupné množství"""
        try:
            items = self.db.execute('''
                SELECT id, name, qty, reserved_qty, unit
                FROM warehouse_items
                WHERE status = 'active'
                AND reserved_qty > qty
            ''').fetchall()
            
            for item in items:
                key = f"R9_RESERVATION_EXCEEDS_{item['id']}"
                shortage = item['reserved_qty'] - item['qty']
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='RESERVATION_EXCEEDS_STOCK',
                    severity='CRITICAL',
                    title=f"🚨 Konflikt rezervací: {item['name']}",
                    summary=f"Rezervováno {item['reserved_qty']:.0f}, skladem pouze {item['qty']:.0f} {item['unit']}",
                    evidence={
                        'item_id': item['id'],
                        'item_name': item['name'],
                        'current_qty': item['qty'],
                        'reserved_qty': item['reserved_qty'],
                        'shortage': shortage
                    },
                    actions=[
                        {'type': 'RESOLVE_RESERVATION_CONFLICT', 'label': 'Vyřešit konflikt', 'payload': {'item_id': item['id']}},
                        {'type': 'GENERATE_PURCHASE_LIST', 'label': 'Urychleně objednat', 'payload': {'item_id': item['id'], 'qty': shortage}}
                    ],
                    entity_type='warehouse_item',
                    entity_id=item['id']
                )
        except Exception as e:
            print(f"R9 error: {e}")
    
    def _rule_missing_location(self):
        """R10: Zakázka bez lokace"""
        try:
            jobs = self.db.execute('''
                SELECT id, client, name
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND (city IS NULL OR city = '')
            ''').fetchall()
            
            for job in jobs:
                key = f"R10_MISSING_LOCATION_{job['id']}"
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='MISSING_LOCATION',
                    severity='INFO',
                    title=f"📍 Chybí lokace: {job['client'] or job['name']}",
                    summary=f"Zakázka nemá vyplněnou adresu/město",
                    evidence={'job_id': job['id']},
                    actions=[
                        {'type': 'link', 'label': 'Doplnit', 'url': f"/job-detail.html?id={job['id']}"}
                    ],
                    entity_type='job',
                    entity_id=job['id']
                )
        except Exception as e:
            print(f"R10 error: {e}")
    
    def _rule_missing_estimates(self):
        """R11: Úkoly bez odhadu"""
        try:
            # Počet úkolů bez odhadu na aktivních zakázkách
            result = self.db.execute('''
                SELECT j.id, j.client, j.name, COUNT(t.id) as tasks_without_estimate
                FROM jobs j
                JOIN tasks t ON t.job_id = j.id
                WHERE j.status IN ('active', 'Aktivní', 'rozpracováno')
                AND t.status NOT IN ('done', 'completed', 'cancelled')
                GROUP BY j.id
                HAVING tasks_without_estimate > 3
            ''').fetchall()
            
            for job in result:
                key = f"R11_MISSING_ESTIMATES_{job['id']}"
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='MISSING_ESTIMATES',
                    severity='INFO',
                    title=f"⏱️ Chybí odhady: {job['client'] or job['name']}",
                    summary=f"{job['tasks_without_estimate']} úkolů bez časového odhadu",
                    evidence={
                        'job_id': job['id'],
                        'tasks_without_estimate': job['tasks_without_estimate']
                    },
                    actions=[
                        {'type': 'link', 'label': 'Doplnit odhady', 'url': f"/job-detail.html?id={job['id']}#tasks"}
                    ],
                    entity_type='job',
                    entity_id=job['id']
                )
        except Exception as e:
            print(f"R11 error: {e}")
    
    def _rule_missing_photo_doc(self):
        """R12: Chybějící foto dokumentace pro zakázky vyžadující fotky"""
        try:
            # Najdi aktivní zakázky které vyžadují foto dokumentaci
            # (landscaping, garden, outdoor typy nebo ty s photo_required flag)
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.name, j.type, j.status, j.created_at,
                       (SELECT COUNT(*) FROM attachments a 
                        WHERE a.entity_type = 'job' AND a.entity_id = j.id 
                        AND (a.mime_type LIKE 'image/%' OR a.filename LIKE '%.jpg' 
                             OR a.filename LIKE '%.png' OR a.filename LIKE '%.jpeg')) as photo_count
                FROM jobs j
                WHERE j.status IN ('active', 'Aktivní', 'rozpracováno', 'Dokončeno', 'completed')
                AND (j.type IN ('landscaping', 'garden', 'outdoor', 'zahrada', 'terasa', 'plot', 'venkovní') 
                     OR j.photo_required = 1)
            ''').fetchall()
            
            for job in jobs:
                photo_count = job['photo_count'] or 0
                
                # Zakázka bez fotek
                if photo_count == 0:
                    key = f"R12_MISSING_PHOTO_{job['id']}"
                    
                    # Kritičtější pro dokončené zakázky
                    is_completed = job['status'] in ('Dokončeno', 'completed')
                    
                    self._create_or_update_insight(
                        key=key,
                        insight_type='MISSING_PHOTO_DOC',
                        severity='WARN' if is_completed else 'INFO',
                        title=f"📷 Chybí foto: {job['client'] or job['name']}",
                        summary=f"Zakázka typu '{job['type'] or 'standard'}' nemá žádnou foto dokumentaci" + 
                                (" (dokončeno!)" if is_completed else ""),
                        evidence={
                            'job_id': job['id'],
                            'job_type': job['type'],
                            'status': job['status'],
                            'photo_count': photo_count,
                            'requires_photo': True
                        },
                        actions=[
                            {'type': 'REQUEST_PHOTO', 'label': 'Vyžádat foto', 'payload': {'job_id': job['id']}},
                            {'type': 'link', 'label': 'Otevřít zakázku', 'url': f"/job-detail.html?id={job['id']}"}
                        ],
                        entity_type='job',
                        entity_id=job['id']
                    )
        except Exception as e:
            print(f"R12 error: {e}")
    
    def _rule_completed_not_invoiced(self):
        """R13: Dokončená zakázka bez faktury"""
        try:
            jobs = self.db.execute('''
                SELECT id, client, name, completed_at, actual_end_date
                FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND (completed_at IS NOT NULL OR actual_end_date IS NOT NULL)
            ''').fetchall()
            
            # Check if invoice exists (simplified - would need invoices table)
            for job in jobs:
                # For now, create insight for all completed jobs as reminder
                key = f"R13_NOT_INVOICED_{job['id']}"
                
                self._create_or_update_insight(
                    key=key,
                    insight_type='COMPLETED_NOT_INVOICED',
                    severity='WARN',
                    title=f"💵 K fakturaci: {job['client'] or job['name']}",
                    summary=f"Zakázka dokončena, zkontrolujte fakturaci",
                    evidence={
                        'job_id': job['id'],
                        'completed_at': job['completed_at'] or job['actual_end_date']
                    },
                    actions=[
                        {'type': 'CREATE_INVOICE', 'label': 'Vytvořit fakturu', 'payload': {'job_id': job['id']}},
                        {'type': 'MARK_INVOICED', 'label': 'Už fakturováno', 'payload': {'job_id': job['id']}}
                    ],
                    entity_type='job',
                    entity_id=job['id']
                )
        except Exception as e:
            print(f"R13 error: {e}")
    
    def _rule_weather_risk_outdoor(self, today):
        """R14: Riziko počasí pro venkovní práce"""
        try:
            # Simulace předpovědi - v produkci by se volalo weather API
            forecast = self._get_weather_forecast(today)
            
            # Najdi zakázky s venkovní prací
            jobs = self.db.execute('''
                SELECT id, client, name, start_date, weather_dependent, type
                FROM jobs
                WHERE status IN ('active', 'Aktivní', 'pending', 'rozpracováno')
                AND (weather_dependent = 1 OR type IN ('landscaping', 'garden', 'outdoor'))
            ''').fetchall()
            
            for day in forecast[:5]:
                if day.get('rain_chance', 0) > 60 or day.get('temp', 15) < 0:
                    for job in jobs:
                        job_date = job['start_date']
                        if job_date and job_date == day['date']:
                            key = f"R14_WEATHER_RISK_{job['id']}_{day['date']}"
                            
                            weather_issue = 'déšť' if day.get('rain_chance', 0) > 60 else 'mráz'
                            
                            self._create_or_update_insight(
                                key=key,
                                insight_type='WEATHER_RISK_OUTDOOR',
                                severity='WARN',
                                title=f"🌧️ Počasí ohrožuje: {job['client'] or job['name']}",
                                summary=f"Hlášen {weather_issue} na {day['date']}",
                                evidence={
                                    'job_id': job['id'],
                                    'date': day['date'],
                                    'rain_chance': day.get('rain_chance'),
                                    'temp': day.get('temp')
                                },
                                actions=[
                                    {'type': 'MOVE_JOB', 'label': 'Přesunout', 'payload': {'job_id': job['id'], 'reason': 'WEATHER'}},
                                    {'type': 'link', 'label': 'Detail', 'url': f"/job-detail.html?id={job['id']}"}
                                ],
                                entity_type='job',
                                entity_id=job['id']
                            )
        except Exception as e:
            print(f"R14 error: {e}")
    
    def _rule_inventory_variance(self):
        """R15: Odchylka spotřeby materiálu od plánovaného"""
        try:
            # Porovnej plánovanou vs skutečnou spotřebu materiálu na zakázkách
            # Hledáme zakázky kde skutečná spotřeba se významně liší od plánované
            
            jobs_with_variance = self.db.execute('''
                SELECT 
                    j.id, j.client, j.name,
                    COALESCE(SUM(jr.quantity), 0) as planned_qty,
                    COALESCE(SUM(CASE WHEN wm.movement_type = 'issue' THEN wm.quantity ELSE 0 END), 0) as actual_qty
                FROM jobs j
                LEFT JOIN job_reservations jr ON jr.job_id = j.id
                LEFT JOIN warehouse_movements wm ON wm.job_id = j.id AND wm.movement_type = 'issue'
                WHERE j.status IN ('active', 'Aktivní', 'rozpracováno', 'Dokončeno', 'completed')
                GROUP BY j.id
                HAVING planned_qty > 0 AND ABS(actual_qty - planned_qty) / planned_qty > 0.2
            ''').fetchall()
            
            for job in jobs_with_variance:
                planned = job['planned_qty'] or 0
                actual = job['actual_qty'] or 0
                
                if planned > 0:
                    variance_pct = ((actual - planned) / planned) * 100
                    
                    # Ignoruj malé odchylky
                    if abs(variance_pct) < 20:
                        continue
                    
                    key = f"R15_INVENTORY_VARIANCE_{job['id']}"
                    
                    over_under = 'přečerpáno' if actual > planned else 'nedočerpáno'
                    
                    self._create_or_update_insight(
                        key=key,
                        insight_type='INVENTORY_VARIANCE',
                        severity='INFO' if abs(variance_pct) < 50 else 'WARN',
                        title=f"📊 Odchylka spotřeby: {job['client'] or job['name']}",
                        summary=f"Materiál {over_under} o {abs(variance_pct):.0f}% (plán: {planned:.0f}, skutečnost: {actual:.0f})",
                        evidence={
                            'job_id': job['id'],
                            'planned_qty': planned,
                            'actual_qty': actual,
                            'variance_pct': round(variance_pct, 1),
                            'over_under': over_under
                        },
                        actions=[
                            {'type': 'REVIEW_CONSUMPTION', 'label': 'Zkontrolovat spotřebu', 'payload': {'job_id': job['id']}},
                            {'type': 'UPDATE_TEMPLATES', 'label': 'Upravit šablony', 'payload': {'job_id': job['id']}},
                            {'type': 'link', 'label': 'Detail', 'url': f"/job-detail.html?id={job['id']}"}
                        ],
                        entity_type='job',
                        entity_id=job['id']
                    )
        except Exception as e:
            print(f"R15 error: {e}")
    
    def _get_weather_forecast(self, today):
        """Simulace předpovědi počasí"""
        import random
        forecast = []
        for i in range(7):
            date = today + timedelta(days=i)
            forecast.append({
                'date': date.isoformat(),
                'temp': random.randint(0, 15),
                'rain_chance': random.randint(0, 100),
                'condition': random.choice(['sunny', 'cloudy', 'rain', 'snow'])
            })
        return forecast


# =============================================================================
# INSIGHT MANAGEMENT API
# =============================================================================

def get_insights(status=None, severity=None, insight_type=None, limit=50, apply_rbac=True):
    """Získej seznam insightů s filtry a RBAC"""
    db = get_db_with_row_factory()
    
    query = 'SELECT * FROM insight WHERE 1=1'
    params = []
    
    if status:
        query += ' AND status = ?'
        params.append(status)
    else:
        query += ' AND status NOT IN ("resolved", "dismissed")'
    
    if severity:
        query += ' AND severity = ?'
        params.append(severity)
    
    if insight_type:
        query += ' AND type = ?'
        params.append(insight_type)
    
    # Řazení: CRITICAL first, then by date
    query += ' ORDER BY CASE severity WHEN "CRITICAL" THEN 0 WHEN "WARN" THEN 1 ELSE 2 END, created_at DESC'
    query += f' LIMIT {limit * 2}'  # Načti více kvůli filtrování
    
    insights = db.execute(query, params).fetchall()
    insights_list = [dict(i) for i in insights]
    
    # Aplikuj RBAC filtrování
    if apply_rbac:
        try:
            from ai_operator_notifications import filter_insights_for_user
            insights_list = filter_insights_for_user(insights_list)
        except ImportError:
            pass  # Fallback pokud modul není k dispozici
    
    return insights_list[:limit]


def get_insight_detail(insight_id, apply_rbac=True):
    """Získej detail insightu včetně evidence a akcí s RBAC"""
    db = get_db_with_row_factory()
    
    insight = db.execute('SELECT * FROM insight WHERE id = ?', (insight_id,)).fetchone()
    
    if not insight:
        return None
    
    result = dict(insight)
    result['evidence'] = json.loads(result['evidence_json']) if result['evidence_json'] else {}
    result['actions'] = json.loads(result['actions_json']) if result['actions_json'] else []
    
    # Aplikuj RBAC filtrování
    if apply_rbac:
        try:
            from ai_operator_notifications import filter_insight_for_role, get_current_user_role
            role, user_id = get_current_user_role()
            if role:
                result = filter_insight_for_role(result, role, user_id)
                if result is None:
                    return None  # Nemá přístup
        except ImportError:
            pass
    
    # Přidej související action drafty
    drafts = db.execute(
        'SELECT * FROM action_draft WHERE insight_id = ? ORDER BY created_at DESC',
        (insight_id,)
    ).fetchall()
    result['action_drafts'] = [dict(d) for d in drafts]
    
    return result


def snooze_insight(insight_id, until_date):
    """Odlož insight"""
    db = get_db_with_row_factory()
    
    db.execute('''
        UPDATE insight SET status = 'snoozed', snoozed_until = ?, updated_at = datetime('now')
        WHERE id = ?
    ''', (until_date, insight_id))
    db.commit()
    
    return True


def dismiss_insight(insight_id, reason_code, user_id=None):
    """Zamítni insight s důvodem"""
    db = get_db_with_row_factory()
    
    db.execute('''
        UPDATE insight SET 
            status = 'dismissed', 
            dismissed_reason = ?,
            dismissed_by = ?,
            updated_at = datetime('now')
        WHERE id = ?
    ''', (reason_code, user_id, insight_id))
    db.commit()
    
    return True


def resolve_insight(insight_id):
    """Označ insight jako vyřešený"""
    db = get_db_with_row_factory()
    
    db.execute('''
        UPDATE insight SET 
            status = 'resolved', 
            resolved_at = datetime('now'),
            updated_at = datetime('now')
        WHERE id = ?
    ''', (insight_id,))
    db.commit()
    
    return True


# =============================================================================
# ACTION DRAFT MANAGEMENT
# =============================================================================

def create_action_draft(insight_id, action_type, title, payload, user_id=None):
    """Vytvoř návrh akce"""
    db = get_db_with_row_factory()
    
    cursor = db.execute('''
        INSERT INTO action_draft (insight_id, created_by, action_type, title, payload_json, status)
        VALUES (?, ?, ?, ?, ?, 'proposed')
    ''', (insight_id, user_id, action_type, title, json.dumps(payload)))
    db.commit()
    
    return cursor.lastrowid


def get_action_drafts(status=None, limit=50):
    """Získej seznam návrhů akcí"""
    db = get_db_with_row_factory()
    
    query = 'SELECT * FROM action_draft'
    params = []
    
    if status:
        query += ' WHERE status = ?'
        params.append(status)
    
    query += ' ORDER BY created_at DESC'
    query += f' LIMIT {limit}'
    
    drafts = db.execute(query, params).fetchall()
    
    result = []
    for d in drafts:
        draft = dict(d)
        draft['payload'] = json.loads(draft['payload_json']) if draft['payload_json'] else {}
        result.append(draft)
    
    return result


def approve_action_draft(draft_id, user_id=None):
    """Schval návrh akce"""
    db = get_db_with_row_factory()
    
    db.execute('''
        UPDATE action_draft SET 
            status = 'approved',
            approved_by = ?,
            approved_at = datetime('now')
        WHERE id = ?
    ''', (user_id, draft_id))
    db.commit()
    
    return True


def reject_action_draft(draft_id, reason, user_id=None):
    """Zamítni návrh akce"""
    db = get_db_with_row_factory()
    
    db.execute('''
        UPDATE action_draft SET 
            status = 'rejected',
            rejected_by = ?,
            rejected_at = datetime('now'),
            rejection_reason = ?
        WHERE id = ?
    ''', (user_id, reason, draft_id))
    db.commit()
    
    return True


def execute_action_draft(draft_id):
    """Proveď schválenou akci"""
    db = get_db_with_row_factory()
    
    draft = db.execute('SELECT * FROM action_draft WHERE id = ?', (draft_id,)).fetchone()
    
    if not draft or draft['status'] != 'approved':
        return {'success': False, 'error': 'Draft not approved'}
    
    payload = json.loads(draft['payload_json']) if draft['payload_json'] else {}
    result = {'success': False}
    
    try:
        # Proveď akci podle typu
        action_type = draft['action_type']
        
        if action_type == 'MOVE_JOB':
            result = _execute_move_job(db, payload)
        elif action_type == 'REASSIGN_EMPLOYEES':
            result = _execute_reassign_employees(db, payload)
        elif action_type == 'CREATE_TASKS_FROM_TEMPLATE':
            result = _execute_create_tasks_from_template(db, payload)
        elif action_type == 'GENERATE_PURCHASE_LIST':
            result = _execute_generate_purchase_list(db, payload)
        elif action_type == 'RESERVE_INVENTORY':
            result = _execute_reserve_inventory(db, payload)
        elif action_type == 'REQUEST_TIMESHEET_APPROVAL':
            result = _execute_request_timesheet_approval(db, payload)
        elif action_type == 'CREATE_CLIENT_UPDATE':
            result = _execute_create_client_update(db, payload)
        elif action_type == 'ESCALATE_BUDGET_OVERRUN':
            result = _execute_escalate_budget_overrun(db, payload)
        elif action_type == 'CREATE_MAINTENANCE_OFFER':
            result = _execute_create_maintenance_offer(db, payload)
        else:
            result = {'success': True, 'message': f'Akce {action_type} potvrzena'}
        
        # Aktualizuj draft
        db.execute('''
            UPDATE action_draft SET 
                status = 'executed',
                executed_at = datetime('now'),
                execution_result_json = ?
            WHERE id = ?
        ''', (json.dumps(result), draft_id))
        
        # Pokud má insight, označ jako resolved
        if draft['insight_id']:
            resolve_insight(draft['insight_id'])
        
        db.commit()
        
    except Exception as e:
        result = {'success': False, 'error': str(e)}
        db.execute('''
            UPDATE action_draft SET 
                status = 'failed',
                execution_result_json = ?
            WHERE id = ?
        ''', (json.dumps(result), draft_id))
        db.commit()
    
    return result


def _execute_move_job(db, payload):
    """A1: Proveď přesun zakázky v kalendáři"""
    job_id = payload.get('job_id')
    new_date = payload.get('to') or payload.get('new_date')
    notify_team = payload.get('notify_team', False)
    reason = payload.get('reason', '')
    
    if job_id and new_date:
        # Načti původní datum
        old_job = db.execute('SELECT start_date, client, name FROM jobs WHERE id = ?', (job_id,)).fetchone()
        old_date = old_job['start_date'] if old_job else None
        
        # Aktualizuj datum
        db.execute('UPDATE jobs SET start_date = ?, updated_at = datetime("now") WHERE id = ?', (new_date, job_id))
        
        # Zaloguj událost
        from ai_operator_migrations import log_event
        log_event(db, 'job', job_id, 'JOB_MOVED', {
            'from': old_date,
            'to': new_date,
            'reason': reason,
            'notify_team': notify_team
        })
        
        return {
            'success': True, 
            'message': f'Zakázka přesunuta z {old_date} na {new_date}',
            'job_id': job_id,
            'old_date': old_date,
            'new_date': new_date
        }
    
    return {'success': False, 'error': 'Chybí job_id nebo new_date'}


def _execute_reassign_employees(db, payload):
    """A2: Proveď přeřazení zaměstnanců na zakázku/úkol"""
    job_id = payload.get('job_id')
    task_id = payload.get('task_id')
    add_employee_ids = payload.get('add_employee_ids', [])
    remove_employee_ids = payload.get('remove_employee_ids', [])
    effective_from = payload.get('effective_from')
    
    changes = []
    
    if job_id:
        # Přidej zaměstnance na zakázku
        for emp_id in add_employee_ids:
            try:
                db.execute('''
                    INSERT OR IGNORE INTO job_employees (job_id, employee_id, assigned_at)
                    VALUES (?, ?, datetime('now'))
                ''', (job_id, emp_id))
                changes.append(f'Přidán zaměstnanec {emp_id}')
            except:
                pass
        
        # Odeber zaměstnance ze zakázky
        for emp_id in remove_employee_ids:
            db.execute('DELETE FROM job_employees WHERE job_id = ? AND employee_id = ?', (job_id, emp_id))
            changes.append(f'Odebrán zaměstnanec {emp_id}')
    
    if task_id:
        # Přeřaď úkol
        if add_employee_ids:
            db.execute('UPDATE tasks SET employee_id = ? WHERE id = ?', (add_employee_ids[0], task_id))
            changes.append(f'Úkol {task_id} přiřazen zaměstnanci {add_employee_ids[0]}')
    
    db.commit()
    
    return {
        'success': True,
        'message': 'Zaměstnanci přeřazeni',
        'changes': changes
    }


def _execute_create_tasks_from_template(db, payload):
    """A3: Vygeneruj úkoly podle šablony"""
    job_id = payload.get('job_id')
    template_id = payload.get('template_id')
    
    if not job_id:
        return {'success': False, 'error': 'Chybí job_id'}
    
    # Pokud není template, vytvoř základní úkoly
    tasks_created = []
    default_tasks = [
        ('Příprava materiálu', 'Zajistit a připravit potřebný materiál'),
        ('Realizace', 'Provedení hlavní práce'),
        ('Úklid a kontrola', 'Závěrečný úklid a kontrola kvality'),
        ('Foto dokumentace', 'Pořídit fotky hotového díla')
    ]
    
    for title, description in default_tasks:
        cursor = db.execute('''
            INSERT INTO tasks (job_id, title, description, status, created_at)
            VALUES (?, ?, ?, 'pending', datetime('now'))
        ''', (job_id, title, description))
        tasks_created.append({'id': cursor.lastrowid, 'title': title})
    
    db.commit()
    
    return {
        'success': True,
        'message': f'Vytvořeno {len(tasks_created)} úkolů',
        'tasks': tasks_created
    }


def _execute_generate_purchase_list(db, payload):
    """A4: Sestav nákupní seznam z rezervací a min. stavů"""
    scope = payload.get('scope', 'missing_and_below_min')
    group_by = payload.get('group_by', 'supplier')
    include_job_reservations = payload.get('include_job_reservations', True)
    date_needed = payload.get('date_needed')
    
    items_to_order = []
    
    # Položky pod minimem
    if 'below_min' in scope or scope == 'missing_and_below_min':
        below_min = db.execute('''
            SELECT id, name, qty, minStock, unit, supplier
            FROM warehouse_items
            WHERE status = 'active' AND qty < minStock AND minStock > 0
        ''').fetchall()
        
        for item in below_min:
            items_to_order.append({
                'item_id': item['id'],
                'name': item['name'],
                'current_qty': item['qty'],
                'min_qty': item['minStock'],
                'order_qty': item['minStock'] - item['qty'],
                'unit': item['unit'],
                'supplier': item['supplier'],
                'reason': 'pod_minimem'
            })
    
    # Položky z rezervací
    if include_job_reservations:
        shortages = db.execute('''
            SELECT wi.id, wi.name, wi.qty, wi.unit, wi.supplier,
                   SUM(jr.quantity) as reserved
            FROM warehouse_items wi
            JOIN job_reservations jr ON jr.item_id = wi.id
            WHERE jr.status = 'active'
            GROUP BY wi.id
            HAVING reserved > wi.qty
        ''').fetchall()
        
        for item in shortages:
            shortage = item['reserved'] - item['qty']
            items_to_order.append({
                'item_id': item['id'],
                'name': item['name'],
                'current_qty': item['qty'],
                'reserved_qty': item['reserved'],
                'order_qty': shortage,
                'unit': item['unit'],
                'supplier': item['supplier'],
                'reason': 'rezervace'
            })
    
    return {
        'success': True,
        'message': f'Nákupní seznam: {len(items_to_order)} položek',
        'items': items_to_order,
        'date_needed': date_needed
    }


def _execute_reserve_inventory(db, payload):
    """A5: Vytvoř/aktualizuj rezervace materiálu"""
    job_id = payload.get('job_id')
    items = payload.get('items', [])  # [{item_id, quantity}]
    
    if not job_id:
        return {'success': False, 'error': 'Chybí job_id'}
    
    reserved = []
    for item in items:
        item_id = item.get('item_id')
        quantity = item.get('quantity', 0)
        
        if item_id and quantity > 0:
            # Zkontroluj dostupnost
            stock = db.execute('SELECT qty FROM warehouse_items WHERE id = ?', (item_id,)).fetchone()
            
            db.execute('''
                INSERT INTO job_reservations (job_id, item_id, quantity, status, created_at)
                VALUES (?, ?, ?, 'active', datetime('now'))
                ON CONFLICT(job_id, item_id) DO UPDATE SET quantity = quantity + excluded.quantity
            ''', (job_id, item_id, quantity))
            
            reserved.append({'item_id': item_id, 'quantity': quantity})
    
    db.commit()
    
    return {
        'success': True,
        'message': f'Rezervováno {len(reserved)} položek',
        'reservations': reserved
    }


def _execute_request_timesheet_approval(db, payload):
    """A6: Vyžádej schválení výkazů"""
    period_start = payload.get('period_start')
    period_end = payload.get('period_end')
    approver_ids = payload.get('approver_ids', [])
    remind_after_hours = payload.get('remind_after_hours', 24)
    
    # Najdi neschválené výkazy v období
    pending = db.execute('''
        SELECT t.id, t.employee_id, e.name as employee_name, t.date, t.hours
        FROM timesheets t
        JOIN employees e ON e.id = t.employee_id
        WHERE t.date BETWEEN ? AND ?
        AND (t.approved IS NULL OR t.approved = 0)
    ''', (period_start, period_end)).fetchall()
    
    # Vytvoř notifikace pro schvalovatele
    for approver_id in approver_ids:
        db.execute('''
            INSERT INTO notifications (user_id, type, title, message, entity_type, entity_id, created_at)
            VALUES (?, 'timesheet_approval', 'Ke schválení výkazy', ?, 'timesheet', NULL, datetime('now'))
        ''', (approver_id, f'{len(pending)} výkazů čeká na schválení ({period_start} - {period_end})'))
    
    db.commit()
    
    return {
        'success': True,
        'message': f'Požadavek na schválení odeslán ({len(pending)} výkazů)',
        'pending_count': len(pending),
        'approvers': approver_ids
    }


def _execute_create_client_update(db, payload):
    """A7: Připrav zprávu pro klienta"""
    job_id = payload.get('job_id')
    include_photos = payload.get('include_photos', True)
    
    if not job_id:
        return {'success': False, 'error': 'Chybí job_id'}
    
    # Načti data zakázky
    job = db.execute('''
        SELECT j.*, c.name as client_name, c.email as client_email
        FROM jobs j
        LEFT JOIN clients c ON c.id = j.client_id
        WHERE j.id = ?
    ''', (job_id,)).fetchone()
    
    if not job:
        return {'success': False, 'error': 'Zakázka nenalezena'}
    
    # Připrav návrh zprávy
    message_draft = f"""
Dobrý den,

rádi bychom Vás informovali o průběhu zakázky "{job['name'] or job['client']}".

Stav: {job['status']}
Progress: {job['progress'] or job['completion_percent'] or 0}%

S pozdravem,
Green David s.r.o.
"""
    
    return {
        'success': True,
        'message': 'Návrh zprávy připraven',
        'draft': message_draft.strip(),
        'client_email': job['client_email'] if job else None,
        'job_id': job_id
    }


def _execute_escalate_budget_overrun(db, payload):
    """A8: Eskaluj překročení rozpočtu"""
    job_id = payload.get('job_id')
    
    if not job_id:
        return {'success': False, 'error': 'Chybí job_id'}
    
    # Načti data
    job = db.execute('''
        SELECT id, client, name, budget_labor, actual_labor_cost, budget_materials, actual_material_cost
        FROM jobs WHERE id = ?
    ''', (job_id,)).fetchone()
    
    if not job:
        return {'success': False, 'error': 'Zakázka nenalezena'}
    
    # Vytvoř incident/issue
    cursor = db.execute('''
        INSERT INTO issues (job_id, title, description, severity, status, created_at)
        VALUES (?, ?, ?, 'high', 'open', datetime('now'))
    ''', (
        job_id,
        f'Překročení rozpočtu: {job["client"] or job["name"]}',
        f'Rozpočet práce: {job["budget_labor"]}, Skutečnost: {job["actual_labor_cost"]}\n'
        f'Rozpočet materiál: {job["budget_materials"]}, Skutečnost: {job["actual_material_cost"]}'
    ))
    
    db.commit()
    
    return {
        'success': True,
        'message': 'Eskalace vytvořena',
        'issue_id': cursor.lastrowid,
        'job_id': job_id
    }


def _execute_create_maintenance_offer(db, payload):
    """A10: Návrh údržbové smlouvy po dokončení"""
    job_id = payload.get('job_id')
    
    if not job_id:
        return {'success': False, 'error': 'Chybí job_id'}
    
    job = db.execute('SELECT client, name, type FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    if not job:
        return {'success': False, 'error': 'Zakázka nenalezena'}
    
    # Vytvoř návrh údržbové nabídky
    offer_draft = f"""
NABÍDKA ÚDRŽBY

Vážený zákazníku,

na základě dokončené zakázky "{job['name'] or job['client']}" 
Vám nabízíme pravidelnou údržbu.

Doporučený interval: měsíčně / čtvrtletně / sezónně
Rozsah: kontrola, úklid, drobné opravy

Cena od: XXX Kč/návštěvu

S pozdravem,
Green David s.r.o.
"""
    
    return {
        'success': True,
        'message': 'Návrh údržbové nabídky připraven',
        'offer_draft': offer_draft.strip(),
        'job_id': job_id
    }


# =============================================================================
# DASHBOARD & SCORE
# =============================================================================

def get_company_health_score(db=None):
    """Vypočítej skóre zdraví firmy"""
    if db is None:
        db = get_db_with_row_factory()
    
    # Počty insightů podle severity
    counts = db.execute('''
        SELECT 
            SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN severity = 'WARN' THEN 1 ELSE 0 END) as warn,
            SUM(CASE WHEN severity = 'INFO' THEN 1 ELSE 0 END) as info
        FROM insight
        WHERE status = 'open'
    ''').fetchone()
    
    critical = counts['critical'] or 0
    warn = counts['warn'] or 0
    info = counts['info'] or 0
    
    # Score: 100 - (critical * 20) - (warn * 5) - (info * 1)
    score = max(0, min(100, 100 - (critical * 20) - (warn * 5) - (info * 1)))
    
    return {
        'score': score,
        'critical_count': critical,
        'warn_count': warn,
        'info_count': info,
        'total_open': critical + warn + info
    }


def get_top_insights(limit=3):
    """Získej top N nejdůležitějších insightů pro dnešek"""
    db = get_db_with_row_factory()
    
    insights = db.execute('''
        SELECT id, type, severity, title, summary, actions_json, entity_type, entity_id
        FROM insight
        WHERE status = 'open'
        ORDER BY 
            CASE severity WHEN 'CRITICAL' THEN 0 WHEN 'WARN' THEN 1 ELSE 2 END,
            created_at DESC
        LIMIT ?
    ''', (limit,)).fetchall()
    
    result = []
    for i in insights:
        insight = dict(i)
        insight['actions'] = json.loads(insight['actions_json']) if insight['actions_json'] else []
        del insight['actions_json']
        result.append(insight)
    
    return result


# =============================================================================
# FLASK API ROUTES
# =============================================================================

def register_ai_operator_routes(app):
    """Registruj všechny API routes pro AI Operátor Rule Engine"""
    
    @app.route('/api/ai/dashboard/v2')
    @login_required
    def api_ai_dashboard_v2():
        """Hlavní AI dashboard endpoint (Rule Engine verze)"""
        db = get_db_with_row_factory()
        
        # Spusť rule engine pro aktualizaci insightů
        engine = RuleEngine(db)
        engine.run_all_rules()
        
        # Získej data pro dashboard
        health = get_company_health_score(db)
        top_insights = get_top_insights(3)
        
        # Statistiky
        open_insights = get_insights(status='open', limit=20)
        pending_drafts = get_action_drafts(status='proposed', limit=10)
        
        return jsonify({
            'score': health['score'],
            'health': health,
            'today_actions': top_insights,
            'insights': {
                'open': open_insights,
                'total': health['total_open']
            },
            'action_drafts': {
                'pending': pending_drafts,
                'total': len(pending_drafts)
            }
        })
    
    @app.route('/api/ai/insights')
    @login_required
    def api_get_insights():
        """Seznam insightů s filtry"""
        status = request.args.get('status')
        severity = request.args.get('severity')
        insight_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        
        insights = get_insights(status, severity, insight_type, limit)
        
        # Parse JSON fields
        for i in insights:
            i['evidence'] = json.loads(i['evidence_json']) if i.get('evidence_json') else {}
            i['actions'] = json.loads(i['actions_json']) if i.get('actions_json') else []
        
        return jsonify({'insights': insights, 'total': len(insights)})
    
    @app.route('/api/ai/insights/<int:insight_id>')
    @login_required
    def api_get_insight_detail(insight_id):
        """Detail insightu"""
        insight = get_insight_detail(insight_id)
        if not insight:
            return jsonify({'error': 'Insight not found'}), 404
        return jsonify(insight)
    
    @app.route('/api/ai/insights/<int:insight_id>/snooze', methods=['POST'])
    @login_required
    def api_snooze_insight(insight_id):
        """Odlož insight"""
        data = request.get_json() or {}
        until = data.get('until', (datetime.now() + timedelta(days=1)).isoformat())
        snooze_insight(insight_id, until)
        return jsonify({'success': True})
    
    @app.route('/api/ai/insights/<int:insight_id>/dismiss', methods=['POST'])
    @login_required
    def api_dismiss_insight(insight_id):
        """Zamítni insight"""
        data = request.get_json() or {}
        reason = data.get('reason_code', 'other')
        dismiss_insight(insight_id, reason)
        return jsonify({'success': True})
    
    @app.route('/api/ai/insights/<int:insight_id>/resolve', methods=['POST'])
    @login_required
    def api_resolve_insight(insight_id):
        """Vyřeš insight"""
        resolve_insight(insight_id)
        return jsonify({'success': True})
    
    @app.route('/api/ai/action-drafts', methods=['GET'])
    @login_required
    def api_get_action_drafts():
        """Seznam návrhů akcí"""
        status = request.args.get('status')
        drafts = get_action_drafts(status)
        return jsonify({'drafts': drafts, 'total': len(drafts)})
    
    @app.route('/api/ai/action-drafts', methods=['POST'])
    @login_required
    def api_create_action_draft():
        """Vytvoř návrh akce"""
        data = request.get_json()
        draft_id = create_action_draft(
            insight_id=data.get('insight_id'),
            action_type=data['action_type'],
            title=data.get('title', ''),
            payload=data.get('payload', {})
        )
        return jsonify({'success': True, 'draft_id': draft_id})
    
    @app.route('/api/ai/action-drafts/<int:draft_id>/approve', methods=['POST'])
    @login_required
    def api_approve_draft(draft_id):
        """Schval návrh"""
        approve_action_draft(draft_id)
        return jsonify({'success': True})
    
    @app.route('/api/ai/action-drafts/<int:draft_id>/reject', methods=['POST'])
    @login_required
    def api_reject_draft(draft_id):
        """Zamítni návrh"""
        data = request.get_json() or {}
        reason = data.get('reason', '')
        reject_action_draft(draft_id, reason)
        return jsonify({'success': True})
    
    @app.route('/api/ai/action-drafts/<int:draft_id>/execute', methods=['POST'])
    @login_required
    def api_execute_draft(draft_id):
        """Proveď schválenou akci"""
        result = execute_action_draft(draft_id)
        return jsonify(result)
    
    @app.route('/api/ai/rules/run', methods=['POST'])
    @login_required
    def api_run_rules():
        """Manuální spuštění rule engine"""
        db = get_db_with_row_factory()
        start_time = datetime.now()
        engine = RuleEngine(db)
        insights = engine.run_all_rules()
        end_time = datetime.now()
        
        # Zaloguj běh do event_log
        from ai_operator_migrations import log_event
        log_event(db, 'rule_engine', None, 'RULES_RUN', {
            'insights_generated': len(insights),
            'duration_ms': (end_time - start_time).total_seconds() * 1000
        })
        
        return jsonify({
            'success': True,
            'insights_generated': len(insights),
            'insights': insights,
            'duration_ms': (end_time - start_time).total_seconds() * 1000
        })
    
    @app.route('/api/ai/rules/status', methods=['GET'])
    @login_required
    def api_rules_status():
        """Stav rule engine - poslední běhy, latence, počty insightů"""
        db = get_db_with_row_factory()
        
        # Poslední běhy rule engine
        last_runs = db.execute('''
            SELECT 
                created_at,
                json_extract(payload_json, '$.insights_generated') as insights_generated,
                json_extract(payload_json, '$.duration_ms') as duration_ms
            FROM event_log
            WHERE entity_type = 'rule_engine' AND event_type = 'RULES_RUN'
            ORDER BY created_at DESC
            LIMIT 10
        ''').fetchall()
        
        # Statistiky insightů
        insight_stats = db.execute('''
            SELECT 
                type,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_count,
                SUM(CASE WHEN status = 'dismissed' THEN 1 ELSE 0 END) as dismissed_count
            FROM insight
            GROUP BY type
            ORDER BY count DESC
        ''').fetchall()
        
        # Průměrná latence posledních 10 běhů
        avg_latency = None
        if last_runs:
            latencies = [r['duration_ms'] for r in last_runs if r['duration_ms']]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
        
        return jsonify({
            'last_runs': [dict(r) for r in last_runs],
            'avg_latency_ms': avg_latency,
            'insight_stats': [dict(s) for s in insight_stats],
            'rules_count': 15,
            'rules': [
                {'id': 'R1', 'name': 'BUDGET_OVERRUN_LABOR', 'trigger': 'cron+event'},
                {'id': 'R2', 'name': 'BUDGET_OVERRUN_MATERIAL', 'trigger': 'cron+event'},
                {'id': 'R3', 'name': 'JOB_BEHIND_SCHEDULE', 'trigger': 'cron'},
                {'id': 'R4', 'name': 'TASK_OVERDUE', 'trigger': 'event'},
                {'id': 'R5', 'name': 'NO_ACTIVITY_ON_JOB', 'trigger': 'cron'},
                {'id': 'R6', 'name': 'EMPLOYEE_OVERLOAD', 'trigger': 'cron'},
                {'id': 'R7', 'name': 'EMPLOYEE_IDLE', 'trigger': 'cron'},
                {'id': 'R8', 'name': 'LOW_STOCK', 'trigger': 'event'},
                {'id': 'R9', 'name': 'RESERVATION_EXCEEDS_STOCK', 'trigger': 'event'},
                {'id': 'R10', 'name': 'MISSING_LOCATION', 'trigger': 'event'},
                {'id': 'R11', 'name': 'MISSING_ESTIMATES', 'trigger': 'cron'},
                {'id': 'R12', 'name': 'MISSING_PHOTO_DOC', 'trigger': 'cron'},
                {'id': 'R13', 'name': 'COMPLETED_NOT_INVOICED', 'trigger': 'cron'},
                {'id': 'R14', 'name': 'WEATHER_RISK_OUTDOOR', 'trigger': 'cron'},
                {'id': 'R15', 'name': 'INVENTORY_VARIANCE', 'trigger': 'cron'}
            ]
        })
    
    print("✅ AI Operátor Rule Engine routes registered")
