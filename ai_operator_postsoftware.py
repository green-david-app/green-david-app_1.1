"""
GREEN DAVID APP - AI OPERÁTOR POST-SOFTWARE LAYER V3
=====================================================
Pokročilé "post-software" schopnosti podle Master Prompt V3.

POST-SOFTWARE SCHOPNOSTI:
1. ZERO-UI MODE - Kontextové zobrazení bez menu
2. CONTEXTUAL INTELLIGENCE FIELD - Reakce na lokaci, čas, roli
3. SELF-ORGANIZING WORK - Automatická reorganizace práce
4. DECISION SHADOW - Digitální stín rozhodnutí
5. PROBABILITY VISUALIZATION - Mapa pravděpodobností
6. ADAPTIVE IDENTITY SYSTEM - Adaptace na velikost firmy
7. COLLECTIVE INTELLIGENCE NETWORK - Anonymizovaný benchmark
8. DIGITAL ENERGY MAP - Vizualizace toku práce/zdrojů
9. HUMAN-AI SYMBIOSIS MODE - Spolu-rozhodovací partner
10. TIME-LAYERED VIEW - Více časových vrstev současně
11. AUTONOMOUS MICRO-ECONOMY - Interní ekonomické signály
12. REALITY SIMULATION ENGINE - Simulace budoucnosti

META LAYER - ORGANIZAČNÍ VĚDOMÍ

Autor: Green David s.r.o.
Verze: 3.0 (Post-Software Layer)
"""

from datetime import datetime, timedelta
import json
import sqlite3
import math
import random
from typing import List, Dict, Optional, Any, Tuple

# Reference na get_db
get_db = None

def get_db_with_row_factory():
    db = get_db()
    db.row_factory = sqlite3.Row
    return db


# =============================================================================
# 1. ZERO-UI MODE - Kontextové zobrazení
# =============================================================================

class ZeroUIEngine:
    """
    Systém zobrazuje jen to, co je v daném kontextu nutné.
    Žádné menu, žádné moduly, žádné přepínání.
    """
    
    # Kontextové priority
    CONTEXT_WEIGHTS = {
        'critical_alert': 100,
        'deadline_today': 90,
        'my_tasks': 80,
        'team_issues': 70,
        'upcoming_work': 60,
        'general_info': 30
    }
    
    def __init__(self, db):
        self.db = db
    
    def get_contextual_view(self, user_id: int, role: str, 
                           location: str = None, 
                           current_time: datetime = None) -> Dict:
        """
        Vrať pouze relevantní informace pro daný kontext.
        Zero-UI = zobraz jen to nutné.
        """
        if current_time is None:
            current_time = datetime.now()
        
        context = {
            'user_id': user_id,
            'role': role,
            'location': location,
            'time': current_time.isoformat(),
            'time_of_day': self._get_time_of_day(current_time),
            'is_work_hours': self._is_work_hours(current_time),
            'primary_focus': None,
            'widgets': [],
            'actions': []
        }
        
        # Determine primary focus based on context
        focus_items = []
        
        # 1. Critical alerts first
        criticals = self._get_critical_alerts(user_id, role)
        if criticals:
            focus_items.append({
                'type': 'critical_alert',
                'weight': self.CONTEXT_WEIGHTS['critical_alert'],
                'data': criticals
            })
        
        # 2. Today's deadlines
        deadlines = self._get_today_deadlines(user_id, role)
        if deadlines:
            focus_items.append({
                'type': 'deadline_today',
                'weight': self.CONTEXT_WEIGHTS['deadline_today'],
                'data': deadlines
            })
        
        # 3. My tasks for today
        my_tasks = self._get_my_tasks_today(user_id, current_time.date())
        if my_tasks:
            focus_items.append({
                'type': 'my_tasks',
                'weight': self.CONTEXT_WEIGHTS['my_tasks'],
                'data': my_tasks
            })
        
        # 4. Location-based context
        if location:
            location_data = self._get_location_context(location)
            if location_data:
                focus_items.append({
                    'type': 'location_context',
                    'weight': 85,  # High priority
                    'data': location_data
                })
        
        # 5. Role-based priorities
        role_data = self._get_role_priorities(role, current_time)
        if role_data:
            focus_items.append({
                'type': 'role_priority',
                'weight': 65,
                'data': role_data
            })
        
        # Sort by weight and take top items
        focus_items.sort(key=lambda x: -x['weight'])
        
        # Set primary focus
        if focus_items:
            context['primary_focus'] = focus_items[0]
            context['widgets'] = self._generate_widgets(focus_items[:5])
            context['actions'] = self._generate_quick_actions(focus_items[0], role)
        
        return context
    
    def _get_time_of_day(self, dt: datetime) -> str:
        hour = dt.hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _is_work_hours(self, dt: datetime) -> bool:
        return dt.weekday() < 5 and 7 <= dt.hour < 18
    
    def _get_critical_alerts(self, user_id: int, role: str) -> List[Dict]:
        try:
            # Get active critical insights
            alerts = self.db.execute('''
                SELECT * FROM ai_insights 
                WHERE severity = 'CRITICAL' 
                AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 5
            ''').fetchall()
            return [dict(a) for a in alerts] if alerts else []
        except:
            return []
    
    def _get_today_deadlines(self, user_id: int, role: str) -> List[Dict]:
        try:
            today = datetime.now().date().isoformat()
            tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
            
            jobs = self.db.execute('''
                SELECT id, client, name, planned_end_date, progress
                FROM jobs
                WHERE planned_end_date BETWEEN ? AND ?
                AND status NOT IN ('Dokončeno', 'completed', 'archived')
            ''', (today, tomorrow)).fetchall()
            
            return [dict(j) for j in jobs] if jobs else []
        except:
            return []
    
    def _get_my_tasks_today(self, user_id: int, date) -> List[Dict]:
        try:
            tasks = self.db.execute('''
                SELECT t.id, t.title, t.status, t.priority, j.client
                FROM tasks t
                LEFT JOIN jobs j ON j.id = t.job_id
                WHERE t.assigned_to = ?
                AND t.status NOT IN ('done', 'completed')
                ORDER BY t.priority DESC, t.deadline ASC
                LIMIT 10
            ''', (user_id,)).fetchall()
            
            return [dict(t) for t in tasks] if tasks else []
        except:
            return []
    
    def _get_location_context(self, location: str) -> Dict:
        """Kontext podle lokace (GPS nebo název)"""
        try:
            # Check if near warehouse
            if 'sklad' in location.lower() or 'warehouse' in location.lower():
                low_stock = self.db.execute('''
                    SELECT COUNT(*) as cnt FROM inventory
                    WHERE quantity <= min_quantity AND min_quantity > 0
                ''').fetchone()
                
                return {
                    'location_type': 'warehouse',
                    'low_stock_items': low_stock['cnt'] if low_stock else 0,
                    'suggested_action': 'check_inventory'
                }
            
            # Check if at job site
            job = self.db.execute('''
                SELECT id, client, name, city, address
                FROM jobs
                WHERE city LIKE ? OR address LIKE ?
                AND status NOT IN ('Dokončeno', 'completed', 'archived')
                LIMIT 1
            ''', (f'%{location}%', f'%{location}%')).fetchone()
            
            if job:
                return {
                    'location_type': 'job_site',
                    'job_id': job['id'],
                    'client': job['client'],
                    'suggested_action': 'show_job_tasks'
                }
            
            return None
        except:
            return None
    
    def _get_role_priorities(self, role: str, current_time: datetime) -> Dict:
        """Priority podle role"""
        priorities = {
            'owner': ['finance_overview', 'critical_jobs', 'team_performance'],
            'manager': ['team_workload', 'deadlines', 'resource_allocation'],
            'team_lead': ['team_tasks', 'daily_plan', 'material_needs'],
            'worker': ['my_tasks', 'timesheet', 'job_instructions']
        }
        
        return {
            'role': role,
            'focus_areas': priorities.get(role, ['my_tasks']),
            'time_context': self._get_time_of_day(current_time)
        }
    
    def _generate_widgets(self, focus_items: List[Dict]) -> List[Dict]:
        """Generuj minimalistické widgety"""
        widgets = []
        
        for item in focus_items:
            widget = {
                'type': item['type'],
                'priority': item['weight'],
                'compact': True
            }
            
            if item['type'] == 'critical_alert':
                widget['display'] = 'alert_banner'
                widget['count'] = len(item['data'])
            elif item['type'] == 'my_tasks':
                widget['display'] = 'task_list'
                widget['count'] = len(item['data'])
            elif item['type'] == 'deadline_today':
                widget['display'] = 'deadline_card'
                widget['count'] = len(item['data'])
            else:
                widget['display'] = 'info_card'
            
            widgets.append(widget)
        
        return widgets
    
    def _generate_quick_actions(self, primary_focus: Dict, role: str) -> List[Dict]:
        """Generuj rychlé akce podle kontextu"""
        actions = []
        
        focus_type = primary_focus['type']
        
        if focus_type == 'critical_alert':
            actions.append({'action': 'view_alerts', 'label': 'Zobrazit varování', 'primary': True})
            actions.append({'action': 'snooze_all', 'label': 'Odložit vše'})
        
        elif focus_type == 'my_tasks':
            actions.append({'action': 'start_work', 'label': 'Začít práci', 'primary': True})
            actions.append({'action': 'log_time', 'label': 'Zapsat čas'})
        
        elif focus_type == 'deadline_today':
            actions.append({'action': 'view_job', 'label': 'Detail zakázky', 'primary': True})
            actions.append({'action': 'request_help', 'label': 'Požádat o pomoc'})
        
        elif focus_type == 'location_context':
            data = primary_focus['data']
            if data.get('location_type') == 'warehouse':
                actions.append({'action': 'inventory_check', 'label': 'Kontrola skladu', 'primary': True})
            elif data.get('location_type') == 'job_site':
                actions.append({'action': 'view_job', 'label': 'Zobrazit zakázku', 'primary': True})
                actions.append({'action': 'log_arrival', 'label': 'Zapsat příjezd'})
        
        return actions


