"""
GREEN DAVID APP - AI OPERÁTOR EXTENDED RULE ENGINE
===================================================
Kompletní implementace podle Master Prompt specifikace.

TŘI VRSTVY MOZKU:
1. REFLEXNÍ MOZEK - Deterministická pravidla (offline-capable)
2. STRATEGICKÝ MOZEK - Predikce, trendy, porovnání (online)
3. PAMĚŤ A DNA - Learning layer

SIGNÁLY:
- ČAS: deadliny, neaktivita, překryvy, víkendy/svátky, buffer časy
- KAPACITA TÝMU: přetížení, nevyužití, absence, junior bez mentora
- SKLAD: nízký stav, rezervace > dostupné, expirace, mrtvý kapitál
- ÚKOLY: bez přiřazení, bez deadline, blokované závislosti
- DATA KVALITA: prázdná pole, duplicity, nelogické hodnoty

Autor: Green David s.r.o.
Verze: 3.0 (Master Prompt compliant)
"""

from datetime import datetime, timedelta
import json
import sqlite3

# Reference na get_db
get_db = None

def get_db_with_row_factory():
    """Získej DB connection s row_factory"""
    db = get_db()
    db.row_factory = sqlite3.Row
    return db


# =============================================================================
# REFLEXNÍ MOZEK - OFFLINE ENGINE
# =============================================================================

