"""
GREEN DAVID APP - AI OPERÁTOR ADVANCED MODULES V2
==================================================
Pokročilé moduly podle Master Prompt V2.

MODULY:
1. CAUSAL ENGINE - Root cause analýza
2. CONSTRAINT SOLVER - Optimalizace s omezením
3. DECISION HIERARCHY - Eskalace a priority
4. RISK MANAGEMENT - Rizika a mitigace
5. DATA QUALITY AUTOPILOT - Kvalita dat
6. LEARNING SYSTEM 2.0 - Pokročilé učení
7. MISSION REPLAY - Audit a replay
8. SOP COPILOT - Standardní postupy
9. SUPPLY CHAIN BRAIN - Dodavatelský řetězec
10. CUSTOMER OPS - Klientská automatizace
11. SECURITY & GOVERNANCE - Bezpečnost
12. DECISION JOURNAL - Deník rozhodnutí

Autor: Green David s.r.o.
Verze: 2.0 (Master Prompt V2 compliant)
"""

from datetime import datetime, timedelta
import json
import sqlite3
from typing import List, Dict, Optional, Any

# Reference na get_db
get_db = None

def get_db_with_row_factory():
    db = get_db()
    db.row_factory = sqlite3.Row
    return db


# =============================================================================
# 1. CAUSAL ENGINE - ROOT CAUSE ANALÝZA
# =============================================================================