# =============================================================================
# 2. CONTEXTUAL INTELLIGENCE FIELD
# =============================================================================

class ContextualIntelligenceField:
    """
    Inteligence reaguje na lokaci, čas a roli uživatele.
    Vytváří "pole" kolem uživatele.
    """
    
    def __init__(self, db):
        self.db = db
    
    def calculate_field(self, user_id: int, 
                       gps_lat: float = None, gps_lon: float = None,
                       role: str = None) -> Dict:
        """Vypočítej inteligentní pole kolem uživatele"""
        
        field = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'layers': []
        }
        
        # Layer 1: Temporal (čas)
        field['layers'].append(self._temporal_layer())
        
        # Layer 2: Spatial (prostor)
        if gps_lat and gps_lon:
            field['layers'].append(self._spatial_layer(gps_lat, gps_lon))
        
        # Layer 3: Role-based
        if role:
            field['layers'].append(self._role_layer(role))
        
        # Layer 4: Relational (vztahy)
        field['layers'].append(self._relational_layer(user_id))
        
        # Layer 5: Activity (aktivita)
        field['layers'].append(self._activity_layer(user_id))
        
        # Calculate field intensity
        field['intensity'] = self._calculate_intensity(field['layers'])
        field['recommended_mode'] = self._recommend_mode(field)
        
        return field
    
    def _temporal_layer(self) -> Dict:
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()
        
        urgency = 'low'
        if 8 <= hour <= 10:  # Morning rush
            urgency = 'high'
        elif 14 <= hour <= 16:  # Afternoon peak
            urgency = 'medium'
        
        return {
            'type': 'temporal',
            'hour': hour,
            'weekday': weekday,
            'is_weekend': weekday >= 5,
            'urgency': urgency,
            'time_pressure': self._calculate_time_pressure()
        }
    
    def _spatial_layer(self, lat: float, lon: float) -> Dict:
        # Simplified - would use real GPS matching
        return {
            'type': 'spatial',
            'lat': lat,
            'lon': lon,
            'detected_location': 'unknown',  # Would match against job sites
            'nearby_jobs': [],
            'distance_to_nearest': None
        }
    
    def _role_layer(self, role: str) -> Dict:
        role_configs = {
            'owner': {'scope': 'global', 'detail_level': 'summary', 'decision_authority': 'full'},
            'manager': {'scope': 'department', 'detail_level': 'detailed', 'decision_authority': 'high'},
            'team_lead': {'scope': 'team', 'detail_level': 'operational', 'decision_authority': 'medium'},
            'worker': {'scope': 'personal', 'detail_level': 'task', 'decision_authority': 'low'}
        }
        
        config = role_configs.get(role, role_configs['worker'])
        config['type'] = 'role'
        config['role'] = role
        
        return config
    
    def _relational_layer(self, user_id: int) -> Dict:
        try:
            # Get team members
            team = self.db.execute('''
                SELECT COUNT(*) as cnt FROM employees
                WHERE status = 'active' AND id != ?
            ''', (user_id,)).fetchone()
            
            return {
                'type': 'relational',
                'team_size': team['cnt'] if team else 0,
                'collaboration_mode': 'team' if team and team['cnt'] > 0 else 'solo'
            }
        except:
            return {'type': 'relational', 'team_size': 0}
    
    def _activity_layer(self, user_id: int) -> Dict:
        try:
            # Recent activity
            recent = self.db.execute('''
                SELECT COUNT(*) as cnt FROM timesheets
                WHERE employee_id = ? AND date >= date('now', '-7 days')
            ''', (user_id,)).fetchone()
            
            return {
                'type': 'activity',
                'recent_entries': recent['cnt'] if recent else 0,
                'activity_level': 'high' if recent and recent['cnt'] > 5 else 'low'
            }
        except:
            return {'type': 'activity', 'activity_level': 'unknown'}
    
    def _calculate_time_pressure(self) -> float:
        """Vypočítej časový tlak (0-100)"""
        try:
            today = datetime.now().date().isoformat()
            
            # Count today's deadlines
            deadlines = self.db.execute('''
                SELECT COUNT(*) as cnt FROM jobs
                WHERE planned_end_date = ?
                AND status NOT IN ('Dokončeno', 'completed')
            ''', (today,)).fetchone()
            
            # Count overdue tasks
            overdue = self.db.execute('''
                SELECT COUNT(*) as cnt FROM tasks
                WHERE deadline < ? AND status NOT IN ('done', 'completed')
            ''', (today,)).fetchone()
            
            pressure = 0
            pressure += (deadlines['cnt'] or 0) * 20
            pressure += (overdue['cnt'] or 0) * 10
            
            return min(100, pressure)
        except:
            return 0
    
    def _calculate_intensity(self, layers: List[Dict]) -> float:
        """Vypočítej intenzitu pole"""
        intensity = 50  # Base
        
        for layer in layers:
            if layer.get('urgency') == 'high':
                intensity += 20
            elif layer.get('urgency') == 'medium':
                intensity += 10
            
            if layer.get('time_pressure', 0) > 50:
                intensity += 15
            
            if layer.get('activity_level') == 'high':
                intensity += 10
        
        return min(100, intensity)
    
    def _recommend_mode(self, field: Dict) -> str:
        """Doporuč režim zobrazení"""
        intensity = field.get('intensity', 50)
        
        if intensity > 80:
            return 'focus'  # Minimální UI, jen kritické
        elif intensity > 60:
            return 'active'  # Aktivní práce
        elif intensity > 40:
            return 'normal'  # Standardní zobrazení
        else:
            return 'relaxed'  # Rozšířené možnosti