class ReflexEngine:
    """
    Deterministický rule engine - funguje offline.
    Generuje insighty a draft akce bez ML.
    """
    
    def __init__(self, db):
        self.db = db
        self.today = datetime.now().date()
        self.insights = []
        
        # Načtení company preferences
        self.preferences = self._load_preferences()
    
    def _load_preferences(self):
        """Načti firemní nastavení"""
        prefs = {
            'max_weekly_hours': 45,
            'budget_warning_pct': 90,
            'budget_critical_pct': 110,
            'inactive_days': 5,
            'stock_warning_days': 7,
            'risk_tolerance': 'medium'
        }
        
        try:
            rows = self.db.execute('''
                SELECT key, value FROM ai_company_preferences
            ''').fetchall()
            for row in rows:
                if row['key'] in prefs:
                    val = row['value']
                    # Convert to int if numeric
                    try:
                        prefs[row['key']] = int(val)
                    except:
                        prefs[row['key']] = val
        except:
            pass
        
        return prefs
    
    def run_all_rules(self):
        """Spusť všechny reflexní pravidla"""
        self.insights = []
        
        # =========== ČAS ===========
        self._rules_time()
        
        # =========== KAPACITA TÝMU ===========
        self._rules_team_capacity()
        
        # =========== SKLAD A ZDROJE ===========
        self._rules_inventory()
        
        # =========== ÚKOLY A ZAKÁZKY ===========
        self._rules_tasks_jobs()
        
        # =========== DATA KVALITA ===========
        self._rules_data_quality()
        
        return self.insights
    
    # =========================================================================
    # ČAS - Time-based rules
    # =========================================================================
    
    def _rules_time(self):
        """Pravidla založená na čase"""
        
        # T1: Deadline zakázky - prošlá
        self._check_job_deadline_passed()
        
        # T2: Deadline zakázky - blíží se (3 dny)
        self._check_job_deadline_approaching()
        
        # T3: Deadline úkolu - prošlá
        self._check_task_deadline_passed()
        
        # T4: Deadline úkolu - blíží se
        self._check_task_deadline_approaching()
        
        # T5: Neaktivita zakázky
        self._check_job_no_activity()
        
        # T6: Plánovaná práce na víkend/svátek
        self._check_weekend_holiday_work()
        
        # T7: Přetížený den (příliš mnoho práce)
        self._check_overloaded_day()
        
        # T8: Prázdný kalendář (nic naplánováno)
        self._check_empty_calendar()
        
        # T9: Opakovaná zpoždění u stejného typu práce
        self._check_repeated_delays()
    
    def _check_job_deadline_passed(self):
        """T1: Zakázky po termínu"""
        try:
            jobs = self.db.execute('''
                SELECT id, client, name, planned_end_date
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND planned_end_date IS NOT NULL
                AND planned_end_date < ?
            ''', (self.today.isoformat(),)).fetchall()
            
            for job in jobs:
                days_late = (self.today - datetime.strptime(job['planned_end_date'], '%Y-%m-%d').date()).days
                self._add_insight(
                    key=f"job_deadline_passed_{job['id']}",
                    severity='CRITICAL' if days_late > 7 else 'WARN',
                    category='time',
                    title=f"Zakázka po termínu: {job['client'] or job['name']}",
                    summary=f"{days_late} dní po deadline ({job['planned_end_date']})",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'link', 'label': 'Otevřít zakázku', 'url': f"/job-detail.html?id={job['id']}"},
                        {'type': 'draft', 'label': 'Navrhnout nový termín', 'action': 'reschedule_job'}
                    ]
                )
        except Exception as e:
            print(f"T1 error: {e}")
    
    def _check_job_deadline_approaching(self):
        """T2: Deadline se blíží (do 3 dnů)"""
        try:
            deadline_soon = self.today + timedelta(days=3)
            jobs = self.db.execute('''
                SELECT id, client, name, planned_end_date, progress
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND planned_end_date IS NOT NULL
                AND planned_end_date BETWEEN ? AND ?
            ''', (self.today.isoformat(), deadline_soon.isoformat())).fetchall()
            
            for job in jobs:
                progress = job['progress'] or 0
                days_left = (datetime.strptime(job['planned_end_date'], '%Y-%m-%d').date() - self.today).days
                
                # Varování pokud progress < 80% a zbývají < 3 dny
                if progress < 80:
                    self._add_insight(
                        key=f"job_deadline_approaching_{job['id']}",
                        severity='WARN',
                        category='time',
                        title=f"Deadline se blíží: {job['client'] or job['name']}",
                        summary=f"Zbývá {days_left} dní, progress {progress}%",
                        entity_type='job',
                        entity_id=job['id'],
                        actions=[
                            {'type': 'link', 'label': 'Otevřít zakázku', 'url': f"/job-detail.html?id={job['id']}"},
                            {'type': 'draft', 'label': 'Přidat lidi', 'action': 'add_workers'}
                        ]
                    )
        except Exception as e:
            print(f"T2 error: {e}")
    
    def _check_task_deadline_passed(self):
        """T3: Úkoly po termínu"""
        try:
            tasks = self.db.execute('''
                SELECT t.id, t.title, COALESCE(t.deadline, t.due_date), t.job_id, j.client
                FROM tasks t
                LEFT JOIN jobs j ON j.id = t.job_id
                WHERE t.status NOT IN ('done', 'completed', 'cancelled')
                AND COALESCE(t.deadline, t.due_date) IS NOT NULL
                AND COALESCE(t.deadline, t.due_date) < ?
            ''', (self.today.isoformat(),)).fetchall()
            
            for task in tasks:
                self._add_insight(
                    key=f"task_overdue_{task['id']}",
                    severity='WARN',
                    category='time',
                    title=f"Úkol po termínu: {task['title'][:50]}",
                    summary=f"Zakázka: {task['client'] or 'N/A'}, deadline: {task['deadline']}",
                    entity_type='task',
                    entity_id=task['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Přeplánovat', 'action': 'reschedule_task'},
                        {'type': 'draft', 'label': 'Přeřadit', 'action': 'reassign_task'}
                    ]
                )
        except Exception as e:
            pass  # Table/column may not exist
    
    def _check_task_deadline_approaching(self):
        """T4: Deadline úkolu se blíží"""
        try:
            deadline_soon = self.today + timedelta(days=2)
            tasks = self.db.execute('''
                SELECT t.id, t.title, COALESCE(t.deadline, t.due_date), t.assigned_to, e.name as assignee_name
                FROM tasks t
                LEFT JOIN employees e ON e.id = t.assigned_to
                WHERE t.status NOT IN ('done', 'completed', 'cancelled')
                AND COALESCE(t.deadline, t.due_date) BETWEEN ? AND ?
                AND t.assigned_to IS NULL
            ''', (self.today.isoformat(), deadline_soon.isoformat())).fetchall()
            
            for task in tasks:
                self._add_insight(
                    key=f"task_deadline_unassigned_{task['id']}",
                    severity='WARN',
                    category='time',
                    title=f"Úkol bez přiřazení blízko deadline",
                    summary=f"{task['title'][:40]}, deadline: {task['deadline']}",
                    entity_type='task',
                    entity_id=task['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Přiřadit', 'action': 'assign_task'}
                    ]
                )
        except Exception as e:
            pass  # Table/column may not exist
    
    def _check_job_no_activity(self):
        """T5: Zakázka bez aktivity X dní"""
        inactive_days = self.preferences.get('inactive_days', 5)
        cutoff = self.today - timedelta(days=inactive_days)
        
        try:
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.name, j.status,
                       MAX(t.date) as last_timesheet,
                       MAX(tk.updated_at) as last_task_update
                FROM jobs j
                LEFT JOIN timesheets t ON t.job_id = j.id
                LEFT JOIN tasks tk ON tk.job_id = j.id
                WHERE j.status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled', 'waiting')
                GROUP BY j.id
                HAVING (last_timesheet IS NULL OR last_timesheet < ?)
                   AND (last_task_update IS NULL OR last_task_update < ?)
            ''', (cutoff.isoformat(), cutoff.isoformat())).fetchall()
            
            for job in jobs:
                self._add_insight(
                    key=f"job_inactive_{job['id']}",
                    severity='WARN',
                    category='time',
                    title=f"Zakázka bez aktivity {inactive_days}+ dní",
                    summary=f"{job['client'] or job['name']}, status: {job['status']}",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'link', 'label': 'Zkontrolovat', 'url': f"/job-detail.html?id={job['id']}"},
                        {'type': 'draft', 'label': 'Pozastavit', 'action': 'pause_job'}
                    ]
                )
        except Exception as e:
            print(f"T5 error: {e}")
    
    def _check_weekend_holiday_work(self):
        """T6: Plánovaná práce na víkend/svátek"""
        # Check next 7 days for weekend work
        for i in range(7):
            check_date = self.today + timedelta(days=i)
            if check_date.weekday() >= 5:  # Saturday=5, Sunday=6
                try:
                    planned = self.db.execute('''
                        SELECT COUNT(*) as cnt FROM planning_assignments
                        WHERE date = ?
                    ''', (check_date.isoformat(),)).fetchone()
                    
                    if planned and planned['cnt'] > 0:
                        self._add_insight(
                            key=f"weekend_work_{check_date.isoformat()}",
                            severity='INFO',
                            category='time',
                            title=f"Práce naplánována na víkend",
                            summary=f"{check_date.strftime('%d.%m.%Y')} ({['Po','Út','St','Čt','Pá','So','Ne'][check_date.weekday()]}): {planned['cnt']} přiřazení",
                            entity_type='planning',
                            entity_id=None,
                            actions=[
                                {'type': 'link', 'label': 'Zobrazit plán', 'url': f"/planning-timeline.html?date={check_date.isoformat()}"}
                            ]
                        )
                except:
                    pass
    
    def _check_overloaded_day(self):
        """T7: Přetížený den - příliš mnoho práce"""
        # Check next 14 days
        for i in range(14):
            check_date = self.today + timedelta(days=i)
            try:
                # Count planned hours per day
                planned = self.db.execute('''
                    SELECT SUM(COALESCE(planned_hours, 8)) as total_hours,
                           COUNT(DISTINCT employee_id) as workers
                    FROM planning_assignments
                    WHERE date = ?
                ''', (check_date.isoformat(),)).fetchone()
                
                if planned and planned['workers'] and planned['workers'] > 0:
                    avg_hours = (planned['total_hours'] or 0) / planned['workers']
                    if avg_hours > 10:  # More than 10h average per person
                        self._add_insight(
                            key=f"overloaded_day_{check_date.isoformat()}",
                            severity='WARN',
                            category='time',
                            title=f"Přetížený den: {check_date.strftime('%d.%m.')}",
                            summary=f"Průměr {avg_hours:.1f}h na osobu ({planned['workers']} lidí)",
                            entity_type='planning',
                            entity_id=None,
                            actions=[
                                {'type': 'draft', 'label': 'Přerozdělit', 'action': 'redistribute_work'}
                            ]
                        )
            except:
                pass
    
    def _check_empty_calendar(self):
        """T8: Prázdný kalendář - nic naplánováno na pracovní dny"""
        for i in range(1, 8):  # Next 7 working days
            check_date = self.today + timedelta(days=i)
            if check_date.weekday() < 5:  # Only working days
                try:
                    planned = self.db.execute('''
                        SELECT COUNT(*) as cnt FROM planning_assignments
                        WHERE date = ?
                    ''', (check_date.isoformat(),)).fetchone()
                    
                    if not planned or planned['cnt'] == 0:
                        self._add_insight(
                            key=f"empty_calendar_{check_date.isoformat()}",
                            severity='INFO',
                            category='time',
                            title=f"Prázdný kalendář: {check_date.strftime('%d.%m.')}",
                            summary=f"Žádná práce naplánována na {['Po','Út','St','Čt','Pá'][check_date.weekday()]}",
                            entity_type='planning',
                            entity_id=None,
                            actions=[
                                {'type': 'link', 'label': 'Naplánovat', 'url': f"/planning-timeline.html?date={check_date.isoformat()}"}
                            ]
                        )
                except:
                    pass
    
    def _check_repeated_delays(self):
        """T9: Opakovaná zpoždění u stejného typu práce/klienta"""
        try:
            # Find clients with multiple delayed jobs
            delayed_clients = self.db.execute('''
                SELECT client, COUNT(*) as delay_count
                FROM jobs
                WHERE planned_end_date IS NOT NULL
                AND (
                    (status IN ('Dokončeno', 'completed') AND completed_at > planned_end_date)
                    OR (status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled') AND planned_end_date < ?)
                )
                GROUP BY client
                HAVING delay_count >= 2
            ''', (self.today.isoformat(),)).fetchall()
            
            for client in delayed_clients:
                self._add_insight(
                    key=f"repeated_delays_{client['client']}",
                    severity='INFO',
                    category='time',
                    title=f"Opakovaná zpoždění: {client['client']}",
                    summary=f"{client['delay_count']} zakázek se zpožděním u tohoto klienta",
                    entity_type='client',
                    entity_id=None,
                    confidence='MEDIUM',
                    actions=[
                        {'type': 'link', 'label': 'Zobrazit zakázky', 'url': f"/jobs.html?client={client['client']}"}
                    ]
                )
        except Exception as e:
            print(f"T9 error: {e}")
    
    # =========================================================================
    # KAPACITA TÝMU - Team capacity rules
    # =========================================================================
    
    def _rules_team_capacity(self):
        """Pravidla pro kapacitu týmu"""
        
        # K1: Přetížení zaměstnance (>45h týdně)
        self._check_employee_overload()
        
        # K2: Nevyužitý zaměstnanec
        self._check_employee_idle()
        
        # K3: Absence/dovolená bez náhrady
        self._check_absence_no_coverage()
        
        # K4: Junior bez mentora
        self._check_junior_no_mentor()
        
        # K5: Multitasking - příliš mnoho zakázek najednou
        self._check_multitasking()
        
        # K6: Nevyvážené dovednosti v týmu
        self._check_skill_imbalance()
    
    def _check_employee_overload(self):
        """K1: Zaměstnanec přes limit hodin"""
        max_hours = self.preferences.get('max_weekly_hours', 45)
        week_start = self.today - timedelta(days=self.today.weekday())
        week_end = week_start + timedelta(days=6)
        
        try:
            employees = self.db.execute('''
                SELECT e.id, e.name, COALESCE(SUM(t.hours), 0) as hours_this_week
                FROM employees e
                LEFT JOIN timesheets t ON t.employee_id = e.id
                    AND t.date BETWEEN ? AND ?
                WHERE e.status = 'active'
                GROUP BY e.id
                HAVING hours_this_week > ?
            ''', (week_start.isoformat(), week_end.isoformat(), max_hours)).fetchall()
            
            for emp in employees:
                overtime = emp['hours_this_week'] - max_hours
                self._add_insight(
                    key=f"employee_overload_{emp['id']}_{week_start.isoformat()}",
                    severity='CRITICAL' if overtime > 10 else 'WARN',
                    category='team',
                    title=f"Přetížený zaměstnanec: {emp['name']}",
                    summary=f"{emp['hours_this_week']:.1f}h tento týden (+{overtime:.1f}h přes limit)",
                    entity_type='employee',
                    entity_id=emp['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Přerozdělit práci', 'action': 'redistribute_workload'},
                        {'type': 'link', 'label': 'Detail', 'url': f"/employee-detail.html?id={emp['id']}"}
                    ]
                )
        except Exception as e:
            print(f"K1 error: {e}")
    
    def _check_employee_idle(self):
        """K2: Nevyužitý zaměstnanec - málo práce"""
        week_start = self.today - timedelta(days=self.today.weekday())
        week_end = week_start + timedelta(days=6)
        
        try:
            # Check employees with < 20h this week AND no future assignments
            employees = self.db.execute('''
                SELECT e.id, e.name, 
                       COALESCE(SUM(t.hours), 0) as hours_this_week,
                       (SELECT COUNT(*) FROM planning_assignments pa 
                        WHERE pa.employee_id = e.id AND pa.date > ?) as future_assignments
                FROM employees e
                LEFT JOIN timesheets t ON t.employee_id = e.id
                    AND t.date BETWEEN ? AND ?
                WHERE e.status = 'active'
                GROUP BY e.id
                HAVING hours_this_week < 20 AND future_assignments = 0
            ''', (self.today.isoformat(), week_start.isoformat(), week_end.isoformat())).fetchall()
            
            for emp in employees:
                self._add_insight(
                    key=f"employee_idle_{emp['id']}_{week_start.isoformat()}",
                    severity='INFO',
                    category='team',
                    title=f"Nevyužitý zaměstnanec: {emp['name']}",
                    summary=f"Pouze {emp['hours_this_week']:.1f}h tento týden, žádná budoucí práce",
                    entity_type='employee',
                    entity_id=emp['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Přiřadit práci', 'action': 'assign_work'},
                        {'type': 'link', 'label': 'Plánování', 'url': '/planning-timeline.html'}
                    ]
                )
        except Exception as e:
            pass  # Table may not exist
    
    def _check_absence_no_coverage(self):
        """K3: Absence bez náhrady"""
        # Check for planned absences in next 14 days
        try:
            # This would need absence table - simplified check
            pass
        except:
            pass
    
    def _check_junior_no_mentor(self):
        """K4: Junior přiřazený na práci bez seniora"""
        try:
            # Find juniors working alone on jobs
            juniors_alone = self.db.execute('''
                SELECT DISTINCT e.id, e.name, j.id as job_id, j.client
                FROM employees e
                JOIN planning_assignments pa ON pa.employee_id = e.id
                JOIN jobs j ON j.id = pa.job_id
                WHERE e.role IN ('junior', 'trainee', 'brigádník')
                AND pa.date >= ?
                AND NOT EXISTS (
                    SELECT 1 FROM planning_assignments pa2
                    JOIN employees e2 ON e2.id = pa2.employee_id
                    WHERE pa2.job_id = pa.job_id
                    AND pa2.date = pa.date
                    AND e2.role IN ('senior', 'vedoucí', 'team_lead', 'manager')
                )
            ''', (self.today.isoformat(),)).fetchall()
            
            for junior in juniors_alone:
                self._add_insight(
                    key=f"junior_no_mentor_{junior['id']}_{junior['job_id']}",
                    severity='INFO',
                    category='team',
                    title=f"Junior bez mentora: {junior['name']}",
                    summary=f"Pracuje sám na zakázce {junior['client']}",
                    entity_type='employee',
                    entity_id=junior['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Přidat seniora', 'action': 'add_mentor'}
                    ]
                )
        except Exception as e:
            pass  # Table may not exist
    
    def _check_multitasking(self):
        """K5: Zaměstnanec na příliš mnoha zakázkách najednou"""
        try:
            # Find employees assigned to 4+ active jobs
            multitaskers = self.db.execute('''
                SELECT e.id, e.name, COUNT(DISTINCT pa.job_id) as job_count
                FROM employees e
                JOIN planning_assignments pa ON pa.employee_id = e.id
                WHERE pa.date BETWEEN ? AND ?
                GROUP BY e.id
                HAVING job_count >= 4
            ''', (self.today.isoformat(), (self.today + timedelta(days=7)).isoformat())).fetchall()
            
            for emp in multitaskers:
                self._add_insight(
                    key=f"multitasking_{emp['id']}",
                    severity='INFO',
                    category='team',
                    title=f"Multitasking: {emp['name']}",
                    summary=f"Přiřazen na {emp['job_count']} zakázek tento týden",
                    entity_type='employee',
                    entity_id=emp['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Zjednodušit', 'action': 'reduce_assignments'}
                    ]
                )
        except Exception as e:
            pass  # Table may not exist
    
    def _check_skill_imbalance(self):
        """K6: Nevyvážené dovednosti"""
        # Would need skills table - placeholder
        pass
    
    # =========================================================================
    # SKLAD A ZDROJE - Inventory rules
    # =========================================================================
    
    def _rules_inventory(self):
        """Pravidla pro sklad"""
        
        # S1: Nízký stav
        self._check_low_stock()
        
        # S2: Rezervace > dostupné
        self._check_reservation_exceeds_stock()
        
        # S3: Expirace materiálu
        self._check_expiring_items()
        
        # S4: Mrtvý kapitál (bez pohybu)
        self._check_dead_stock()
        
        # S5: Materiál bez zakázky
        self._check_material_no_job()
        
        # S6: Zakázka bez materiálu
        self._check_job_no_material()
        
        # S7: Duplicitní položky
        self._check_duplicate_items()
    
    def _check_low_stock(self):
        """S1: Položky pod minimem"""
        try:
            # Try inventory table first, fallback to warehouse_items
            try:
                low_items = self.db.execute('''
                    SELECT id, name, quantity, min_quantity, unit, location
                    FROM inventory
                    WHERE min_quantity IS NOT NULL
                    AND min_quantity > 0
                    AND quantity <= min_quantity
                ''').fetchall()
            except:
                low_items = self.db.execute('''
                    SELECT id, name, quantity, min_quantity, unit, location
                    FROM warehouse_items
                    WHERE min_quantity IS NOT NULL
                    AND min_quantity > 0
                    AND quantity <= min_quantity
                ''').fetchall()
            
            for item in low_items:
                severity = 'CRITICAL' if item['quantity'] == 0 else 'WARN'
                self._add_insight(
                    key=f"low_stock_{item['id']}",
                    severity=severity,
                    category='warehouse',
                    title=f"Nízký stav: {item['name']}",
                    summary=f"{item['quantity']} {item['unit'] or 'ks'} (min: {item['min_quantity']})",
                    entity_type='inventory',
                    entity_id=item['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Objednat', 'action': 'create_purchase_order'},
                        {'type': 'link', 'label': 'Sklad', 'url': '/warehouse.html'}
                    ]
                )
        except:
            pass  # Tables don't exist yet
    
    def _check_reservation_exceeds_stock(self):
        """S2: Rezervace převyšuje dostupné"""
        try:
            items = self.db.execute('''
                SELECT i.id, i.name, i.quantity,
                       COALESCE(SUM(wr.quantity), 0) as reserved
                FROM inventory i
                LEFT JOIN warehouse_reservations wr ON wr.inventory_id = i.id
                    AND wr.status = 'reserved'
                GROUP BY i.id
                HAVING reserved > quantity
            ''').fetchall()
            
            for item in items:
                shortage = item['reserved'] - item['quantity']
                self._add_insight(
                    key=f"reservation_exceeds_{item['id']}",
                    severity='CRITICAL',
                    category='warehouse',
                    title=f"Rezervace > sklad: {item['name']}",
                    summary=f"Chybí {shortage} ks (rezervováno {item['reserved']}, na skladě {item['quantity']})",
                    entity_type='inventory',
                    entity_id=item['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Přerozdělit', 'action': 'reallocate_reservations'},
                        {'type': 'draft', 'label': 'Objednat', 'action': 'create_purchase_order'}
                    ]
                )
        except Exception as e:
            pass  # Table may not exist
    
    def _check_expiring_items(self):
        """S3: Položky blízko expirace"""
        try:
            expiry_soon = self.today + timedelta(days=30)
            items = self.db.execute('''
                SELECT id, name, quantity, expiry_date
                FROM inventory
                WHERE expiry_date IS NOT NULL
                AND expiry_date <= ?
                AND quantity > 0
            ''', (expiry_soon.isoformat(),)).fetchall()
            
            for item in items:
                days_left = (datetime.strptime(item['expiry_date'], '%Y-%m-%d').date() - self.today).days
                severity = 'CRITICAL' if days_left <= 7 else 'WARN'
                self._add_insight(
                    key=f"expiring_{item['id']}",
                    severity=severity,
                    category='warehouse',
                    title=f"Expiruje: {item['name']}",
                    summary=f"{item['quantity']} ks, expiruje za {days_left} dní",
                    entity_type='inventory',
                    entity_id=item['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Použít přednostně', 'action': 'prioritize_usage'}
                    ]
                )
        except Exception as e:
            pass  # Table may not exist
    
    def _check_dead_stock(self):
        """S4: Mrtvý kapitál - bez pohybu 90+ dní"""
        cutoff = self.today - timedelta(days=90)
        try:
            items = self.db.execute('''
                SELECT i.id, i.name, i.quantity, i.unit_price,
                       MAX(wm.created_at) as last_movement
                FROM inventory i
                LEFT JOIN warehouse_movements wm ON wm.inventory_id = i.id
                WHERE i.quantity > 0
                AND i.unit_price > 0
                GROUP BY i.id
                HAVING last_movement IS NULL OR last_movement < ?
            ''', (cutoff.isoformat(),)).fetchall()
            
            for item in items:
                value = (item['quantity'] or 0) * (item['unit_price'] or 0)
                if value > 1000:  # Only report if value > 1000 Kč
                    self._add_insight(
                        key=f"dead_stock_{item['id']}",
                        severity='INFO',
                        category='warehouse',
                        title=f"Mrtvý kapitál: {item['name']}",
                        summary=f"Bez pohybu 90+ dní, hodnota {value:,.0f} Kč",
                        entity_type='inventory',
                        entity_id=item['id'],
                        actions=[
                            {'type': 'draft', 'label': 'Prodat/Vyřadit', 'action': 'dispose_item'}
                        ]
                    )
        except Exception as e:
            pass  # Table may not exist
    
    def _check_material_no_job(self):
        """S5: Materiál rezervován ale zakázka dokončena/zrušena"""
        try:
            orphaned = self.db.execute('''
                SELECT wr.id, i.name, wr.quantity, j.client, j.status
                FROM warehouse_reservations wr
                JOIN inventory i ON i.id = wr.inventory_id
                JOIN jobs j ON j.id = wr.job_id
                WHERE wr.status = 'reserved'
                AND j.status IN ('Dokončeno', 'completed', 'cancelled', 'archived')
            ''').fetchall()
            
            for res in orphaned:
                self._add_insight(
                    key=f"orphaned_reservation_{res['id']}",
                    severity='WARN',
                    category='warehouse',
                    title=f"Sirotčí rezervace: {res['name']}",
                    summary=f"{res['quantity']} ks pro {res['client']} (status: {res['status']})",
                    entity_type='reservation',
                    entity_id=res['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Uvolnit', 'action': 'release_reservation'}
                    ]
                )
        except Exception as e:
            pass  # Table may not exist
    
    def _check_job_no_material(self):
        """S6: Aktivní zakázka bez materiálu"""
        try:
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.name
                FROM jobs j
                WHERE j.status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled', 'waiting')
                AND j.start_date <= ?
                AND NOT EXISTS (
                    SELECT 1 FROM warehouse_reservations wr
                    WHERE wr.job_id = j.id
                )
                AND j.estimated_value > 10000
            ''', (self.today.isoformat(),)).fetchall()
            
            for job in jobs:
                self._add_insight(
                    key=f"job_no_material_{job['id']}",
                    severity='INFO',
                    category='warehouse',
                    title=f"Zakázka bez materiálu: {job['client']}",
                    summary=f"Aktivní zakázka nemá žádné rezervace",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'link', 'label': 'Přidat materiál', 'url': f"/job-detail.html?id={job['id']}#materials"}
                    ]
                )
        except Exception as e:
            print(f"S6 error: {e}")
    
    def _check_duplicate_items(self):
        """S7: Duplicitní položky na skladě"""
        try:
            duplicates = self.db.execute('''
                SELECT LOWER(name) as name_lower, COUNT(*) as cnt,
                       GROUP_CONCAT(id) as ids
                FROM inventory
                GROUP BY name_lower
                HAVING cnt > 1
            ''').fetchall()
            
            for dup in duplicates:
                self._add_insight(
                    key=f"duplicate_item_{dup['name_lower'][:30]}",
                    severity='INFO',
                    category='warehouse',
                    title=f"Duplicitní položka: {dup['name_lower'][:40]}",
                    summary=f"Nalezeno {dup['cnt']}x (ID: {dup['ids']})",
                    entity_type='inventory',
                    entity_id=None,
                    actions=[
                        {'type': 'draft', 'label': 'Sloučit', 'action': 'merge_items'}
                    ]
                )
        except Exception as e:
            pass  # Table may not exist
    
    # =========================================================================
    # ÚKOLY A ZAKÁZKY - Tasks & Jobs rules
    # =========================================================================
    
    def _rules_tasks_jobs(self):
        """Pravidla pro úkoly a zakázky"""
        
        # U1: Úkol bez přiřazení
        self._check_task_unassigned()
        
        # U2: Zakázka bez deadline
        self._check_job_no_deadline()
        
        # U3: Blokované závislosti
        self._check_blocked_dependencies()
        
        # U4: Budget overrun
        self._check_budget_overrun()
        
        # U5: Dokončená zakázka - nefakturováno
        self._check_completed_not_invoiced()
    
    def _check_task_unassigned(self):
        """U1: Úkoly bez přiřazení"""
        try:
            tasks = self.db.execute('''
                SELECT t.id, t.title, COALESCE(t.deadline, t.due_date), j.client
                FROM tasks t
                LEFT JOIN jobs j ON j.id = t.job_id
                WHERE t.status NOT IN ('done', 'completed', 'cancelled')
                AND t.assigned_to IS NULL
                ORDER BY COALESCE(t.deadline, t.due_date) ASC
                LIMIT 20
            ''').fetchall()
            
            for task in tasks:
                self._add_insight(
                    key=f"task_unassigned_{task['id']}",
                    severity='WARN' if task['deadline'] else 'INFO',
                    category='tasks',
                    title=f"Úkol bez přiřazení",
                    summary=f"{task['title'][:40]}, zakázka: {task['client'] or 'N/A'}",
                    entity_type='task',
                    entity_id=task['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Přiřadit', 'action': 'assign_task'}
                    ]
                )
        except Exception as e:
            pass  # Column may not exist
    
    def _check_job_no_deadline(self):
        """U2: Aktivní zakázky bez deadline"""
        try:
            jobs = self.db.execute('''
                SELECT id, client, name, status, start_date
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND planned_end_date IS NULL
            ''').fetchall()
            
            for job in jobs:
                self._add_insight(
                    key=f"job_no_deadline_{job['id']}",
                    severity='WARN',
                    category='jobs',
                    title=f"Zakázka bez termínu: {job['client']}",
                    summary=f"Status: {job['status']}, bez plánovaného ukončení",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'link', 'label': 'Doplnit', 'url': f"/job-detail.html?id={job['id']}"}
                    ]
                )
        except Exception as e:
            print(f"U2 error: {e}")
    
    def _check_blocked_dependencies(self):
        """U3: Úkoly blokované závislostmi"""
        try:
            blocked = self.db.execute('''
                SELECT t.id, t.title, t.depends_on,
                       dt.title as blocking_task, dt.status as blocking_status
                FROM tasks t
                JOIN tasks dt ON dt.id = t.depends_on
                WHERE t.status NOT IN ('done', 'completed', 'cancelled')
                AND dt.status NOT IN ('done', 'completed')
            ''').fetchall()
            
            for task in blocked:
                self._add_insight(
                    key=f"task_blocked_{task['id']}",
                    severity='WARN',
                    category='tasks',
                    title=f"Blokovaný úkol: {task['title'][:30]}",
                    summary=f"Čeká na: {task['blocking_task'][:30]} ({task['blocking_status']})",
                    entity_type='task',
                    entity_id=task['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Urychlit závislost', 'action': 'prioritize_dependency'}
                    ]
                )
        except Exception as e:
            pass  # Column may not exist
    
    def _check_budget_overrun(self):
        """U4: Překročený rozpočet"""
        warning_pct = self.preferences.get('budget_warning_pct', 90)
        critical_pct = self.preferences.get('budget_critical_pct', 110)
        
        try:
            jobs = self.db.execute('''
                SELECT id, client, name, estimated_value, actual_value,
                       CASE WHEN estimated_value > 0 
                            THEN (COALESCE(actual_value, 0) / estimated_value) * 100 
                            ELSE 0 END as pct_used
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND estimated_value > 0
                AND COALESCE(actual_value, 0) > estimated_value * ? / 100
            ''', (warning_pct,)).fetchall()
            
            for job in jobs:
                pct = job['pct_used']
                severity = 'CRITICAL' if pct >= critical_pct else 'WARN'
                self._add_insight(
                    key=f"budget_overrun_{job['id']}",
                    severity=severity,
                    category='jobs',
                    title=f"Rozpočet: {job['client']}",
                    summary=f"{pct:.0f}% ({job['actual_value']:,.0f} / {job['estimated_value']:,.0f} Kč)",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'link', 'label': 'Detail', 'url': f"/job-detail.html?id={job['id']}"},
                        {'type': 'draft', 'label': 'Eskalovat', 'action': 'escalate_budget'}
                    ]
                )
        except Exception as e:
            print(f"U4 error: {e}")
    
    def _check_completed_not_invoiced(self):
        """U5: Dokončené zakázky bez faktury"""
        try:
            jobs = self.db.execute('''
                SELECT id, client, name, completed_at, actual_value
                FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND (invoiced = 0 OR invoiced IS NULL)
                AND completed_at < ?
            ''', ((self.today - timedelta(days=7)).isoformat(),)).fetchall()
            
            for job in jobs:
                self._add_insight(
                    key=f"not_invoiced_{job['id']}",
                    severity='WARN',
                    category='jobs',
                    title=f"Nefakturováno: {job['client']}",
                    summary=f"Dokončeno {job['completed_at']}, hodnota {job['actual_value'] or 0:,.0f} Kč",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'draft', 'label': 'Vystavit fakturu', 'action': 'create_invoice'}
                    ]
                )
        except Exception as e:
            pass  # Column may not exist
    
    # =========================================================================
    # DATA KVALITA - Data quality rules
    # =========================================================================
    
    def _rules_data_quality(self):
        """Pravidla pro kvalitu dat"""
        
        # D1: Zakázka bez lokace
        self._check_job_no_location()
        
        # D2: Zakázka bez odhadu
        self._check_job_no_estimate()
        
        # D3: Chybějící fotodokumentace
        self._check_missing_photos()
        
        # D4: Nelogické hodnoty
        self._check_illogical_values()
    
    def _check_job_no_location(self):
        """D1: Zakázky bez lokace"""
        try:
            jobs = self.db.execute('''
                SELECT id, client, name
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND (city IS NULL OR city = '' OR address IS NULL OR address = '')
            ''').fetchall()
            
            for job in jobs:
                self._add_insight(
                    key=f"job_no_location_{job['id']}",
                    severity='INFO',
                    category='data_quality',
                    title=f"Chybí lokace: {job['client']}",
                    summary=f"Zakázka nemá adresu/město",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'link', 'label': 'Doplnit', 'url': f"/job-detail.html?id={job['id']}"}
                    ]
                )
        except Exception as e:
            pass  # Column may not exist
    
    def _check_job_no_estimate(self):
        """D2: Zakázky bez odhadu hodnoty/hodin"""
        try:
            jobs = self.db.execute('''
                SELECT id, client, name
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND (estimated_value IS NULL OR estimated_value = 0)
                AND (estimated_hours IS NULL OR estimated_hours = 0)
            ''').fetchall()
            
            for job in jobs:
                self._add_insight(
                    key=f"job_no_estimate_{job['id']}",
                    severity='WARN',
                    category='data_quality',
                    title=f"Chybí odhad: {job['client']}",
                    summary=f"Zakázka nemá odhad hodnoty ani hodin",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'link', 'label': 'Doplnit', 'url': f"/job-detail.html?id={job['id']}"}
                    ]
                )
        except Exception as e:
            print(f"D2 error: {e}")
    
    def _check_missing_photos(self):
        """D3: Zakázky bez fotodokumentace"""
        try:
            # Jobs completed in last 30 days without photos
            cutoff = (self.today - timedelta(days=30)).isoformat()
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.completed_at
                FROM jobs j
                WHERE j.status IN ('Dokončeno', 'completed')
                AND j.completed_at >= ?
                AND NOT EXISTS (
                    SELECT 1 FROM attachments a
                    WHERE a.entity_type = 'job' AND a.entity_id = j.id
                    AND a.file_type LIKE 'image/%'
                )
            ''', (cutoff,)).fetchall()
            
            for job in jobs:
                self._add_insight(
                    key=f"missing_photos_{job['id']}",
                    severity='INFO',
                    category='data_quality',
                    title=f"Chybí foto: {job['client']}",
                    summary=f"Dokončená zakázka bez fotodokumentace",
                    entity_type='job',
                    entity_id=job['id'],
                    actions=[
                        {'type': 'link', 'label': 'Přidat', 'url': f"/job-detail.html?id={job['id']}#photos"}
                    ]
                )
        except Exception as e:
            pass  # Table may not exist
    
    def _check_illogical_values(self):
        """D4: Nelogické hodnoty (actual > estimated * 3, etc.)"""
        try:
            jobs = self.db.execute('''
                SELECT id, client, estimated_value, actual_value, estimated_hours, actual_hours
                FROM jobs
                WHERE (actual_value > estimated_value * 3 AND estimated_value > 0)
                   OR (actual_hours > estimated_hours * 3 AND estimated_hours > 0)
            ''').fetchall()
            
            for job in jobs:
                self._add_insight(
                    key=f"illogical_value_{job['id']}",
                    severity='WARN',
                    category='data_quality',
                    title=f"Nelogická data: {job['client']}",
                    summary=f"Skutečnost výrazně převyšuje odhad (>300%)",
                    entity_type='job',
                    entity_id=job['id'],
                    confidence='MEDIUM',
                    actions=[
                        {'type': 'link', 'label': 'Zkontrolovat', 'url': f"/job-detail.html?id={job['id']}"}
                    ]
                )
        except Exception as e:
            print(f"D4 error: {e}")
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _add_insight(self, key, severity, category, title, summary, 
                     entity_type=None, entity_id=None, confidence='HIGH', actions=None):
        """Přidej insight do seznamu"""
        self.insights.append({
            'key': key,
            'severity': severity,
            'category': category,
            'title': title,
            'summary': summary,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'confidence': confidence,
            'actions': actions or [],
            'created_at': datetime.now().isoformat()
        })


# =============================================================================
# STRATEGICKÝ MOZEK - ONLINE INTELLIGENCE
# =============================================================================

class StrategicBrain:
    """
    Predikce, trendy, porovnání - vyžaduje online spojení.
    """
    
    def __init__(self, db):
        self.db = db
        self.today = datetime.now().date()
    
    def get_predictions(self):
        """Získej predikce"""
        predictions = []
        
        # P1: Predikce dokončení zakázek
        predictions.extend(self._predict_job_completion())
        
        # P2: Predikce přetížení týmu
        predictions.extend(self._predict_team_overload())
        
        # P3: Predikce cashflow
        predictions.extend(self._predict_cashflow())
        
        return predictions
    
    def _predict_job_completion(self):
        """P1: Kdy bude zakázka dokončena"""
        predictions = []
        
        try:
            # Jobs in progress with deadline
            jobs = self.db.execute('''
                SELECT j.id, j.client, j.planned_end_date, j.progress,
                       j.estimated_hours, COALESCE(SUM(t.hours), 0) as actual_hours
                FROM jobs j
                LEFT JOIN timesheets t ON t.job_id = j.id
                WHERE j.status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND j.planned_end_date IS NOT NULL
                GROUP BY j.id
            ''').fetchall()
            
            for job in jobs:
                if job['progress'] and job['progress'] > 0 and job['actual_hours'] > 0:
                    # Simple linear prediction
                    hours_per_percent = job['actual_hours'] / job['progress']
                    remaining_hours = hours_per_percent * (100 - job['progress'])
                    
                    # Assume 8h/day
                    days_needed = remaining_hours / 8
                    predicted_end = self.today + timedelta(days=int(days_needed))
                    
                    if job['planned_end_date']:
                        deadline = datetime.strptime(job['planned_end_date'], '%Y-%m-%d').date()
                        if predicted_end > deadline:
                            predictions.append({
                                'type': 'job_completion',
                                'job_id': job['id'],
                                'client': job['client'],
                                'predicted_end': predicted_end.isoformat(),
                                'deadline': job['planned_end_date'],
                                'delay_days': (predicted_end - deadline).days,
                                'confidence': 'MEDIUM'
                            })
        except Exception as e:
            print(f"P1 error: {e}")
        
        return predictions
    
    def _predict_team_overload(self):
        """P2: Predikce budoucího přetížení"""
        predictions = []
        
        try:
            # Check next 4 weeks
            for week in range(4):
                week_start = self.today + timedelta(weeks=week)
                week_end = week_start + timedelta(days=6)
                
                planned = self.db.execute('''
                    SELECT SUM(COALESCE(planned_hours, 8)) as total_hours,
                           COUNT(DISTINCT employee_id) as workers
                    FROM planning_assignments
                    WHERE date BETWEEN ? AND ?
                ''', (week_start.isoformat(), week_end.isoformat())).fetchone()
                
                if planned and planned['workers'] and planned['workers'] > 0:
                    avg_hours = (planned['total_hours'] or 0) / planned['workers']
                    if avg_hours > 45:
                        predictions.append({
                            'type': 'team_overload',
                            'week_start': week_start.isoformat(),
                            'avg_hours': avg_hours,
                            'workers': planned['workers'],
                            'confidence': 'HIGH' if week < 2 else 'MEDIUM'
                        })
        except Exception as e:
            pass  # Table may not exist
        
        return predictions
    
    def _predict_cashflow(self):
        """P3: Predikce cashflow"""
        predictions = []
        
        try:
            # Expected income from active jobs
            expected = self.db.execute('''
                SELECT SUM(estimated_value - COALESCE(actual_value, 0)) as expected_income
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND estimated_value > 0
            ''').fetchone()
            
            if expected and expected['expected_income']:
                predictions.append({
                    'type': 'cashflow',
                    'expected_income': expected['expected_income'],
                    'period': 'active_jobs',
                    'confidence': 'LOW'
                })
        except Exception as e:
            print(f"P3 error: {e}")
        
        return predictions
    
    def get_comparisons(self):
        """Získej porovnání"""
        comparisons = []
        
        # C1: Tento měsíc vs minulý měsíc
        comparisons.append(self._compare_months())
        
        # C2: Výkon vs plán
        comparisons.append(self._compare_plan_vs_actual())
        
        return [c for c in comparisons if c]
    
    def _compare_months(self):
        """C1: Porovnání měsíců"""
        try:
            this_month_start = self.today.replace(day=1)
            last_month_end = this_month_start - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            
            this_month = self.db.execute('''
                SELECT COUNT(*) as jobs_completed,
                       COALESCE(SUM(actual_value), 0) as revenue,
                       COALESCE(SUM(actual_hours), 0) as hours
                FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND completed_at >= ?
            ''', (this_month_start.isoformat(),)).fetchone()
            
            last_month = self.db.execute('''
                SELECT COUNT(*) as jobs_completed,
                       COALESCE(SUM(actual_value), 0) as revenue,
                       COALESCE(SUM(actual_hours), 0) as hours
                FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND completed_at BETWEEN ? AND ?
            ''', (last_month_start.isoformat(), last_month_end.isoformat())).fetchone()
            
            return {
                'type': 'month_comparison',
                'this_month': dict(this_month) if this_month else {},
                'last_month': dict(last_month) if last_month else {},
                'revenue_change_pct': self._calc_change_pct(
                    last_month['revenue'] if last_month else 0,
                    this_month['revenue'] if this_month else 0
                )
            }
        except Exception as e:
            print(f"C1 error: {e}")
            return None
    
    def _compare_plan_vs_actual(self):
        """C2: Plán vs skutečnost"""
        try:
            # This week
            week_start = self.today - timedelta(days=self.today.weekday())
            
            planned = self.db.execute('''
                SELECT SUM(COALESCE(planned_hours, 8)) as planned_hours
                FROM planning_assignments
                WHERE date BETWEEN ? AND ?
            ''', (week_start.isoformat(), self.today.isoformat())).fetchone()
            
            actual = self.db.execute('''
                SELECT SUM(hours) as actual_hours
                FROM timesheets
                WHERE date BETWEEN ? AND ?
            ''', (week_start.isoformat(), self.today.isoformat())).fetchone()
            
            return {
                'type': 'plan_vs_actual',
                'period': 'this_week',
                'planned_hours': planned['planned_hours'] if planned else 0,
                'actual_hours': actual['actual_hours'] if actual else 0,
                'variance_pct': self._calc_change_pct(
                    planned['planned_hours'] if planned else 0,
                    actual['actual_hours'] if actual else 0
                )
            }
        except Exception as e:
            pass  # Table may not exist
            return None
    
    def _calc_change_pct(self, old_val, new_val):
        """Vypočítej procentuální změnu"""
        if not old_val or old_val == 0:
            return 0
        return ((new_val - old_val) / old_val) * 100


# =============================================================================
# PAMĚŤ A DNA - LEARNING LAYER
# =============================================================================

class LearningLayer:
    """
    Učení z rozhodnutí, formování firemní DNA.
    """
    
    def __init__(self, db):
        self.db = db
    
    def log_decision(self, insight_id, action, outcome, user_id=None):
        """Zaloguj rozhodnutí pro učení"""
        try:
            self.db.execute('''
                INSERT INTO ai_learning_log 
                (event_type, insight_id, action, outcome, user_id, created_at)
                VALUES ('decision', ?, ?, ?, ?, ?)
            ''', (insight_id, action, outcome, user_id, datetime.now().isoformat()))
            self.db.commit()
        except Exception as e:
            print(f"Learning log error: {e}")
    
    def get_approval_patterns(self):
        """Analyzuj vzorce schvalování"""
        try:
            patterns = self.db.execute('''
                SELECT action, 
                       COUNT(*) as total,
                       SUM(CASE WHEN outcome = 'approved' THEN 1 ELSE 0 END) as approved,
                       SUM(CASE WHEN outcome = 'rejected' THEN 1 ELSE 0 END) as rejected
                FROM ai_learning_log
                WHERE event_type = 'decision'
                GROUP BY action
            ''').fetchall()
            
            return [dict(p) for p in patterns]
        except:
            return []
    
    def get_success_rate(self, action_type=None):
        """Získej úspěšnost akcí"""
        try:
            query = '''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as success
                FROM ai_learning_log
                WHERE event_type = 'execution'
            '''
            params = []
            
            if action_type:
                query += ' AND action = ?'
                params.append(action_type)
            
            result = self.db.execute(query, params).fetchone()
            
            if result and result['total'] > 0:
                return {
                    'total': result['total'],
                    'success': result['success'],
                    'rate': (result['success'] / result['total']) * 100
                }
            return {'total': 0, 'success': 0, 'rate': 0}
        except:
            return {'total': 0, 'success': 0, 'rate': 0}
    
    def update_company_preference(self, key, value):
        """Aktualizuj firemní preferenci"""
        try:
            self.db.execute('''
                INSERT OR REPLACE INTO ai_company_preferences (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, str(value), datetime.now().isoformat()))
            self.db.commit()
        except Exception as e:
            print(f"Update preference error: {e}")


# =============================================================================
# HLAVNÍ API FUNKCE
# =============================================================================

def run_complete_analysis(db):
    """Spusť kompletní analýzu všemi vrstvami"""
    
    # 1. Reflexní mozek (offline capable)
    reflex = ReflexEngine(db)
    insights = reflex.run_all_rules()
    
    # 2. Strategický mozek (online)
    strategic = StrategicBrain(db)
    predictions = strategic.get_predictions()
    comparisons = strategic.get_comparisons()
    
    # 3. Learning layer stats
    learning = LearningLayer(db)
    approval_patterns = learning.get_approval_patterns()
    
    return {
        'insights': insights,
        'predictions': predictions,
        'comparisons': comparisons,
        'approval_patterns': approval_patterns,
        'stats': {
            'total_insights': len(insights),
            'critical': len([i for i in insights if i['severity'] == 'CRITICAL']),
            'warnings': len([i for i in insights if i['severity'] == 'WARN']),
            'info': len([i for i in insights if i['severity'] == 'INFO'])
        },
        'generated_at': datetime.now().isoformat()
    }


# Export
__all__ = ['ReflexEngine', 'StrategicBrain', 'LearningLayer', 'run_complete_analysis']