class CausalEngine:
    """
    Analyzuje příčiny problémů.
    - Strom příčin
    - Důkazní řetězec
    - Symptom vs příčina
    - Kontrafaktuální scénáře
    """
    
    def __init__(self, db):
        self.db = db
    
    def analyze_job_delay(self, job_id: int) -> Dict:
        """Analyzuj příčiny zpoždění zakázky"""
        causes = []
        evidence = []
        
        try:
            job = self.db.execute('''
                SELECT * FROM jobs WHERE id = ?
            ''', (job_id,)).fetchone()
            
            if not job:
                return {'error': 'Job not found'}
            
            # Check various potential causes
            
            # 1. Nedostatek pracovníků
            worker_hours = self.db.execute('''
                SELECT SUM(hours) as total FROM timesheets WHERE job_id = ?
            ''', (job_id,)).fetchone()
            
            if job['estimated_hours'] and worker_hours['total']:
                if worker_hours['total'] < job['estimated_hours'] * 0.5:
                    causes.append({
                        'type': 'insufficient_labor',
                        'severity': 'high',
                        'description': 'Nedostatek odpracovaných hodin',
                        'evidence': f"Odpracováno {worker_hours['total']}h z odhadovaných {job['estimated_hours']}h"
                    })
                    evidence.append('timesheet_analysis')
            
            # 2. Chybějící materiál
            missing_material = self.db.execute('''
                SELECT i.name, wr.quantity as reserved, i.quantity as available
                FROM warehouse_reservations wr
                JOIN inventory i ON i.id = wr.inventory_id
                WHERE wr.job_id = ? AND wr.quantity > i.quantity
            ''', (job_id,)).fetchall()
            
            if missing_material:
                causes.append({
                    'type': 'missing_material',
                    'severity': 'high',
                    'description': 'Chybějící materiál',
                    'evidence': f"{len(missing_material)} položek není dostupných",
                    'items': [dict(m) for m in missing_material]
                })
                evidence.append('inventory_check')
            
            # 3. Blokované úkoly
            blocked_tasks = self.db.execute('''
                SELECT t.id, t.title, dt.title as blocking_task
                FROM tasks t
                JOIN tasks dt ON dt.id = t.depends_on
                WHERE t.job_id = ? 
                AND t.status NOT IN ('done', 'completed')
                AND dt.status NOT IN ('done', 'completed')
            ''', (job_id,)).fetchall()
            
            if blocked_tasks:
                causes.append({
                    'type': 'blocked_dependencies',
                    'severity': 'medium',
                    'description': 'Blokované závislosti úkolů',
                    'evidence': f"{len(blocked_tasks)} úkolů čeká na dokončení jiných",
                    'tasks': [dict(t) for t in blocked_tasks]
                })
                evidence.append('task_dependency_analysis')
            
            # 4. Přetížení klíčových pracovníků
            overloaded = self.db.execute('''
                SELECT e.name, SUM(t.hours) as weekly_hours
                FROM timesheets t
                JOIN employees e ON e.id = t.employee_id
                WHERE t.job_id = ?
                AND t.date >= date('now', '-7 days')
                GROUP BY e.id
                HAVING weekly_hours > 45
            ''', (job_id,)).fetchall()
            
            if overloaded:
                causes.append({
                    'type': 'worker_overload',
                    'severity': 'medium',
                    'description': 'Přetížení pracovníci',
                    'evidence': f"{len(overloaded)} pracovníků překročilo limit hodin"
                })
                evidence.append('workload_analysis')
            
            # Build cause tree
            root_cause = self._identify_root_cause(causes)
            
            return {
                'job_id': job_id,
                'client': job['client'],
                'causes': causes,
                'root_cause': root_cause,
                'evidence_chain': evidence,
                'counterfactual': self._generate_counterfactual(causes),
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Causal analysis error: {e}")
            return {'error': str(e)}
    
    def _identify_root_cause(self, causes: List[Dict]) -> Optional[Dict]:
        """Identifikuj kořenovou příčinu"""
        if not causes:
            return None
        
        # Priority: missing_material > insufficient_labor > blocked_dependencies > worker_overload
        priority = ['missing_material', 'insufficient_labor', 'blocked_dependencies', 'worker_overload']
        
        for cause_type in priority:
            for cause in causes:
                if cause['type'] == cause_type and cause['severity'] == 'high':
                    return cause
        
        # Return first high severity or first cause
        for cause in causes:
            if cause['severity'] == 'high':
                return cause
        
        return causes[0] if causes else None
    
    def _generate_counterfactual(self, causes: List[Dict]) -> str:
        """Generuj kontrafaktuální scénář"""
        if not causes:
            return "Žádné významné příčiny identifikovány."
        
        root = self._identify_root_cause(causes)
        if not root:
            return "Nelze určit hlavní příčinu."
        
        counterfactuals = {
            'missing_material': "Kdyby byl materiál objednán včas, zakázka by pravděpodobně nebyla zpožděna.",
            'insufficient_labor': "Kdyby bylo přiřazeno více pracovníků od začátku, zakázka by postupovala rychleji.",
            'blocked_dependencies': "Kdyby byly předchozí úkoly dokončeny podle plánu, práce by nebyla blokována.",
            'worker_overload': "Kdyby práce byla lépe rozdělena, nedošlo by k přetížení a zpoždění."
        }
        
        return counterfactuals.get(root['type'], "Příčina vyžaduje další analýzu.")


# =============================================================================
# 2. CONSTRAINT SOLVER - OPTIMALIZACE S OMEZENÍM
# =============================================================================

class ConstraintSolver:
    """
    Řeší plánování s ohledem na omezení.
    - Pracovní doba
    - Kvalifikace
    - Lokace a přejezdy
    - Zákonné limity
    """
    
    def __init__(self, db):
        self.db = db
        self.constraints = self._load_constraints()
    
    def _load_constraints(self) -> Dict:
        """Načti výchozí omezení"""
        return {
            'max_daily_hours': 10,
            'max_weekly_hours': 45,
            'min_break_hours': 11,  # Mezi směnami
            'max_travel_km': 50,
            'weekend_allowed': False,
            'overtime_requires_approval': True
        }
    
    def find_available_workers(self, job_id: int, date: str, required_skills: List[str] = None) -> List[Dict]:
        """Najdi dostupné pracovníky pro zakázku"""
        try:
            job = self.db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
            
            # Get all active employees
            employees = self.db.execute('''
                SELECT e.*, 
                       COALESCE(SUM(CASE WHEN t.date = ? THEN t.hours ELSE 0 END), 0) as hours_today,
                       COALESCE(SUM(CASE WHEN t.date >= date(?, '-7 days') THEN t.hours ELSE 0 END), 0) as hours_this_week
                FROM employees e
                LEFT JOIN timesheets t ON t.employee_id = e.id
                WHERE e.status = 'active'
                GROUP BY e.id
            ''', (date, date)).fetchall()
            
            available = []
            
            for emp in employees:
                constraints_ok = True
                violations = []
                
                # Check daily hours
                if emp['hours_today'] >= self.constraints['max_daily_hours']:
                    constraints_ok = False
                    violations.append('max_daily_hours')
                
                # Check weekly hours
                if emp['hours_this_week'] >= self.constraints['max_weekly_hours']:
                    constraints_ok = False
                    violations.append('max_weekly_hours')
                
                # Check existing assignments
                existing = self.db.execute('''
                    SELECT COUNT(*) as cnt FROM planning_assignments
                    WHERE employee_id = ? AND date = ?
                ''', (emp['id'], date)).fetchone()
                
                if existing and existing['cnt'] > 0:
                    violations.append('already_assigned')
                
                # Check skills if required
                skill_match = True
                if required_skills:
                    emp_skills = (emp['skills'] or '').lower().split(',')
                    for skill in required_skills:
                        if skill.lower().strip() not in [s.strip() for s in emp_skills]:
                            skill_match = False
                            violations.append(f'missing_skill:{skill}')
                
                available.append({
                    'id': emp['id'],
                    'name': emp['name'],
                    'role': emp['role'],
                    'available': constraints_ok and skill_match,
                    'hours_today': emp['hours_today'],
                    'hours_this_week': emp['hours_this_week'],
                    'remaining_daily': max(0, self.constraints['max_daily_hours'] - emp['hours_today']),
                    'remaining_weekly': max(0, self.constraints['max_weekly_hours'] - emp['hours_this_week']),
                    'violations': violations,
                    'score': self._calculate_worker_score(emp, job, violations)
                })
            
            # Sort by availability and score
            available.sort(key=lambda x: (-int(x['available']), -x['score']))
            
            return available
            
        except Exception as e:
            print(f"Constraint solver error: {e}")
            return []
    
    def _calculate_worker_score(self, employee: Dict, job: Dict, violations: List) -> float:
        """Vypočítej skóre vhodnosti pracovníka"""
        score = 100.0
        
        # Penalize violations
        score -= len(violations) * 20
        
        # Prefer workers with more remaining hours
        if employee['hours_this_week'] < 30:
            score += 10
        
        # TODO: Add location-based scoring
        # TODO: Add skill match scoring
        
        return max(0, score)
    
    def optimize_daily_plan(self, date: str) -> Dict:
        """Optimalizuj denní plán"""
        try:
            # Get all jobs needing work
            jobs = self.db.execute('''
                SELECT j.*, 
                       (j.estimated_hours - COALESCE(j.actual_hours, 0)) as remaining_hours
                FROM jobs j
                WHERE j.status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
                AND j.start_date <= ?
                ORDER BY j.planned_end_date ASC
            ''', (date,)).fetchall()
            
            # Get available workers
            workers = self.find_available_workers(0, date)
            available_workers = [w for w in workers if w['available']]
            
            assignments = []
            warnings = []
            
            for job in jobs:
                if job['remaining_hours'] <= 0:
                    continue
                
                # Find best workers for this job
                best_workers = self.find_available_workers(job['id'], date)
                suitable = [w for w in best_workers if w['available'] and w not in [a['worker'] for a in assignments]]
                
                if suitable:
                    worker = suitable[0]
                    hours = min(8, worker['remaining_daily'], job['remaining_hours'])
                    
                    assignments.append({
                        'job_id': job['id'],
                        'job_client': job['client'],
                        'worker': worker,
                        'hours': hours
                    })
                else:
                    warnings.append({
                        'type': 'no_available_worker',
                        'job_id': job['id'],
                        'job_client': job['client'],
                        'message': f"Žádný dostupný pracovník pro {job['client']}"
                    })
            
            return {
                'date': date,
                'assignments': assignments,
                'warnings': warnings,
                'total_hours': sum(a['hours'] for a in assignments),
                'workers_used': len(set(a['worker']['id'] for a in assignments)),
                'optimized_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Plan optimization error: {e}")
            return {'error': str(e)}


# =============================================================================
# 3. DECISION HIERARCHY - ESKALACE A PRIORITY
# =============================================================================

class DecisionHierarchy:
    """
    Řídí eskalaci rozhodnutí podle hierarchie.
    - Decision thresholds
    - Escalation ladder
    - Role-based priority
    - SLA reakce
    - Do-Not-Disturb logika
    """
    
    THRESHOLDS = {
        'budget_warning': 0.9,      # 90% rozpočtu
        'budget_critical': 1.1,     # 110% rozpočtu
        'deadline_warning_days': 3,
        'deadline_critical_days': 0,
        'hours_warning': 40,
        'hours_critical': 50
    }
    
    ESCALATION_LADDER = [
        {'level': 1, 'role': 'worker', 'can_approve': ['timesheet', 'minor_task']},
        {'level': 2, 'role': 'team_lead', 'can_approve': ['task_reassign', 'material_request', 'schedule_change']},
        {'level': 3, 'role': 'manager', 'can_approve': ['budget_increase', 'deadline_change', 'hiring']},
        {'level': 4, 'role': 'owner', 'can_approve': ['contract_change', 'major_expense', 'strategic_decision']}
    ]
    
    SLA_RESPONSE_TIMES = {
        'critical': timedelta(hours=1),
        'high': timedelta(hours=4),
        'medium': timedelta(hours=24),
        'low': timedelta(hours=72)
    }
    
    def __init__(self, db):
        self.db = db
    
    def get_required_approval_level(self, action_type: str, value: float = 0) -> Dict:
        """Zjisti potřebnou úroveň schválení"""
        
        # Budget-based escalation
        if action_type == 'budget_increase':
            if value > 100000:
                return {'level': 4, 'role': 'owner', 'reason': 'Vysoká částka'}
            elif value > 20000:
                return {'level': 3, 'role': 'manager', 'reason': 'Střední částka'}
            else:
                return {'level': 2, 'role': 'team_lead', 'reason': 'Nízká částka'}
        
        # Find in escalation ladder
        for level in self.ESCALATION_LADDER:
            if action_type in level['can_approve']:
                return {'level': level['level'], 'role': level['role'], 'reason': 'Standard workflow'}
        
        # Default to manager
        return {'level': 3, 'role': 'manager', 'reason': 'Výchozí eskalace'}
    
    def check_sla_breach(self, insight_id: str, severity: str, created_at: str) -> Dict:
        """Zkontroluj porušení SLA"""
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.now()
            elapsed = now - created.replace(tzinfo=None)
            
            sla = self.SLA_RESPONSE_TIMES.get(severity, self.SLA_RESPONSE_TIMES['medium'])
            
            if elapsed > sla:
                return {
                    'breached': True,
                    'severity': severity,
                    'elapsed': str(elapsed),
                    'sla': str(sla),
                    'overdue_by': str(elapsed - sla)
                }
            else:
                return {
                    'breached': False,
                    'severity': severity,
                    'elapsed': str(elapsed),
                    'sla': str(sla),
                    'remaining': str(sla - elapsed)
                }
        except:
            return {'breached': False, 'error': 'Invalid date'}
    
    def should_notify(self, user_role: str, severity: str, current_hour: int = None) -> Dict:
        """Rozhodni jestli notifikovat (Do-Not-Disturb logika)"""
        if current_hour is None:
            current_hour = datetime.now().hour
        
        # Night hours (22:00 - 07:00) - only critical
        is_night = current_hour >= 22 or current_hour < 7
        
        # Weekend check
        is_weekend = datetime.now().weekday() >= 5
        
        if severity == 'critical':
            return {'notify': True, 'channel': 'sms', 'reason': 'Critical vždy notifikuje'}
        
        if is_night:
            return {'notify': False, 'channel': None, 'reason': 'Noční hodiny - pouze critical'}
        
        if is_weekend and severity not in ['critical', 'high']:
            return {'notify': False, 'channel': None, 'reason': 'Víkend - pouze critical/high'}
        
        # Role-based
        if user_role == 'owner':
            return {'notify': severity in ['critical', 'high'], 'channel': 'push', 'reason': 'Owner - pouze důležité'}
        
        return {'notify': True, 'channel': 'app', 'reason': 'Standard notifikace'}


# =============================================================================
# 4. RISK MANAGEMENT - RIZIKA A MITIGACE
# =============================================================================

class RiskManager:
    """
    Správa rizik projektu.
    - Risk registry
    - Risk scoring
    - Mitigation playbooks
    - Early warnings
    """
    
    RISK_CATEGORIES = [
        'schedule', 'budget', 'resource', 'quality', 
        'safety', 'weather', 'client', 'supplier'
    ]
    
    MITIGATION_PLAYBOOKS = {
        'schedule_delay': [
            {'action': 'add_workers', 'description': 'Přidat pracovníky', 'cost': 'medium'},
            {'action': 'overtime', 'description': 'Přesčasy', 'cost': 'high'},
            {'action': 'reschedule', 'description': 'Přeplánovat', 'cost': 'low'}
        ],
        'budget_overrun': [
            {'action': 'review_scope', 'description': 'Přezkoumat rozsah', 'cost': 'low'},
            {'action': 'negotiate', 'description': 'Vyjednávat s klientem', 'cost': 'low'},
            {'action': 'find_savings', 'description': 'Najít úspory', 'cost': 'medium'}
        ],
        'resource_shortage': [
            {'action': 'reassign', 'description': 'Přerozdělit', 'cost': 'low'},
            {'action': 'hire_temp', 'description': 'Najmout brigádníka', 'cost': 'medium'},
            {'action': 'outsource', 'description': 'Outsourcovat', 'cost': 'high'}
        ],
        'weather_risk': [
            {'action': 'indoor_work', 'description': 'Přesunout na vnitřní práce', 'cost': 'low'},
            {'action': 'delay_start', 'description': 'Odložit začátek', 'cost': 'medium'},
            {'action': 'protective_measures', 'description': 'Ochranná opatření', 'cost': 'medium'}
        ]
    }
    
    def __init__(self, db):
        self.db = db
    
    def assess_job_risks(self, job_id: int) -> List[Dict]:
        """Vyhodnoť rizika zakázky"""
        risks = []
        
        try:
            job = self.db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
            if not job:
                return []
            
            today = datetime.now().date()
            
            # Schedule risk
            if job['planned_end_date']:
                deadline = datetime.strptime(job['planned_end_date'], '%Y-%m-%d').date()
                days_left = (deadline - today).days
                progress = job['progress'] or 0
                
                # Calculate expected progress
                if job['start_date']:
                    start = datetime.strptime(job['start_date'], '%Y-%m-%d').date()
                    total_days = (deadline - start).days
                    elapsed_days = (today - start).days
                    expected_progress = (elapsed_days / total_days * 100) if total_days > 0 else 0
                    
                    if progress < expected_progress - 20:
                        risks.append({
                            'category': 'schedule',
                            'type': 'schedule_delay',
                            'severity': 'high' if progress < expected_progress - 40 else 'medium',
                            'score': self._calculate_risk_score('schedule', progress, expected_progress),
                            'description': f'Progress {progress}% vs očekávaných {expected_progress:.0f}%',
                            'mitigation': self.MITIGATION_PLAYBOOKS['schedule_delay']
                        })
            
            # Budget risk
            if job['estimated_value'] and job['actual_value']:
                budget_pct = (job['actual_value'] / job['estimated_value']) * 100
                if budget_pct > 90:
                    risks.append({
                        'category': 'budget',
                        'type': 'budget_overrun',
                        'severity': 'high' if budget_pct > 110 else 'medium',
                        'score': self._calculate_risk_score('budget', budget_pct, 100),
                        'description': f'Vyčerpáno {budget_pct:.0f}% rozpočtu',
                        'mitigation': self.MITIGATION_PLAYBOOKS['budget_overrun']
                    })
            
            # Resource risk - check if enough workers assigned
            assignments = self.db.execute('''
                SELECT COUNT(DISTINCT employee_id) as workers
                FROM planning_assignments
                WHERE job_id = ? AND date >= ?
            ''', (job_id, today.isoformat())).fetchone()
            
            if not assignments or assignments['workers'] == 0:
                risks.append({
                    'category': 'resource',
                    'type': 'resource_shortage',
                    'severity': 'high',
                    'score': 80,
                    'description': 'Žádní pracovníci přiřazeni',
                    'mitigation': self.MITIGATION_PLAYBOOKS['resource_shortage']
                })
            
            # Weather risk for outdoor jobs
            if job['tags'] and 'outdoor' in str(job['tags']).lower():
                risks.append({
                    'category': 'weather',
                    'type': 'weather_risk',
                    'severity': 'low',
                    'score': 30,
                    'description': 'Venkovní práce - závislost na počasí',
                    'mitigation': self.MITIGATION_PLAYBOOKS['weather_risk']
                })
            
            return sorted(risks, key=lambda x: -x['score'])
            
        except Exception as e:
            print(f"Risk assessment error: {e}")
            return []
    
    def _calculate_risk_score(self, category: str, actual: float, expected: float) -> int:
        """Vypočítej skóre rizika (0-100)"""
        if expected == 0:
            return 50
        
        variance = abs(actual - expected) / expected * 100
        
        # Different scoring for different categories
        if category == 'schedule':
            # Higher variance = higher risk
            return min(100, int(variance * 2))
        elif category == 'budget':
            # Over budget is worse than under
            if actual > expected:
                return min(100, int((actual - expected) / expected * 200))
            return 0
        
        return min(100, int(variance))
    
    def get_risk_summary(self) -> Dict:
        """Získej souhrn všech rizik"""
        try:
            jobs = self.db.execute('''
                SELECT id FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
            ''').fetchall()
            
            all_risks = []
            for job in jobs:
                risks = self.assess_job_risks(job['id'])
                for risk in risks:
                    risk['job_id'] = job['id']
                    all_risks.append(risk)
            
            # Group by severity
            high = [r for r in all_risks if r['severity'] == 'high']
            medium = [r for r in all_risks if r['severity'] == 'medium']
            low = [r for r in all_risks if r['severity'] == 'low']
            
            return {
                'total_risks': len(all_risks),
                'high': len(high),
                'medium': len(medium),
                'low': len(low),
                'top_risks': all_risks[:10],
                'by_category': self._group_by_category(all_risks)
            }
        except Exception as e:
            print(f"Risk summary error: {e}")
            return {'total_risks': 0}
    
    def _group_by_category(self, risks: List[Dict]) -> Dict:
        """Seskup rizika podle kategorie"""
        grouped = {}
        for risk in risks:
            cat = risk['category']
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(risk)
        return {k: len(v) for k, v in grouped.items()}


# =============================================================================
# 5. DATA QUALITY AUTOPILOT
# =============================================================================

class DataQualityAutopilot:
    """
    Automatická kontrola a oprava kvality dat.
    - Completeness score
    - Self-healing návrhy
    - Anomaly detection
    """
    
    REQUIRED_FIELDS = {
        'jobs': ['client', 'name', 'status', 'estimated_value', 'planned_end_date'],
        'employees': ['name', 'email', 'role', 'status'],
        'tasks': ['title', 'status', 'job_id'],
        'inventory': ['name', 'quantity', 'unit']
    }
    
    def __init__(self, db):
        self.db = db
    
    def calculate_completeness_score(self, entity_type: str, entity_id: int = None) -> Dict:
        """Vypočítej skóre kompletnosti dat"""
        try:
            if entity_type not in self.REQUIRED_FIELDS:
                return {'error': f'Unknown entity type: {entity_type}'}
            
            required = self.REQUIRED_FIELDS[entity_type]
            
            if entity_id:
                # Single entity
                row = self.db.execute(f'SELECT * FROM {entity_type} WHERE id = ?', (entity_id,)).fetchone()
                if not row:
                    return {'error': 'Entity not found'}
                
                filled = sum(1 for f in required if row[f] is not None and row[f] != '')
                score = (filled / len(required)) * 100
                
                missing = [f for f in required if row[f] is None or row[f] == '']
                
                return {
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                    'score': score,
                    'filled': filled,
                    'total': len(required),
                    'missing_fields': missing,
                    'healing_suggestions': self._get_healing_suggestions(entity_type, missing)
                }
            else:
                # All entities of type
                rows = self.db.execute(f'SELECT * FROM {entity_type}').fetchall()
                
                total_score = 0
                incomplete = []
                
                for row in rows:
                    filled = sum(1 for f in required if row[f] is not None and row[f] != '')
                    score = (filled / len(required)) * 100
                    total_score += score
                    
                    if score < 100:
                        missing = [f for f in required if row[f] is None or row[f] == '']
                        incomplete.append({
                            'id': row['id'],
                            'score': score,
                            'missing': missing
                        })
                
                avg_score = total_score / len(rows) if rows else 0
                
                return {
                    'entity_type': entity_type,
                    'average_score': avg_score,
                    'total_entities': len(rows),
                    'incomplete_count': len(incomplete),
                    'incomplete_entities': incomplete[:20]  # Top 20
                }
                
        except Exception as e:
            print(f"Completeness score error: {e}")
            return {'error': str(e)}
    
    def _get_healing_suggestions(self, entity_type: str, missing_fields: List[str]) -> List[Dict]:
        """Generuj návrhy na opravu"""
        suggestions = []
        
        for field in missing_fields:
            suggestion = {
                'field': field,
                'action': 'fill_required',
                'priority': 'high' if field in ['client', 'name', 'email'] else 'medium'
            }
            
            # Add smart suggestions based on field
            if field == 'estimated_value':
                suggestion['hint'] = 'Použijte průměr podobných zakázek'
            elif field == 'planned_end_date':
                suggestion['hint'] = 'Nastavte deadline na základě rozsahu práce'
            elif field == 'email':
                suggestion['hint'] = 'Kontaktujte zaměstnance pro doplnění'
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def detect_anomalies(self) -> List[Dict]:
        """Detekuj anomálie v datech"""
        anomalies = []
        
        try:
            # Jobs with actual > estimated * 3
            jobs = self.db.execute('''
                SELECT id, client, actual_value, estimated_value
                FROM jobs
                WHERE actual_value > estimated_value * 3 AND estimated_value > 0
            ''').fetchall()
            
            for job in jobs:
                anomalies.append({
                    'type': 'value_anomaly',
                    'entity': 'job',
                    'entity_id': job['id'],
                    'description': f"Skutečná hodnota {job['actual_value']} je 3x vyšší než odhad {job['estimated_value']}",
                    'severity': 'high'
                })
            
            # Employees with >60h in a week
            overworked = self.db.execute('''
                SELECT e.id, e.name, SUM(t.hours) as weekly_hours
                FROM employees e
                JOIN timesheets t ON t.employee_id = e.id
                WHERE t.date >= date('now', '-7 days')
                GROUP BY e.id
                HAVING weekly_hours > 60
            ''').fetchall()
            
            for emp in overworked:
                anomalies.append({
                    'type': 'hours_anomaly',
                    'entity': 'employee',
                    'entity_id': emp['id'],
                    'description': f"{emp['name']} má {emp['weekly_hours']}h tento týden (>60h)",
                    'severity': 'high'
                })
            
            # Negative inventory
            negative = self.db.execute('''
                SELECT id, name, quantity FROM inventory WHERE quantity < 0
            ''').fetchall()
            
            for item in negative:
                anomalies.append({
                    'type': 'negative_stock',
                    'entity': 'inventory',
                    'entity_id': item['id'],
                    'description': f"{item['name']} má záporné množství: {item['quantity']}",
                    'severity': 'critical'
                })
            
            return anomalies
            
        except Exception as e:
            print(f"Anomaly detection error: {e}")
            return []


# =============================================================================
# 6. DECISION JOURNAL - DENÍK ROZHODNUTÍ
# =============================================================================

class DecisionJournal:
    """
    Ukládá a analyzuje rozhodnutí.
    - Návrh, důvod, schválení, výsledek, poučení
    - Paměť firmy
    - Audit trail
    """
    
    def __init__(self, db):
        self.db = db
        self._ensure_table()
    
    def _ensure_table(self):
        """Zajisti existenci tabulky"""
        try:
            self.db.execute('''
                CREATE TABLE IF NOT EXISTS decision_journal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    context TEXT,
                    proposal TEXT,
                    reasoning TEXT,
                    alternatives TEXT,
                    approved_by INTEGER,
                    approval_status TEXT DEFAULT 'pending',
                    approval_date TEXT,
                    outcome TEXT,
                    outcome_date TEXT,
                    lessons_learned TEXT,
                    tags TEXT,
                    entity_type TEXT,
                    entity_id INTEGER,
                    created_at TEXT NOT NULL,
                    created_by INTEGER
                )
            ''')
            self.db.commit()
        except:
            pass
    
    def record_decision(self, decision_type: str, title: str, 
                       proposal: str, reasoning: str,
                       alternatives: List[str] = None,
                       entity_type: str = None, entity_id: int = None,
                       tags: List[str] = None, created_by: int = None) -> int:
        """Zaznamenej nové rozhodnutí"""
        try:
            cursor = self.db.execute('''
                INSERT INTO decision_journal 
                (decision_type, title, proposal, reasoning, alternatives, 
                 entity_type, entity_id, tags, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision_type,
                title,
                proposal,
                reasoning,
                json.dumps(alternatives) if alternatives else None,
                entity_type,
                entity_id,
                json.dumps(tags) if tags else None,
                datetime.now().isoformat(),
                created_by
            ))
            self.db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Record decision error: {e}")
            return None
    
    def approve_decision(self, decision_id: int, approved_by: int, status: str = 'approved') -> bool:
        """Schval nebo zamítni rozhodnutí"""
        try:
            self.db.execute('''
                UPDATE decision_journal
                SET approval_status = ?, approved_by = ?, approval_date = ?
                WHERE id = ?
            ''', (status, approved_by, datetime.now().isoformat(), decision_id))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Approve decision error: {e}")
            return False
    
    def record_outcome(self, decision_id: int, outcome: str, lessons: str = None) -> bool:
        """Zaznamenej výsledek rozhodnutí"""
        try:
            self.db.execute('''
                UPDATE decision_journal
                SET outcome = ?, outcome_date = ?, lessons_learned = ?
                WHERE id = ?
            ''', (outcome, datetime.now().isoformat(), lessons, decision_id))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Record outcome error: {e}")
            return False
    
    def get_decision_history(self, entity_type: str = None, entity_id: int = None,
                            limit: int = 50) -> List[Dict]:
        """Získej historii rozhodnutí"""
        try:
            query = 'SELECT * FROM decision_journal WHERE 1=1'
            params = []
            
            if entity_type:
                query += ' AND entity_type = ?'
                params.append(entity_type)
            
            if entity_id:
                query += ' AND entity_id = ?'
                params.append(entity_id)
            
            query += ' ORDER BY created_at DESC LIMIT ?'
            params.append(limit)
            
            rows = self.db.execute(query, params).fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Get decision history error: {e}")
            return []
    
    def get_lessons_learned(self, decision_type: str = None) -> List[Dict]:
        """Získej poučení z minulých rozhodnutí"""
        try:
            query = '''
                SELECT decision_type, title, proposal, outcome, lessons_learned
                FROM decision_journal
                WHERE outcome IS NOT NULL AND lessons_learned IS NOT NULL
            '''
            params = []
            
            if decision_type:
                query += ' AND decision_type = ?'
                params.append(decision_type)
            
            query += ' ORDER BY outcome_date DESC LIMIT 50'
            
            rows = self.db.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Get lessons error: {e}")
            return []
    
    def get_decision_stats(self) -> Dict:
        """Statistiky rozhodnutí"""
        try:
            total = self.db.execute('SELECT COUNT(*) as cnt FROM decision_journal').fetchone()['cnt']
            approved = self.db.execute("SELECT COUNT(*) as cnt FROM decision_journal WHERE approval_status = 'approved'").fetchone()['cnt']
            rejected = self.db.execute("SELECT COUNT(*) as cnt FROM decision_journal WHERE approval_status = 'rejected'").fetchone()['cnt']
            pending = self.db.execute("SELECT COUNT(*) as cnt FROM decision_journal WHERE approval_status = 'pending'").fetchone()['cnt']
            with_outcome = self.db.execute("SELECT COUNT(*) as cnt FROM decision_journal WHERE outcome IS NOT NULL").fetchone()['cnt']
            
            return {
                'total': total,
                'approved': approved,
                'rejected': rejected,
                'pending': pending,
                'with_outcome': with_outcome,
                'approval_rate': (approved / (approved + rejected) * 100) if (approved + rejected) > 0 else 0
            }
        except Exception as e:
            print(f"Decision stats error: {e}")
            return {}


# =============================================================================
# 7. SUPPLY CHAIN BRAIN
# =============================================================================

class SupplyChainBrain:
    """
    Inteligence dodavatelského řetězce.
    - Predikce spotřeby
    - Dynamické min/max
    - Vendor scoring
    """
    
    def __init__(self, db):
        self.db = db
    
    def predict_consumption(self, item_id: int, days: int = 30) -> Dict:
        """Predikuj spotřebu položky"""
        try:
            # Get historical consumption
            movements = self.db.execute('''
                SELECT SUM(ABS(quantity)) as total, COUNT(*) as count
                FROM warehouse_movements
                WHERE inventory_id = ? 
                AND movement_type IN ('usage', 'out', 'reservation')
                AND created_at >= date('now', '-90 days')
            ''', (item_id,)).fetchone()
            
            if not movements or not movements['total']:
                return {
                    'item_id': item_id,
                    'predicted_consumption': 0,
                    'confidence': 'low',
                    'message': 'Nedostatek historických dat'
                }
            
            # Average daily consumption over 90 days
            daily_avg = movements['total'] / 90
            predicted = daily_avg * days
            
            # Get current stock
            item = self.db.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
            current_stock = item['quantity'] if item else 0
            
            days_until_zero = current_stock / daily_avg if daily_avg > 0 else 999
            
            return {
                'item_id': item_id,
                'item_name': item['name'] if item else None,
                'current_stock': current_stock,
                'daily_average': round(daily_avg, 2),
                'predicted_consumption': round(predicted, 0),
                'days_until_zero': round(days_until_zero, 0),
                'reorder_recommended': days_until_zero < 14,
                'confidence': 'high' if movements['count'] > 10 else 'medium'
            }
        except Exception as e:
            print(f"Predict consumption error: {e}")
            return {'error': str(e)}
    
    def calculate_dynamic_minmax(self, item_id: int) -> Dict:
        """Vypočítej dynamické minimum a maximum"""
        try:
            prediction = self.predict_consumption(item_id, 30)
            
            if 'error' in prediction:
                return prediction
            
            daily_avg = prediction.get('daily_average', 0)
            
            # Safety stock = 7 days of average consumption
            safety_stock = round(daily_avg * 7)
            
            # Reorder point = safety stock + lead time consumption (assume 5 days)
            lead_time_days = 5
            reorder_point = round(safety_stock + (daily_avg * lead_time_days))
            
            # Max = reorder point + economic order quantity (assume 30 days supply)
            max_stock = round(reorder_point + (daily_avg * 30))
            
            return {
                'item_id': item_id,
                'recommended_min': reorder_point,
                'recommended_max': max_stock,
                'safety_stock': safety_stock,
                'lead_time_days': lead_time_days,
                'daily_average': daily_avg
            }
        except Exception as e:
            print(f"Dynamic minmax error: {e}")
            return {'error': str(e)}
    
    def get_dead_capital_report(self) -> List[Dict]:
        """Report mrtvého kapitálu"""
        try:
            items = self.db.execute('''
                SELECT i.id, i.name, i.quantity, i.unit_price,
                       (i.quantity * COALESCE(i.unit_price, 0)) as value,
                       MAX(wm.created_at) as last_movement
                FROM inventory i
                LEFT JOIN warehouse_movements wm ON wm.inventory_id = i.id
                WHERE i.quantity > 0
                GROUP BY i.id
                HAVING last_movement IS NULL OR last_movement < date('now', '-90 days')
                ORDER BY value DESC
            ''').fetchall()
            
            total_value = sum(item['value'] or 0 for item in items)
            
            return {
                'items': [dict(item) for item in items],
                'total_items': len(items),
                'total_value': total_value,
                'recommendations': [
                    'Zvážit likvidaci položek bez pohybu >180 dní',
                    'Nabídnout slevu na položky bez pohybu >90 dní',
                    'Zkontrolovat, zda jsou položky stále potřebné'
                ]
            }
        except Exception as e:
            print(f"Dead capital report error: {e}")
            return {'items': [], 'total_value': 0}


# =============================================================================
# 8. MISSION REPLAY - AUDIT A REPLAY
# =============================================================================

class MissionReplay:
    """
    Přehrávání a analýza historie.
    - Timeline replay
    - Audit telemetrie
    - Incident reports
    """
    
    def __init__(self, db):
        self.db = db
    
    def get_job_timeline(self, job_id: int) -> List[Dict]:
        """Získej timeline zakázky"""
        events = []
        
        try:
            # Job creation and updates
            job = self.db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
            if job:
                events.append({
                    'type': 'job_created',
                    'date': job['created_at'] or job['start_date'],
                    'description': f"Zakázka vytvořena: {job['client']}"
                })
            
            # Timesheets
            timesheets = self.db.execute('''
                SELECT t.date, t.hours, e.name as worker
                FROM timesheets t
                JOIN employees e ON e.id = t.employee_id
                WHERE t.job_id = ?
                ORDER BY t.date
            ''', (job_id,)).fetchall()
            
            for ts in timesheets:
                events.append({
                    'type': 'work_logged',
                    'date': ts['date'],
                    'description': f"{ts['worker']}: {ts['hours']}h"
                })
            
            # Tasks
            tasks = self.db.execute('''
                SELECT title, status, created_at, updated_at
                FROM tasks
                WHERE job_id = ?
                ORDER BY created_at
            ''', (job_id,)).fetchall()
            
            for task in tasks:
                events.append({
                    'type': 'task_created',
                    'date': task['created_at'],
                    'description': f"Úkol: {task['title']}"
                })
                if task['status'] in ('done', 'completed'):
                    events.append({
                        'type': 'task_completed',
                        'date': task['updated_at'],
                        'description': f"Dokončeno: {task['title']}"
                    })
            
            # Material reservations
            reservations = self.db.execute('''
                SELECT wr.created_at, wr.quantity, i.name
                FROM warehouse_reservations wr
                JOIN inventory i ON i.id = wr.inventory_id
                WHERE wr.job_id = ?
            ''', (job_id,)).fetchall()
            
            for res in reservations:
                events.append({
                    'type': 'material_reserved',
                    'date': res['created_at'],
                    'description': f"Rezervace: {res['quantity']}x {res['name']}"
                })
            
            # Sort by date
            events.sort(key=lambda x: x['date'] or '1970-01-01')
            
            return events
            
        except Exception as e:
            print(f"Job timeline error: {e}")
            return []
    
    def generate_incident_report(self, job_id: int, incident_type: str) -> Dict:
        """Generuj incident report"""
        try:
            job = self.db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
            timeline = self.get_job_timeline(job_id)
            
            # Analyze based on incident type
            analysis = {}
            
            if incident_type == 'delay':
                # Find delays
                if job['planned_end_date'] and job['completed_at']:
                    planned = datetime.strptime(job['planned_end_date'], '%Y-%m-%d').date()
                    actual = datetime.strptime(job['completed_at'][:10], '%Y-%m-%d').date()
                    delay_days = (actual - planned).days
                    analysis['delay_days'] = delay_days
                
                # Count work gaps
                work_dates = [e['date'] for e in timeline if e['type'] == 'work_logged']
                if work_dates:
                    analysis['first_work'] = min(work_dates)
                    analysis['last_work'] = max(work_dates)
                    analysis['work_days'] = len(set(work_dates))
            
            elif incident_type == 'budget_overrun':
                if job['estimated_value'] and job['actual_value']:
                    analysis['estimated'] = job['estimated_value']
                    analysis['actual'] = job['actual_value']
                    analysis['overrun'] = job['actual_value'] - job['estimated_value']
                    analysis['overrun_pct'] = (job['actual_value'] / job['estimated_value'] - 1) * 100
            
            return {
                'job_id': job_id,
                'client': job['client'] if job else None,
                'incident_type': incident_type,
                'timeline_events': len(timeline),
                'analysis': analysis,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Incident report error: {e}")
            return {'error': str(e)}


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'CausalEngine',
    'ConstraintSolver', 
    'DecisionHierarchy',
    'RiskManager',
    'DataQualityAutopilot',
    'DecisionJournal',
    'SupplyChainBrain',
    'MissionReplay'
]