# =============================================================================
# 3. SELF-ORGANIZING WORK
# =============================================================================

class SelfOrganizingWork:
    """
    Práce se sama přerozděluje podle reality.
    Nemoc, počasí, materiál, kapacita → automatická reorganizace.
    """
    
    def __init__(self, db):
        self.db = db
    
    def detect_disruptions(self) -> List[Dict]:
        """Detekuj narušení plánu"""
        disruptions = []
        today = datetime.now().date()
        
        # 1. Absence zaměstnanců
        try:
            # Workers with assignments but marked absent
            absent = self.db.execute('''
                SELECT DISTINCT pa.employee_id, e.name, pa.job_id, pa.date
                FROM planning_assignments pa
                JOIN employees e ON e.id = pa.employee_id
                WHERE pa.date >= ?
                AND e.status = 'absent'
            ''', (today.isoformat(),)).fetchall()
            
            for a in absent:
                disruptions.append({
                    'type': 'absence',
                    'severity': 'high',
                    'employee_id': a['employee_id'],
                    'employee_name': a['name'],
                    'affected_job': a['job_id'],
                    'date': a['date'],
                    'requires_reorg': True
                })
        except:
            pass
        
        # 2. Chybějící materiál
        try:
            missing = self.db.execute('''
                SELECT wr.job_id, j.client, i.name as material, 
                       wr.quantity as needed, i.quantity as available
                FROM warehouse_reservations wr
                JOIN jobs j ON j.id = wr.job_id
                JOIN inventory i ON i.id = wr.inventory_id
                WHERE wr.quantity > i.quantity
                AND j.status NOT IN ('Dokončeno', 'completed', 'archived')
            ''').fetchall()
            
            for m in missing:
                disruptions.append({
                    'type': 'material_shortage',
                    'severity': 'medium',
                    'job_id': m['job_id'],
                    'client': m['client'],
                    'material': m['material'],
                    'shortage': m['needed'] - m['available'],
                    'requires_reorg': True
                })
        except:
            pass
        
        # 3. Přetížení kapacity
        try:
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            
            overloaded = self.db.execute('''
                SELECT e.id, e.name, SUM(COALESCE(pa.planned_hours, 8)) as total_hours
                FROM employees e
                JOIN planning_assignments pa ON pa.employee_id = e.id
                WHERE pa.date BETWEEN ? AND ?
                GROUP BY e.id
                HAVING total_hours > 45
            ''', (week_start.isoformat(), week_end.isoformat())).fetchall()
            
            for o in overloaded:
                disruptions.append({
                    'type': 'capacity_overload',
                    'severity': 'medium',
                    'employee_id': o['id'],
                    'employee_name': o['name'],
                    'hours': o['total_hours'],
                    'requires_reorg': True
                })
        except:
            pass
        
        return disruptions
    
    def generate_reorganization_plan(self, disruptions: List[Dict]) -> Dict:
        """Generuj plán reorganizace"""
        plan = {
            'generated_at': datetime.now().isoformat(),
            'disruptions_count': len(disruptions),
            'proposals': [],
            'impact_summary': {}
        }
        
        for disruption in disruptions:
            proposal = self._create_proposal(disruption)
            if proposal:
                plan['proposals'].append(proposal)
        
        # Calculate impact
        plan['impact_summary'] = {
            'jobs_affected': len(set(p.get('job_id') for p in plan['proposals'] if p.get('job_id'))),
            'workers_reassigned': len(set(p.get('new_worker_id') for p in plan['proposals'] if p.get('new_worker_id'))),
            'estimated_delay_days': sum(p.get('delay_days', 0) for p in plan['proposals'])
        }
        
        return plan
    
    def _create_proposal(self, disruption: Dict) -> Optional[Dict]:
        """Vytvoř návrh řešení disruption"""
        
        if disruption['type'] == 'absence':
            # Find replacement worker
            replacement = self._find_replacement_worker(
                disruption.get('affected_job'),
                disruption.get('date')
            )
            
            if replacement:
                return {
                    'type': 'reassign_worker',
                    'reason': f"Absence: {disruption['employee_name']}",
                    'job_id': disruption.get('affected_job'),
                    'original_worker_id': disruption['employee_id'],
                    'new_worker_id': replacement['id'],
                    'new_worker_name': replacement['name'],
                    'confidence': replacement.get('score', 70),
                    'delay_days': 0
                }
            else:
                return {
                    'type': 'reschedule',
                    'reason': f"Absence: {disruption['employee_name']}, náhrada nedostupná",
                    'job_id': disruption.get('affected_job'),
                    'delay_days': 1,
                    'confidence': 50
                }
        
        elif disruption['type'] == 'material_shortage':
            return {
                'type': 'reorder_material',
                'reason': f"Chybí materiál: {disruption['material']}",
                'job_id': disruption['job_id'],
                'material': disruption['material'],
                'quantity_needed': disruption['shortage'],
                'suggested_action': 'create_purchase_order',
                'delay_days': 2,  # Estimate
                'confidence': 80
            }
        
        elif disruption['type'] == 'capacity_overload':
            return {
                'type': 'redistribute_work',
                'reason': f"Přetížení: {disruption['employee_name']} ({disruption['hours']}h)",
                'employee_id': disruption['employee_id'],
                'suggested_action': 'balance_workload',
                'hours_to_redistribute': disruption['hours'] - 45,
                'confidence': 60
            }
        
        return None
    
    def _find_replacement_worker(self, job_id: int, date: str) -> Optional[Dict]:
        """Najdi náhradního pracovníka"""
        try:
            # Find available workers not assigned on that date
            available = self.db.execute('''
                SELECT e.id, e.name, e.skills
                FROM employees e
                WHERE e.status = 'active'
                AND e.id NOT IN (
                    SELECT employee_id FROM planning_assignments
                    WHERE date = ?
                )
                LIMIT 1
            ''', (date,)).fetchone()
            
            if available:
                return {
                    'id': available['id'],
                    'name': available['name'],
                    'score': 75
                }
            
            return None
        except:
            return None


# =============================================================================
# 4. DECISION SHADOW
# =============================================================================

class DecisionShadow:
    """
    Každé rozhodnutí má digitální stín:
    kdo, proč, kontext, dopad.
    Vzniká psychologie organizace.
    """
    
    def __init__(self, db):
        self.db = db
        self._ensure_table()
    
    def _ensure_table(self):
        try:
            self.db.execute('''
                CREATE TABLE IF NOT EXISTS decision_shadows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_type TEXT NOT NULL,
                    decision_maker_id INTEGER,
                    decision_maker_role TEXT,
                    context_snapshot TEXT,
                    alternatives_considered TEXT,
                    chosen_option TEXT,
                    reasoning TEXT,
                    emotional_state TEXT,
                    time_pressure_level INTEGER,
                    confidence_level INTEGER,
                    expected_outcome TEXT,
                    actual_outcome TEXT,
                    outcome_variance TEXT,
                    lessons TEXT,
                    entity_type TEXT,
                    entity_id INTEGER,
                    created_at TEXT NOT NULL,
                    outcome_recorded_at TEXT
                )
            ''')
            self.db.commit()
        except:
            pass
    
    def cast_shadow(self, decision_type: str, decision_maker_id: int,
                   chosen_option: str, reasoning: str,
                   context: Dict = None, alternatives: List[str] = None,
                   confidence: int = 70, time_pressure: int = 50,
                   entity_type: str = None, entity_id: int = None) -> int:
        """Vytvoř stín rozhodnutí"""
        try:
            cursor = self.db.execute('''
                INSERT INTO decision_shadows
                (decision_type, decision_maker_id, context_snapshot, 
                 alternatives_considered, chosen_option, reasoning,
                 confidence_level, time_pressure_level,
                 entity_type, entity_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision_type,
                decision_maker_id,
                json.dumps(context) if context else None,
                json.dumps(alternatives) if alternatives else None,
                chosen_option,
                reasoning,
                confidence,
                time_pressure,
                entity_type,
                entity_id,
                datetime.now().isoformat()
            ))
            self.db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Cast shadow error: {e}")
            return None
    
    def record_outcome(self, shadow_id: int, actual_outcome: str, lessons: str = None) -> bool:
        """Zaznamenej výsledek rozhodnutí"""
        try:
            # Get expected outcome
            shadow = self.db.execute(
                'SELECT expected_outcome FROM decision_shadows WHERE id = ?',
                (shadow_id,)
            ).fetchone()
            
            variance = None
            if shadow and shadow['expected_outcome']:
                variance = self._calculate_variance(shadow['expected_outcome'], actual_outcome)
            
            self.db.execute('''
                UPDATE decision_shadows
                SET actual_outcome = ?, outcome_variance = ?, lessons = ?,
                    outcome_recorded_at = ?
                WHERE id = ?
            ''', (actual_outcome, variance, lessons, datetime.now().isoformat(), shadow_id))
            self.db.commit()
            return True
        except Exception as e:
            print(f"Record outcome error: {e}")
            return False
    
    def _calculate_variance(self, expected: str, actual: str) -> str:
        """Vypočítej odchylku od očekávání"""
        # Simplified - could use NLP for better comparison
        if expected.lower() == actual.lower():
            return 'match'
        elif 'success' in actual.lower() and 'success' in expected.lower():
            return 'partial_match'
        else:
            return 'deviation'
    
    def get_decision_patterns(self, decision_maker_id: int = None) -> Dict:
        """Analyzuj vzorce rozhodování"""
        try:
            query = '''
                SELECT decision_type, 
                       COUNT(*) as total,
                       AVG(confidence_level) as avg_confidence,
                       AVG(time_pressure_level) as avg_time_pressure,
                       SUM(CASE WHEN outcome_variance = 'match' THEN 1 ELSE 0 END) as good_outcomes
                FROM decision_shadows
                WHERE actual_outcome IS NOT NULL
            '''
            params = []
            
            if decision_maker_id:
                query += ' AND decision_maker_id = ?'
                params.append(decision_maker_id)
            
            query += ' GROUP BY decision_type'
            
            patterns = self.db.execute(query, params).fetchall()
            
            return {
                'patterns': [dict(p) for p in patterns],
                'total_decisions': sum(p['total'] for p in patterns) if patterns else 0,
                'overall_accuracy': self._calculate_accuracy(patterns)
            }
        except Exception as e:
            print(f"Decision patterns error: {e}")
            return {'patterns': [], 'total_decisions': 0}
    
    def _calculate_accuracy(self, patterns: List) -> float:
        if not patterns:
            return 0
        
        total = sum(p['total'] for p in patterns)
        good = sum(p['good_outcomes'] or 0 for p in patterns)
        
        return (good / total * 100) if total > 0 else 0
    
    def get_organizational_psychology(self) -> Dict:
        """Získej psychologii organizace z rozhodnutí"""
        try:
            # Average confidence
            confidence = self.db.execute('''
                SELECT AVG(confidence_level) as avg FROM decision_shadows
            ''').fetchone()
            
            # Average time pressure
            pressure = self.db.execute('''
                SELECT AVG(time_pressure_level) as avg FROM decision_shadows
            ''').fetchone()
            
            # Decision speed (time from context to decision)
            speed = self.db.execute('''
                SELECT decision_type, COUNT(*) as cnt
                FROM decision_shadows
                GROUP BY decision_type
                ORDER BY cnt DESC
            ''').fetchall()
            
            # Risk tolerance (based on confidence in uncertain decisions)
            
            return {
                'average_confidence': confidence['avg'] if confidence else 50,
                'average_time_pressure': pressure['avg'] if pressure else 50,
                'top_decision_types': [dict(s) for s in speed[:5]] if speed else [],
                'profile': self._calculate_profile(confidence, pressure)
            }
        except Exception as e:
            print(f"Org psychology error: {e}")
            return {}
    
    def _calculate_profile(self, confidence, pressure) -> str:
        """Určí profil rozhodování"""
        conf = confidence['avg'] if confidence and confidence['avg'] else 50
        pres = pressure['avg'] if pressure and pressure['avg'] else 50
        
        if conf > 70 and pres < 40:
            return 'confident_methodical'
        elif conf > 70 and pres > 60:
            return 'confident_fast'
        elif conf < 40 and pres > 60:
            return 'reactive_stressed'
        elif conf < 40 and pres < 40:
            return 'cautious_deliberate'
        else:
            return 'balanced'


# =============================================================================
# 5. PROBABILITY VISUALIZATION
# =============================================================================

class ProbabilityVisualization:
    """
    Budoucnost jako mapa pravděpodobností, rizik a trajektorií.
    """
    
    def __init__(self, db):
        self.db = db
    
    def generate_probability_map(self, entity_type: str, entity_id: int,
                                 horizon_days: int = 30) -> Dict:
        """Generuj mapu pravděpodobností"""
        
        if entity_type == 'job':
            return self._job_probability_map(entity_id, horizon_days)
        elif entity_type == 'project':
            return self._project_probability_map(entity_id, horizon_days)
        else:
            return {'error': 'Unknown entity type'}
    
    def _job_probability_map(self, job_id: int, horizon_days: int) -> Dict:
        """Mapa pravděpodobností pro zakázku"""
        try:
            job = self.db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
            
            if not job:
                return {'error': 'Job not found'}
            
            today = datetime.now().date()
            
            # Calculate trajectories
            trajectories = []
            
            # Optimistic trajectory
            trajectories.append({
                'name': 'optimistic',
                'probability': 0.2,
                'completion_date': self._calculate_completion_date(job, 0.8),
                'final_cost_multiplier': 0.95,
                'assumptions': ['Žádné komplikace', 'Materiál dostupný', 'Tým plně funkční']
            })
            
            # Realistic trajectory
            trajectories.append({
                'name': 'realistic',
                'probability': 0.6,
                'completion_date': self._calculate_completion_date(job, 1.0),
                'final_cost_multiplier': 1.05,
                'assumptions': ['Běžné komplikace', 'Mírná zpoždění materiálu']
            })
            
            # Pessimistic trajectory
            trajectories.append({
                'name': 'pessimistic',
                'probability': 0.2,
                'completion_date': self._calculate_completion_date(job, 1.3),
                'final_cost_multiplier': 1.2,
                'assumptions': ['Významné komplikace', 'Zpoždění materiálu', 'Kapacitní problémy']
            })
            
            # Risk points
            risks = self._identify_risk_points(job)
            
            return {
                'job_id': job_id,
                'client': job['client'],
                'current_progress': job['progress'] or 0,
                'trajectories': trajectories,
                'risk_points': risks,
                'confidence_interval': {
                    'lower': trajectories[0]['completion_date'],
                    'upper': trajectories[2]['completion_date']
                },
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Job probability map error: {e}")
            return {'error': str(e)}
    
    def _calculate_completion_date(self, job: Dict, factor: float) -> str:
        """Vypočítej datum dokončení"""
        if job['planned_end_date']:
            planned = datetime.strptime(job['planned_end_date'], '%Y-%m-%d').date()
            today = datetime.now().date()
            
            remaining_days = (planned - today).days
            adjusted_days = int(remaining_days * factor)
            
            completion = today + timedelta(days=max(0, adjusted_days))
            return completion.isoformat()
        
        return (datetime.now().date() + timedelta(days=30)).isoformat()
    
    def _identify_risk_points(self, job: Dict) -> List[Dict]:
        """Identifikuj rizikové body"""
        risks = []
        
        progress = job['progress'] or 0
        
        # Budget risk
        if job['estimated_value'] and job['actual_value']:
            budget_usage = job['actual_value'] / job['estimated_value']
            if budget_usage > 0.8 and progress < 80:
                risks.append({
                    'type': 'budget',
                    'severity': 'high' if budget_usage > 1 else 'medium',
                    'description': f'Rozpočet na {budget_usage*100:.0f}% při {progress}% progresu',
                    'probability': 0.7 if budget_usage > 1 else 0.4
                })
        
        # Deadline risk
        if job['planned_end_date']:
            deadline = datetime.strptime(job['planned_end_date'], '%Y-%m-%d').date()
            days_left = (deadline - datetime.now().date()).days
            
            if days_left < 7 and progress < 80:
                risks.append({
                    'type': 'deadline',
                    'severity': 'high',
                    'description': f'{days_left} dní do deadline, progress {progress}%',
                    'probability': 0.8
                })
        
        return risks
    
    def _project_probability_map(self, project_id: int, horizon_days: int) -> Dict:
        """Mapa pravděpodobností pro projekt (skupina zakázek)"""
        # Placeholder for project-level analysis
        return {'project_id': project_id, 'message': 'Not implemented yet'}


# =============================================================================
# 6. REALITY SIMULATION ENGINE
# =============================================================================

class RealitySimulationEngine:
    """
    Simulace budoucnosti firmy před implementací změn.
    "Co kdyby" scénáře.
    """
    
    def __init__(self, db):
        self.db = db
    
    def simulate_scenario(self, scenario: Dict) -> Dict:
        """Spusť simulaci scénáře"""
        
        scenario_type = scenario.get('type')
        
        if scenario_type == 'add_worker':
            return self._simulate_add_worker(scenario)
        elif scenario_type == 'remove_job':
            return self._simulate_remove_job(scenario)
        elif scenario_type == 'change_deadline':
            return self._simulate_change_deadline(scenario)
        elif scenario_type == 'capacity_change':
            return self._simulate_capacity_change(scenario)
        else:
            return {'error': f'Unknown scenario type: {scenario_type}'}
    
    def _simulate_add_worker(self, scenario: Dict) -> Dict:
        """Simuluj přidání pracovníka"""
        try:
            # Current state
            current_capacity = self.db.execute('''
                SELECT COUNT(*) as workers, 
                       SUM(COALESCE(pa.planned_hours, 0)) as planned_hours
                FROM employees e
                LEFT JOIN planning_assignments pa ON pa.employee_id = e.id
                    AND pa.date >= date('now')
                WHERE e.status = 'active'
            ''').fetchone()
            
            # Simulate adding one worker
            new_capacity = (current_capacity['workers'] or 0) + 1
            hours_per_week = 40
            
            # Calculate impact
            pending_hours = self.db.execute('''
                SELECT SUM(estimated_hours - COALESCE(actual_hours, 0)) as pending
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived')
            ''').fetchone()
            
            pending = pending_hours['pending'] or 0
            
            weeks_current = pending / ((current_capacity['workers'] or 1) * hours_per_week)
            weeks_new = pending / (new_capacity * hours_per_week)
            
            return {
                'scenario': 'add_worker',
                'current_state': {
                    'workers': current_capacity['workers'] or 0,
                    'pending_hours': pending,
                    'weeks_to_complete': round(weeks_current, 1)
                },
                'simulated_state': {
                    'workers': new_capacity,
                    'weeks_to_complete': round(weeks_new, 1),
                    'time_saved_weeks': round(weeks_current - weeks_new, 1)
                },
                'recommendation': 'beneficial' if (weeks_current - weeks_new) > 2 else 'marginal'
            }
        except Exception as e:
            print(f"Simulate add worker error: {e}")
            return {'error': str(e)}
    
    def _simulate_change_deadline(self, scenario: Dict) -> Dict:
        """Simuluj změnu deadline"""
        job_id = scenario.get('job_id')
        new_deadline = scenario.get('new_deadline')
        
        try:
            job = self.db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
            
            if not job:
                return {'error': 'Job not found'}
            
            old_deadline = job['planned_end_date']
            
            # Calculate impacts
            if old_deadline and new_deadline:
                old_date = datetime.strptime(old_deadline, '%Y-%m-%d').date()
                new_date = datetime.strptime(new_deadline, '%Y-%m-%d').date()
                days_change = (new_date - old_date).days
                
                return {
                    'scenario': 'change_deadline',
                    'job_id': job_id,
                    'client': job['client'],
                    'old_deadline': old_deadline,
                    'new_deadline': new_deadline,
                    'days_change': days_change,
                    'impacts': {
                        'schedule_pressure': 'reduced' if days_change > 0 else 'increased',
                        'resource_flexibility': 'more' if days_change > 0 else 'less',
                        'client_relationship': 'may need communication' if days_change > 7 else 'minimal'
                    }
                }
            
            return {'error': 'Missing deadline data'}
        except Exception as e:
            print(f"Simulate deadline change error: {e}")
            return {'error': str(e)}
    
    def _simulate_remove_job(self, scenario: Dict) -> Dict:
        """Simuluj odebrání zakázky"""
        job_id = scenario.get('job_id')
        
        try:
            job = self.db.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
            
            if not job:
                return {'error': 'Job not found'}
            
            # Calculate freed resources
            assignments = self.db.execute('''
                SELECT COUNT(*) as cnt, SUM(COALESCE(planned_hours, 8)) as hours
                FROM planning_assignments
                WHERE job_id = ? AND date >= date('now')
            ''', (job_id,)).fetchone()
            
            return {
                'scenario': 'remove_job',
                'job_id': job_id,
                'client': job['client'],
                'freed_resources': {
                    'assignments': assignments['cnt'] or 0,
                    'hours': assignments['hours'] or 0
                },
                'revenue_impact': -(job['estimated_value'] or 0),
                'impacts': {
                    'capacity': 'freed',
                    'revenue': 'reduced',
                    'team_utilization': 'to_be_reallocated'
                }
            }
        except Exception as e:
            print(f"Simulate remove job error: {e}")
            return {'error': str(e)}
    
    def _simulate_capacity_change(self, scenario: Dict) -> Dict:
        """Simuluj změnu kapacity"""
        change_pct = scenario.get('change_percent', 0)  # e.g., -20 for 20% reduction
        
        try:
            # Current workload
            current = self.db.execute('''
                SELECT COUNT(DISTINCT employee_id) as workers,
                       SUM(COALESCE(planned_hours, 8)) as total_hours
                FROM planning_assignments
                WHERE date BETWEEN date('now') AND date('now', '+30 days')
            ''').fetchone()
            
            new_capacity = (current['workers'] or 1) * (1 + change_pct/100)
            
            return {
                'scenario': 'capacity_change',
                'change_percent': change_pct,
                'current_state': {
                    'workers': current['workers'] or 0,
                    'planned_hours_30d': current['total_hours'] or 0
                },
                'simulated_state': {
                    'effective_workers': round(new_capacity, 1),
                    'capacity_hours_30d': round(new_capacity * 40 * 4, 0)  # 4 weeks
                },
                'stress_level': 'high' if change_pct < -10 else 'normal'
            }
        except Exception as e:
            print(f"Simulate capacity change error: {e}")
            return {'error': str(e)}
    
    def compare_scenarios(self, scenarios: List[Dict]) -> Dict:
        """Porovnej více scénářů"""
        results = []
        
        for scenario in scenarios:
            result = self.simulate_scenario(scenario)
            result['scenario_input'] = scenario
            results.append(result)
        
        # Rank by benefit
        # Simplified ranking
        return {
            'scenarios_compared': len(results),
            'results': results,
            'recommendation': results[0] if results else None
        }


# =============================================================================
# 7. TIME-LAYERED VIEW
# =============================================================================

class TimeLayeredView:
    """
    Zobrazení více časových vrstev současně:
    dnes, týden, měsíc, minulost, predikce.
    """
    
    def __init__(self, db):
        self.db = db
    
    def get_layered_view(self, entity_type: str = 'company', 
                        entity_id: int = None) -> Dict:
        """Získej vícevrstvý pohled"""
        
        view = {
            'generated_at': datetime.now().isoformat(),
            'layers': {}
        }
        
        # Layer: TODAY
        view['layers']['today'] = self._today_layer(entity_type, entity_id)
        
        # Layer: THIS WEEK
        view['layers']['week'] = self._week_layer(entity_type, entity_id)
        
        # Layer: THIS MONTH
        view['layers']['month'] = self._month_layer(entity_type, entity_id)
        
        # Layer: PAST (last 30 days trends)
        view['layers']['past'] = self._past_layer(entity_type, entity_id)
        
        # Layer: FUTURE (predictions)
        view['layers']['future'] = self._future_layer(entity_type, entity_id)
        
        return view
    
    def _today_layer(self, entity_type: str, entity_id: int) -> Dict:
        today = datetime.now().date().isoformat()
        
        try:
            # Today's work
            work = self.db.execute('''
                SELECT COUNT(DISTINCT pa.employee_id) as workers,
                       COUNT(DISTINCT pa.job_id) as active_jobs,
                       SUM(COALESCE(pa.planned_hours, 8)) as planned_hours
                FROM planning_assignments pa
                WHERE pa.date = ?
            ''', (today,)).fetchone()
            
            # Today's logged hours
            logged = self.db.execute('''
                SELECT SUM(hours) as hours FROM timesheets WHERE date = ?
            ''', (today,)).fetchone()
            
            return {
                'date': today,
                'workers_active': work['workers'] or 0,
                'jobs_active': work['active_jobs'] or 0,
                'planned_hours': work['planned_hours'] or 0,
                'logged_hours': logged['hours'] or 0,
                'status': 'in_progress' if datetime.now().hour < 17 else 'closing'
            }
        except:
            return {'date': today}
    
    def _week_layer(self, entity_type: str, entity_id: int) -> Dict:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        try:
            work = self.db.execute('''
                SELECT COUNT(DISTINCT pa.employee_id) as workers,
                       COUNT(DISTINCT pa.job_id) as jobs,
                       SUM(COALESCE(pa.planned_hours, 8)) as planned
                FROM planning_assignments pa
                WHERE pa.date BETWEEN ? AND ?
            ''', (week_start.isoformat(), week_end.isoformat())).fetchone()
            
            logged = self.db.execute('''
                SELECT SUM(hours) as hours FROM timesheets
                WHERE date BETWEEN ? AND ?
            ''', (week_start.isoformat(), week_end.isoformat())).fetchone()
            
            return {
                'start': week_start.isoformat(),
                'end': week_end.isoformat(),
                'planned_hours': work['planned'] or 0,
                'logged_hours': logged['hours'] or 0,
                'jobs_count': work['jobs'] or 0,
                'utilization': round((logged['hours'] or 0) / (work['planned'] or 1) * 100, 1)
            }
        except:
            return {'start': week_start.isoformat()}
    
    def _month_layer(self, entity_type: str, entity_id: int) -> Dict:
        today = datetime.now().date()
        month_start = today.replace(day=1)
        
        try:
            # Jobs this month
            jobs = self.db.execute('''
                SELECT COUNT(*) as started,
                       SUM(CASE WHEN status IN ('Dokončeno', 'completed') THEN 1 ELSE 0 END) as completed
                FROM jobs
                WHERE start_date >= ?
            ''', (month_start.isoformat(),)).fetchone()
            
            # Revenue
            revenue = self.db.execute('''
                SELECT SUM(actual_value) as revenue
                FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND completed_at >= ?
            ''', (month_start.isoformat(),)).fetchone()
            
            return {
                'month_start': month_start.isoformat(),
                'jobs_started': jobs['started'] or 0,
                'jobs_completed': jobs['completed'] or 0,
                'revenue': revenue['revenue'] or 0
            }
        except:
            return {'month_start': month_start.isoformat()}
    
    def _past_layer(self, entity_type: str, entity_id: int) -> Dict:
        """Trendy za posledních 30 dní"""
        past_30 = (datetime.now().date() - timedelta(days=30)).isoformat()
        
        try:
            # Completed jobs
            completed = self.db.execute('''
                SELECT COUNT(*) as cnt, SUM(actual_value) as value
                FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND completed_at >= ?
            ''', (past_30,)).fetchone()
            
            # Hours worked
            hours = self.db.execute('''
                SELECT SUM(hours) as total FROM timesheets WHERE date >= ?
            ''', (past_30,)).fetchone()
            
            return {
                'period': 'last_30_days',
                'jobs_completed': completed['cnt'] or 0,
                'revenue': completed['value'] or 0,
                'hours_worked': hours['total'] or 0,
                'avg_job_value': (completed['value'] or 0) / (completed['cnt'] or 1)
            }
        except:
            return {'period': 'last_30_days'}
    
    def _future_layer(self, entity_type: str, entity_id: int) -> Dict:
        """Predikce na příštích 30 dní"""
        today = datetime.now().date()
        future_30 = (today + timedelta(days=30)).isoformat()
        
        try:
            # Upcoming deadlines
            deadlines = self.db.execute('''
                SELECT COUNT(*) as cnt
                FROM jobs
                WHERE planned_end_date BETWEEN ? AND ?
                AND status NOT IN ('Dokončeno', 'completed', 'archived')
            ''', (today.isoformat(), future_30)).fetchone()
            
            # Planned work
            planned = self.db.execute('''
                SELECT SUM(COALESCE(planned_hours, 8)) as hours
                FROM planning_assignments
                WHERE date BETWEEN ? AND ?
            ''', (today.isoformat(), future_30)).fetchone()
            
            # Predicted revenue (from active jobs)
            predicted = self.db.execute('''
                SELECT SUM(estimated_value - COALESCE(actual_value, 0)) as remaining
                FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived')
                AND planned_end_date <= ?
            ''', (future_30,)).fetchone()
            
            return {
                'period': 'next_30_days',
                'deadlines_count': deadlines['cnt'] or 0,
                'planned_hours': planned['hours'] or 0,
                'predicted_revenue': predicted['remaining'] or 0,
                'confidence': 'medium'
            }
        except:
            return {'period': 'next_30_days'}


# =============================================================================
# 8. DIGITAL ENERGY MAP
# =============================================================================

class DigitalEnergyMap:
    """
    Mapa toku práce, zdrojů, pozornosti a rozhodnutí.
    Jedna vizualizace zdraví organizace.
    """
    
    def __init__(self, db):
        self.db = db
    
    def generate_energy_map(self) -> Dict:
        """Generuj mapu energie organizace"""
        
        energy_map = {
            'generated_at': datetime.now().isoformat(),
            'overall_health': 0,
            'flows': [],
            'hotspots': [],
            'coldspots': [],
            'dimensions': {}
        }
        
        # Dimension: Work Flow
        energy_map['dimensions']['work'] = self._measure_work_energy()
        
        # Dimension: Resource Flow
        energy_map['dimensions']['resources'] = self._measure_resource_energy()
        
        # Dimension: Decision Flow
        energy_map['dimensions']['decisions'] = self._measure_decision_energy()
        
        # Dimension: Team Energy
        energy_map['dimensions']['team'] = self._measure_team_energy()
        
        # Dimension: Financial Energy
        energy_map['dimensions']['financial'] = self._measure_financial_energy()
        
        # Calculate overall health
        dimensions = energy_map['dimensions']
        scores = [d.get('score', 50) for d in dimensions.values() if isinstance(d, dict)]
        energy_map['overall_health'] = sum(scores) / len(scores) if scores else 50
        
        # Identify hotspots and coldspots
        energy_map['hotspots'] = self._find_hotspots(dimensions)
        energy_map['coldspots'] = self._find_coldspots(dimensions)
        
        return energy_map
    
    def _measure_work_energy(self) -> Dict:
        """Měř energii práce"""
        try:
            today = datetime.now().date()
            
            # Active jobs
            active = self.db.execute('''
                SELECT COUNT(*) as cnt FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived', 'cancelled')
            ''').fetchone()
            
            # Progress this week
            progress = self.db.execute('''
                SELECT AVG(progress) as avg FROM jobs
                WHERE status NOT IN ('Dokončeno', 'completed', 'archived')
            ''').fetchone()
            
            # Completed this month
            month_start = today.replace(day=1)
            completed = self.db.execute('''
                SELECT COUNT(*) as cnt FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND completed_at >= ?
            ''', (month_start.isoformat(),)).fetchone()
            
            score = 50
            if (progress['avg'] or 0) > 50:
                score += 20
            if (completed['cnt'] or 0) > 5:
                score += 15
            if (active['cnt'] or 0) > 0:
                score += 15
            
            return {
                'score': min(100, score),
                'active_jobs': active['cnt'] or 0,
                'avg_progress': round(progress['avg'] or 0, 1),
                'completed_this_month': completed['cnt'] or 0,
                'status': 'healthy' if score > 70 else 'moderate' if score > 40 else 'low'
            }
        except:
            return {'score': 50, 'status': 'unknown'}
    
    def _measure_resource_energy(self) -> Dict:
        """Měř energii zdrojů"""
        try:
            # Low stock items
            low = self.db.execute('''
                SELECT COUNT(*) as cnt FROM inventory
                WHERE quantity <= min_quantity AND min_quantity > 0
            ''').fetchone()
            
            # Total items
            total = self.db.execute('SELECT COUNT(*) as cnt FROM inventory').fetchone()
            
            # Reservations vs stock
            over_reserved = self.db.execute('''
                SELECT COUNT(*) as cnt
                FROM warehouse_reservations wr
                JOIN inventory i ON i.id = wr.inventory_id
                WHERE wr.quantity > i.quantity
            ''').fetchone()
            
            score = 100
            score -= (low['cnt'] or 0) * 5
            score -= (over_reserved['cnt'] or 0) * 10
            
            return {
                'score': max(0, min(100, score)),
                'low_stock_items': low['cnt'] or 0,
                'total_items': total['cnt'] or 0,
                'over_reserved': over_reserved['cnt'] or 0,
                'status': 'healthy' if score > 70 else 'warning' if score > 40 else 'critical'
            }
        except:
            return {'score': 50, 'status': 'unknown'}
    
    def _measure_decision_energy(self) -> Dict:
        """Měř energii rozhodování"""
        try:
            # Pending decisions/drafts
            pending = self.db.execute('''
                SELECT COUNT(*) as cnt FROM ai_action_drafts
                WHERE status = 'pending'
            ''').fetchone()
            
            # Recent decisions
            recent = self.db.execute('''
                SELECT COUNT(*) as cnt FROM ai_learning_log
                WHERE created_at >= date('now', '-7 days')
            ''').fetchone()
            
            score = 70
            if (pending['cnt'] or 0) > 10:
                score -= 20  # Too many pending = bottleneck
            if (recent['cnt'] or 0) > 5:
                score += 15  # Active decision making
            
            return {
                'score': max(0, min(100, score)),
                'pending_decisions': pending['cnt'] or 0,
                'decisions_this_week': recent['cnt'] or 0,
                'status': 'healthy' if score > 70 else 'moderate' if score > 40 else 'bottleneck'
            }
        except:
            return {'score': 50, 'status': 'unknown'}
    
    def _measure_team_energy(self) -> Dict:
        """Měř energii týmu"""
        try:
            # Active workers
            active = self.db.execute('''
                SELECT COUNT(*) as cnt FROM employees WHERE status = 'active'
            ''').fetchone()
            
            # Hours this week
            week_start = (datetime.now().date() - timedelta(days=datetime.now().weekday())).isoformat()
            hours = self.db.execute('''
                SELECT SUM(hours) as total, COUNT(DISTINCT employee_id) as workers
                FROM timesheets
                WHERE date >= ?
            ''', (week_start,)).fetchone()
            
            avg_hours = (hours['total'] or 0) / (hours['workers'] or 1)
            
            score = 70
            if 30 <= avg_hours <= 45:
                score += 20  # Good utilization
            elif avg_hours > 50:
                score -= 15  # Overworked
            elif avg_hours < 20:
                score -= 10  # Underutilized
            
            return {
                'score': max(0, min(100, score)),
                'active_workers': active['cnt'] or 0,
                'avg_hours_this_week': round(avg_hours, 1),
                'status': 'healthy' if score > 70 else 'stressed' if avg_hours > 45 else 'underutilized'
            }
        except:
            return {'score': 50, 'status': 'unknown'}
    
    def _measure_financial_energy(self) -> Dict:
        """Měř finanční energii"""
        try:
            # Revenue this month
            month_start = datetime.now().date().replace(day=1).isoformat()
            
            revenue = self.db.execute('''
                SELECT SUM(actual_value) as total
                FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND completed_at >= ?
            ''', (month_start,)).fetchone()
            
            # Pending invoices
            pending = self.db.execute('''
                SELECT SUM(actual_value) as total
                FROM jobs
                WHERE status IN ('Dokončeno', 'completed')
                AND (invoiced = 0 OR invoiced IS NULL)
            ''').fetchone()
            
            score = 60
            if (revenue['total'] or 0) > 100000:
                score += 25
            elif (revenue['total'] or 0) > 50000:
                score += 15
            
            if (pending['total'] or 0) > 50000:
                score -= 15  # Money stuck
            
            return {
                'score': max(0, min(100, score)),
                'revenue_this_month': revenue['total'] or 0,
                'pending_invoices': pending['total'] or 0,
                'status': 'healthy' if score > 70 else 'moderate' if score > 40 else 'concerning'
            }
        except:
            return {'score': 50, 'status': 'unknown'}
    
    def _find_hotspots(self, dimensions: Dict) -> List[Dict]:
        """Najdi hotspoty (vysoká aktivita/energie)"""
        hotspots = []
        
        for name, dim in dimensions.items():
            if isinstance(dim, dict) and dim.get('score', 0) > 80:
                hotspots.append({
                    'dimension': name,
                    'score': dim['score'],
                    'reason': 'high_energy'
                })
        
        return hotspots
    
    def _find_coldspots(self, dimensions: Dict) -> List[Dict]:
        """Najdi coldspoty (nízká energie/problémy)"""
        coldspots = []
        
        for name, dim in dimensions.items():
            if isinstance(dim, dict) and dim.get('score', 100) < 40:
                coldspots.append({
                    'dimension': name,
                    'score': dim['score'],
                    'reason': 'needs_attention'
                })
        
        return coldspots


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'ZeroUIEngine',
    'ContextualIntelligenceField',
    'SelfOrganizingWork',
    'DecisionShadow',
    'ProbabilityVisualization',
    'RealitySimulationEngine',
    'TimeLayeredView',
    'DigitalEnergyMap'
]
