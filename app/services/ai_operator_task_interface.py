from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter
import json

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import services directly
import sys
import os
import importlib.util

_dependency_graph_path = os.path.join(os.path.dirname(__file__), 'dependency_graph_service.py')
spec = importlib.util.spec_from_file_location("dependency_graph_service", _dependency_graph_path)
dependency_graph_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dependency_graph_module)
DependencyGraphService = dependency_graph_module.DependencyGraphService

_risk_propagation_path = os.path.join(os.path.dirname(__file__), 'risk_propagation_service.py')
spec = importlib.util.spec_from_file_location("risk_propagation_service", _risk_propagation_path)
risk_propagation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(risk_propagation_module)
RiskPropagationService = risk_propagation_module.RiskPropagationService

_task_event_service_path = os.path.join(os.path.dirname(__file__), 'task_event_service.py')
spec = importlib.util.spec_from_file_location("task_event_service", _task_event_service_path)
event_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_service_module)
TaskEventService = event_service_module.TaskEventService

_task_integrity_service_path = os.path.join(os.path.dirname(__file__), 'task_integrity_service.py')
spec = importlib.util.spec_from_file_location("task_integrity_service", _task_integrity_service_path)
integrity_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity_service_module)
TaskIntegrityService = integrity_service_module.TaskIntegrityService

_aggregated_integrity_path = os.path.join(os.path.dirname(__file__), 'aggregated_integrity_service.py')
spec = importlib.util.spec_from_file_location("aggregated_integrity_service", _aggregated_integrity_path)
aggregated_integrity_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aggregated_integrity_module)
AggregatedIntegrityService = aggregated_integrity_module.AggregatedIntegrityService


class AIOperatorTaskInterface:
    """
    Hlavní interface pro AI Operátora.
    Poskytuje strukturovaná data pro analýzu a rozhodování.
    """
    
    # === SITUAČNÍ REPORTY ===
    
    @staticmethod
    def get_job_situation_report(job_id: int) -> Dict:
        """
        Kompletní situační report zakázky pro AI analýzu.
        Toto je hlavní vstupní bod pro AI rozhodování o zakázce.
        """
        db = get_db()
        
        # Get job
        job_row = db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not job_row:
            return {'error': 'Job not found'}
        
        job = dict(job_row)
        
        # Get tasks
        tasks_rows = db.execute("SELECT * FROM tasks WHERE job_id = ?", (job_id,)).fetchall()
        tasks = [dict(t) for t in tasks_rows]
        
        # === JOB META ===
        job_meta = {
            'job_id': job_id,
            'name': job.get('name', f'Job #{job_id}'),
            'deadline': job.get('deadline'),
            'status': job.get('status', 'unknown'),
            'report_generated_at': datetime.utcnow().isoformat()
        }
        
        # === TASK OVERVIEW ===
        status_counts = Counter(t.get('status', 'planned') for t in tasks)
        task_overview = {
            'total': len(tasks),
            'completed': status_counts.get('completed', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'blocked': status_counts.get('blocked', 0),
            'pending': status_counts.get('planned', 0) + status_counts.get('assigned', 0),
            'failed': status_counts.get('failed', 0),
            'completion_percentage': round(status_counts.get('completed', 0) / len(tasks) * 100, 1) if tasks else 0
        }
        
        # === INTEGRITY SUMMARY ===
        try:
            integrity_data = AggregatedIntegrityService.job_integrity_score(job_id)
            integrity_summary = {
                'average_score': integrity_data.get('average_score'),
                'ai_trust_level': integrity_data.get('ai_trust_level'),
                'critical_count': len(integrity_data.get('critical_tasks', [])),
                'trend': 'stable',  # Simplified
                'distribution': integrity_data.get('distribution', {})
            }
        except:
            integrity_summary = {
                'average_score': None,
                'ai_trust_level': None,
                'critical_count': 0,
                'trend': 'unknown',
                'distribution': {}
            }
        
        # === ACTIVE BLOCKS ===
        blocked_tasks = [t for t in tasks if t.get('status') == 'blocked']
        active_blocks = []
        for bt in blocked_tasks:
            try:
                # Find block event
                block_events = TaskEventService.get_task_history(
                    bt['id'],
                    event_types=['task_blocked', 'task_blocked_material', 'task_blocked_weather'],
                    limit=1
                )
                
                downstream = DependencyGraphService.get_downstream_tasks(bt['id'])
                
                block_event = block_events[0] if block_events else None
                payload = block_event.payload if block_event and hasattr(block_event, 'payload') else {}
                
                active_blocks.append({
                    'task_id': bt['id'],
                    'task_title': bt.get('title', 'Unknown'),
                    'blocked_since': block_event.occurred_at.isoformat() if block_event and hasattr(block_event, 'occurred_at') else None,
                    'block_type': payload.get('block_type') if payload else 'unknown',
                    'block_reason': payload.get('block_reason') if payload else None,
                    'downstream_impact': {
                        'affected_tasks': len(downstream),
                        'critical_path_affected': any(d.get('is_critical') for d in downstream)
                    }
                })
            except:
                pass
        
        # === CRITICAL PATH STATUS ===
        try:
            topo_order = DependencyGraphService.topological_sort(job_id)
            critical_path_data = {
                'critical_path': topo_order or [],
                'task_count': len(topo_order) if topo_order else 0,
                'total_duration_hours': 0  # Simplified
            }
        except:
            critical_path_data = {
                'critical_path': [],
                'task_count': 0,
                'total_duration_hours': 0
            }
        
        # Check critical path delays
        critical_delays = []
        if critical_path_data['critical_path']:
            for task_id in critical_path_data['critical_path'][:10]:  # Limit to first 10
                task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                if task_row:
                    task = dict(task_row)
                    if task.get('status') == 'in_progress' and task.get('planned_end'):
                        try:
                            planned_end_str = task.get('planned_end')
                            if isinstance(planned_end_str, str):
                                planned_end = datetime.fromisoformat(planned_end_str.replace('Z', '+00:00'))
                            else:
                                planned_end = planned_end_str
                            
                            if datetime.utcnow() > planned_end:
                                delay = int((datetime.utcnow() - planned_end).total_seconds() / 60)
                                critical_delays.append({'task_id': task_id, 'delay_minutes': delay})
                        except:
                            pass
        
        critical_path_status = {
            'total_duration_hours': critical_path_data.get('total_duration_hours', 0),
            'task_count': critical_path_data.get('task_count', 0),
            'on_track': len(critical_delays) == 0,
            'current_delays': critical_delays,
            'bottleneck_task_id': critical_delays[0]['task_id'] if critical_delays else None,
            'deadline_at_risk': len(critical_delays) > 0 and sum(d['delay_minutes'] for d in critical_delays) > 120
        }
        
        # === DEVIATION PATTERNS ===
        try:
            deviation_patterns = AIOperatorTaskInterface.analyze_deviation_patterns(
                scope={'job_id': job_id},
                min_occurrences=2
            )
        except:
            deviation_patterns = []
        
        # === RESOURCE TENSIONS ===
        try:
            resource_tensions = AIOperatorTaskInterface._detect_resource_tensions(job_id, tasks)
        except:
            resource_tensions = []
        
        # === RECENT EVENTS ===
        try:
            recent_events = TaskEventService.get_job_event_stream(job_id, limit=20)
            recent_events_summary = []
            for e in recent_events:
                event_type = e.event_type if hasattr(e, 'event_type') else str(e)
                occurred_at = e.occurred_at if hasattr(e, 'occurred_at') else datetime.utcnow()
                if isinstance(occurred_at, str):
                    occurred_at = datetime.fromisoformat(occurred_at.replace('Z', '+00:00'))
                
                recent_events_summary.append({
                    'event_type': event_type,
                    'task_id': e.task_id if hasattr(e, 'task_id') else None,
                    'occurred_at': occurred_at.isoformat(),
                    'severity': AIOperatorTaskInterface._classify_event_severity(event_type)
                })
        except:
            recent_events_summary = []
        
        # === AI ATTENTION REQUIRED ===
        ai_attention = []
        
        # Critical integrity
        if integrity_summary.get('critical_count', 0) > 0:
            ai_attention.append({
                'priority': 'high',
                'type': 'integrity_crisis',
                'detail': f"{integrity_summary['critical_count']} tasks with critical integrity",
                'suggested_action': 'Review and fix data quality issues'
            })
        
        # Blocked tasks
        if len(active_blocks) > 0:
            ai_attention.append({
                'priority': 'high',
                'type': 'blocked_tasks',
                'detail': f"{len(active_blocks)} tasks blocked",
                'suggested_action': 'Resolve blockers or find workarounds'
            })
        
        # Deadline risk
        if critical_path_status.get('deadline_at_risk'):
            ai_attention.append({
                'priority': 'critical',
                'type': 'deadline_risk',
                'detail': 'Critical path delays threatening deadline',
                'suggested_action': 'Immediate escalation and replanning required'
            })
        
        # Declining integrity
        if integrity_summary.get('trend') == 'declining':
            ai_attention.append({
                'priority': 'medium',
                'type': 'integrity_trend',
                'detail': 'Data quality is declining',
                'suggested_action': 'Investigate causes and enforce data entry standards'
            })
        
        return {
            'job_meta': job_meta,
            'task_overview': task_overview,
            'integrity_summary': integrity_summary,
            'active_blocks': active_blocks,
            'critical_path_status': critical_path_status,
            'deviation_patterns': deviation_patterns[:5],  # Top 5
            'resource_tensions': resource_tensions,
            'recent_events': recent_events_summary,
            'ai_attention_required': sorted(ai_attention, key=lambda x: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(x['priority'], 4))
        }
    
    @staticmethod
    def get_employee_performance_context(employee_id: int, days: int = 30) -> Dict:
        """
        Kontext výkonu zaměstnance pro AI analýzu.
        NEHODNOTÍ člověka - hodnotí vzorce pro optimalizaci.
        """
        db = get_db()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        tasks_rows = db.execute("""
            SELECT * FROM tasks 
            WHERE assigned_employee_id = ? AND created_at >= ?
        """, (employee_id, since)).fetchall()
        
        tasks = [dict(t) for t in tasks_rows]
        completed_tasks = [t for t in tasks if t.get('status') in ['completed', 'partial']]
        
        # === TASK STATISTICS ===
        task_statistics = {
            'total_assigned': len(tasks),
            'completed': len(completed_tasks),
            'completion_rate': round(len(completed_tasks) / len(tasks) * 100, 1) if tasks else 0,
            'average_integrity': round(sum(t.get('integrity_score', 100) or 100 for t in completed_tasks) / len(completed_tasks), 1) if completed_tasks else None,
            'blocked_count': sum(1 for t in tasks if t.get('status') == 'blocked'),
            'failed_count': sum(1 for t in tasks if t.get('status') == 'failed')
        }
        
        # === TIME PATTERNS ===
        time_deviations = [t.get('time_deviation_minutes') for t in completed_tasks if t.get('time_deviation_minutes') is not None]
        
        # Analyze by hour of day
        hour_performance = {}
        for t in completed_tasks:
            actual_start_str = t.get('actual_start')
            if actual_start_str:
                try:
                    if isinstance(actual_start_str, str):
                        actual_start = datetime.fromisoformat(actual_start_str.replace('Z', '+00:00'))
                    else:
                        actual_start = actual_start_str
                    
                    hour = actual_start.hour
                    if hour not in hour_performance:
                        hour_performance[hour] = []
                    if t.get('time_deviation_minutes') is not None:
                        hour_performance[hour].append(t.get('time_deviation_minutes'))
                except:
                    pass
        
        best_hours = []
        worst_hours = []
        for hour, deviations in hour_performance.items():
            avg = sum(deviations) / len(deviations) if deviations else 0
            if avg < 0:  # Faster than planned
                best_hours.append({'hour': hour, 'avg_deviation': avg})
            elif avg > 30:  # Significantly slower
                worst_hours.append({'hour': hour, 'avg_deviation': avg})
        
        time_patterns = {
            'average_deviation_minutes': round(sum(time_deviations) / len(time_deviations), 1) if time_deviations else 0,
            'best_performance_hours': sorted(best_hours, key=lambda x: x['avg_deviation'])[:3],
            'worst_performance_hours': sorted(worst_hours, key=lambda x: x['avg_deviation'], reverse=True)[:3],
            'on_time_percentage': round(sum(1 for d in time_deviations if abs(d) <= 15) / len(time_deviations) * 100, 1) if time_deviations else 0
        }
        
        # === TASK TYPE AFFINITY ===
        type_stats = {}
        for t in completed_tasks:
            task_type = t.get('task_type', 'work')
            if task_type not in type_stats:
                type_stats[task_type] = {'count': 0, 'total_deviation': 0, 'total_integrity': 0}
            type_stats[task_type]['count'] += 1
            type_stats[task_type]['total_deviation'] += t.get('time_deviation_minutes', 0) or 0
            type_stats[task_type]['total_integrity'] += t.get('integrity_score', 100) or 100
        
        task_type_affinity = []
        for task_type, stats in type_stats.items():
            task_type_affinity.append({
                'task_type': task_type,
                'count': stats['count'],
                'avg_time_deviation': round(stats['total_deviation'] / stats['count'], 1),
                'avg_integrity': round(stats['total_integrity'] / stats['count'], 1),
                'efficiency_score': 100 - abs(stats['total_deviation'] / stats['count'])  # Simplified
            })
        
        task_type_affinity.sort(key=lambda x: x['efficiency_score'], reverse=True)
        
        # === EVIDENCE QUALITY ===
        evidence_counts = []
        for t in completed_tasks:
            task_id = t['id']
            count = db.execute("SELECT COUNT(*) FROM task_evidence WHERE task_id = ?", (task_id,)).fetchone()[0]
            evidence_counts.append(count)
        
        # Check for photos
        tasks_with_photo = 0
        for t in completed_tasks:
            task_id = t['id']
            photo_count = db.execute("SELECT COUNT(*) FROM task_evidence WHERE task_id = ? AND evidence_type = 'photo'", (task_id,)).fetchone()[0]
            if photo_count > 0:
                tasks_with_photo += 1
        
        evidence_quality = {
            'average_evidence_per_task': round(sum(evidence_counts) / len(evidence_counts), 1) if evidence_counts else 0,
            'tasks_without_evidence': sum(1 for c in evidence_counts if c == 0),
            'tasks_with_photo': tasks_with_photo
        }
        
        # === SYSTEM RECOMMENDATIONS ===
        recommendations = []
        
        if time_patterns.get('worst_performance_hours'):
            worst_hour = time_patterns['worst_performance_hours'][0]['hour']
            recommendations.append({
                'type': 'scheduling_optimization',
                'recommendation': f'Avoid scheduling complex tasks at {worst_hour}:00',
                'confidence': 0.7
            })
        
        if task_type_affinity:
            best_type = task_type_affinity[0]['task_type']
            recommendations.append({
                'type': 'task_assignment',
                'recommendation': f'Employee excels at {best_type} tasks',
                'confidence': 0.8
            })
        
        if evidence_quality.get('tasks_without_evidence', 0) > len(completed_tasks) * 0.3:
            recommendations.append({
                'type': 'process_improvement',
                'recommendation': 'Encourage more evidence capture',
                'confidence': 0.9
            })
        
        return {
            'employee_id': employee_id,
            'analysis_period_days': days,
            'task_statistics': task_statistics,
            'time_patterns': time_patterns,
            'task_type_affinity': task_type_affinity,
            'evidence_quality': evidence_quality,
            'system_recommendations': recommendations
        }
    
    # === DETECTION METHODS ===
    
    @staticmethod
    def detect_bottlenecks(scope: Dict = None) -> List[Dict]:
        """
        Detekuje úzká hrdla v systému.
        scope = {'job_id': int} nebo {'all': True}
        """
        db = get_db()
        bottlenecks = []
        
        if scope and scope.get('job_id'):
            job_ids = [scope['job_id']]
        else:
            # Active jobs
            jobs_rows = db.execute("SELECT id FROM jobs WHERE status = 'active'").fetchall()
            job_ids = [j[0] for j in jobs_rows] if jobs_rows else []
        
        for job_id in job_ids:
            tasks_rows = db.execute("SELECT * FROM tasks WHERE job_id = ?", (job_id,)).fetchall()
            tasks = [dict(t) for t in tasks_rows]
            
            # === RESOURCE BOTTLENECKS ===
            employee_loads = Counter(t.get('assigned_employee_id') for t in tasks if t.get('status') in ['in_progress', 'assigned'])
            for emp_id, count in employee_loads.items():
                if count >= 5:  # Threshold
                    bottlenecks.append({
                        'type': 'resource',
                        'subtype': 'employee_overload',
                        'severity': 'high' if count >= 7 else 'medium',
                        'entity_type': 'employee',
                        'entity_id': emp_id,
                        'job_id': job_id,
                        'detail': f'Employee has {count} active tasks',
                        'impact_assessment': f'Risk of delays and quality issues',
                        'resolution_options': [
                            {'action': 'Reassign tasks', 'effort': 'medium', 'time_saved_hours': count * 0.5},
                            {'action': 'Add support worker', 'effort': 'high', 'time_saved_hours': count * 1}
                        ]
                    })
            
            # === DEPENDENCY BOTTLENECKS ===
            for task in tasks:
                if task.get('status') not in ['completed', 'cancelled']:
                    try:
                        downstream = DependencyGraphService.get_downstream_tasks(task['id'])
                        if len(downstream) >= 3:
                            bottlenecks.append({
                                'type': 'dependency',
                                'subtype': 'blocking_task',
                                'severity': 'critical' if len(downstream) >= 5 else 'high',
                                'entity_type': 'task',
                                'entity_id': task['id'],
                                'job_id': job_id,
                                'detail': f'Task "{task.get("title", "Unknown")}" blocks {len(downstream)} other tasks',
                                'impact_assessment': f'Cascade delay risk',
                                'resolution_options': [
                                    {'action': 'Prioritize this task', 'effort': 'low', 'time_saved_hours': len(downstream) * 0.5},
                                    {'action': 'Find parallel path', 'effort': 'high', 'time_saved_hours': len(downstream) * 1}
                                ]
                            })
                    except:
                        pass
            
            # === MATERIAL BOTTLENECKS ===
            blocked_by_material = [t for t in tasks if t.get('status') == 'blocked']
            for bt in blocked_by_material:
                try:
                    events = TaskEventService.get_task_history(bt['id'], event_types=['task_blocked_material'], limit=1)
                    if events:
                        event = events[0]
                        payload = event.payload if hasattr(event, 'payload') else {}
                        
                        bottlenecks.append({
                            'type': 'material',
                            'subtype': 'shortage',
                            'severity': 'high',
                            'entity_type': 'task',
                            'entity_id': bt['id'],
                            'job_id': job_id,
                            'detail': f'Task blocked by material shortage',
                            'material_id': payload.get('blocking_entity_id'),
                            'impact_assessment': 'Work stoppage',
                            'resolution_options': [
                                {'action': 'Express order', 'effort': 'medium', 'time_saved_hours': 4},
                                {'action': 'Find substitute', 'effort': 'low', 'time_saved_hours': 2}
                            ]
                        })
                except:
                    pass
        
        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        bottlenecks.sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return bottlenecks
    
    @staticmethod
    def analyze_deviation_patterns(scope: Dict, min_occurrences: int = 3) -> List[Dict]:
        """
        Analyzuje opakující se vzorce odchylek.
        """
        db = get_db()
        since = (datetime.utcnow() - timedelta(days=90)).isoformat()
        
        query = "SELECT * FROM task_events WHERE occurred_at >= ? AND event_type IN (?, ?, ?, ?, ?, ?)"
        params = [
            since,
            'task_deviation_time',
            'task_deviation_material',
            'task_blocked',
            'task_blocked_material',
            'task_blocked_weather',
            'task_failed'
        ]
        
        if scope.get('job_id'):
            query += " AND job_id = ?"
            params.append(scope['job_id'])
        if scope.get('employee_id'):
            query += " AND employee_id = ?"
            params.append(scope['employee_id'])
        
        events_rows = db.execute(query, params).fetchall()
        
        # Group by type and reason
        patterns = {}
        for event_row in events_rows:
            event = dict(event_row)
            event_type = event.get('event_type', '')
            payload_str = event.get('payload', '{}')
            
            try:
                payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
            except:
                payload = {}
            
            reason = payload.get('reason_category') or payload.get('block_type') or event_type
            key = f"{event_type}:{reason}"
            
            if key not in patterns:
                patterns[key] = {
                    'event_type': event_type,
                    'reason': reason,
                    'occurrences': [],
                    'task_ids': set(),
                    'total_impact_minutes': 0
                }
            
            patterns[key]['occurrences'].append(event)
            patterns[key]['task_ids'].add(event.get('task_id'))
            
            # Impact
            if payload.get('deviation_minutes'):
                patterns[key]['total_impact_minutes'] += abs(payload['deviation_minutes'])
            elif payload.get('delay_minutes'):
                patterns[key]['total_impact_minutes'] += payload['delay_minutes']
        
        # Filter and format
        result = []
        for key, data in patterns.items():
            if len(data['occurrences']) >= min_occurrences:
                result.append({
                    'pattern_type': data['event_type'],
                    'reason': data['reason'],
                    'occurrence_count': len(data['occurrences']),
                    'affected_tasks': len(data['task_ids']),
                    'total_impact_hours': round(data['total_impact_minutes'] / 60, 1),
                    'confidence': min(0.95, 0.5 + len(data['occurrences']) * 0.1),
                    'sample_task_ids': list(data['task_ids'])[:5],
                    'root_cause_hypothesis': AIOperatorTaskInterface._hypothesize_root_cause(data),
                    'recommended_actions': AIOperatorTaskInterface._suggest_pattern_actions(data)
                })
        
        result.sort(key=lambda x: x['occurrence_count'], reverse=True)
        return result
    
    @staticmethod
    def generate_daily_briefing(date: datetime = None) -> Dict:
        """
        Generuje denní briefing pro management.
        """
        db = get_db()
        
        if not date:
            date = datetime.utcnow()
        
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = date.replace(hour=23, minute=59, second=59)
        
        # Today's tasks
        todays_tasks_rows = db.execute("""
            SELECT * FROM tasks 
            WHERE planned_start >= ? AND planned_start <= ? AND status != 'cancelled'
        """, (day_start.isoformat(), day_end.isoformat())).fetchall()
        
        todays_tasks = [dict(t) for t in todays_tasks_rows]
        
        # Yesterday's incomplete
        yesterday = day_start - timedelta(days=1)
        carryover_rows = db.execute("""
            SELECT * FROM tasks 
            WHERE planned_end < ? AND status IN ('planned', 'assigned', 'in_progress', 'blocked')
        """, (day_start.isoformat(),)).fetchall()
        
        carryover = [dict(t) for t in carryover_rows]
        
        # System integrity
        try:
            system_integrity = AggregatedIntegrityService.system_integrity_dashboard()
        except:
            system_integrity = {'average_score': None, 'distribution_percentage': {}}
        
        # Bottlenecks
        bottlenecks = AIOperatorTaskInterface.detect_bottlenecks({'all': True})
        critical_bottlenecks = [b for b in bottlenecks if b['severity'] == 'critical']
        
        # Executive summary
        summary_parts = []
        summary_parts.append(f"{len(todays_tasks)} tasks scheduled for today.")
        
        if carryover:
            summary_parts.append(f"⚠️ {len(carryover)} tasks carried over from previous days.")
        
        if system_integrity.get('average_score') and system_integrity['average_score'] < 70:
            summary_parts.append(f"⚠️ System data quality needs attention (avg: {system_integrity['average_score']}).")
        
        if critical_bottlenecks:
            summary_parts.append(f"🚨 {len(critical_bottlenecks)} critical bottlenecks require immediate attention.")
        
        # Attention items
        attention_items = []
        
        for task in carryover[:5]:
            planned_end_str = task.get('planned_end')
            planned_end_display = planned_end_str[:10] if planned_end_str else 'unknown'
            attention_items.append({
                'priority': 'high',
                'title': f'Overdue: {task.get("title", "Unknown")}',
                'detail': f'Was due {planned_end_display}',
                'recommended_action': 'Reschedule or escalate'
            })
        
        for bn in critical_bottlenecks[:3]:
            attention_items.append({
                'priority': 'critical',
                'title': f'Bottleneck: {bn["detail"]}',
                'detail': bn['impact_assessment'],
                'recommended_action': bn['resolution_options'][0]['action'] if bn.get('resolution_options') else 'Review'
            })
        
        # Resource warnings
        employee_loads = Counter(t.get('assigned_employee_id') for t in todays_tasks)
        overloaded = [(emp_id, count) for emp_id, count in employee_loads.items() if count > 8]
        
        resource_warnings = []
        for emp_id, count in overloaded:
            resource_warnings.append({
                'employee_id': emp_id,
                'task_count': count,
                'warning': 'Overloaded - consider redistribution'
            })
        
        return {
            'date': date.strftime('%Y-%m-%d'),
            'generated_at': datetime.utcnow().isoformat(),
            'executive_summary': ' '.join(summary_parts),
            'todays_schedule': {
                'total_tasks': len(todays_tasks),
                'by_status': dict(Counter(t.get('status', 'planned') for t in todays_tasks)),
                'by_priority': dict(Counter(t.get('priority', 'normal') for t in todays_tasks))
            },
            'carryover_tasks': len(carryover),
            'attention_items': sorted(attention_items, key=lambda x: {'critical': 0, 'high': 1, 'medium': 2}.get(x['priority'], 3)),
            'resource_warnings': resource_warnings,
            'integrity_status': {
                'average': system_integrity.get('average_score'),
                'critical_percentage': system_integrity.get('distribution_percentage', {}).get('critical', 0) + 
                                      system_integrity.get('distribution_percentage', {}).get('failed', 0)
            },
            'bottleneck_count': len(bottlenecks),
            'critical_bottleneck_count': len(critical_bottlenecks)
        }
    
    # === HELPER METHODS ===
    
    @staticmethod
    def _detect_resource_tensions(job_id: int, tasks: List[Dict]) -> List[Dict]:
        """Detekuje napětí v přidělení zdrojů."""
        tensions = []
        
        # Time conflicts - same person, overlapping tasks
        by_employee = {}
        for task in tasks:
            if task.get('status') not in ['completed', 'cancelled', 'failed']:
                emp_id = task.get('assigned_employee_id')
                if emp_id:
                    if emp_id not in by_employee:
                        by_employee[emp_id] = []
                    by_employee[emp_id].append(task)
        
        for emp_id, emp_tasks in by_employee.items():
            # Check overlaps
            for i, t1 in enumerate(emp_tasks):
                for t2 in emp_tasks[i+1:]:
                    t1_start = t1.get('planned_start')
                    t1_end = t1.get('planned_end')
                    t2_start = t2.get('planned_start')
                    t2_end = t2.get('planned_end')
                    
                    if t1_start and t1_end and t2_start and t2_end:
                        try:
                            if isinstance(t1_start, str):
                                t1_start_dt = datetime.fromisoformat(t1_start.replace('Z', '+00:00'))
                                t1_end_dt = datetime.fromisoformat(t1_end.replace('Z', '+00:00'))
                                t2_start_dt = datetime.fromisoformat(t2_start.replace('Z', '+00:00'))
                                t2_end_dt = datetime.fromisoformat(t2_end.replace('Z', '+00:00'))
                            else:
                                t1_start_dt = t1_start
                                t1_end_dt = t1_end
                                t2_start_dt = t2_start
                                t2_end_dt = t2_end
                            
                            # Overlap check
                            if t1_start_dt < t2_end_dt and t2_start_dt < t1_end_dt:
                                tensions.append({
                                    'type': 'time_conflict',
                                    'employee_id': emp_id,
                                    'task1_id': t1['id'],
                                    'task2_id': t2['id'],
                                    'overlap_period': 'Overlapping schedules',
                                    'resolution': 'Reschedule one task or reassign'
                                })
                        except:
                            pass
        
        return tensions[:10]  # Max 10
    
    @staticmethod
    def _classify_event_severity(event_type: str) -> str:
        """Klasifikuje závažnost event typu."""
        critical = ['task_failed', 'task_integrity_critical', 'task_blocked']
        high = ['task_blocked_material', 'task_blocked_weather', 'task_deviation_time']
        medium = ['task_deviation_material', 'task_workaround_used', 'task_rescheduled']
        
        if event_type in critical:
            return 'critical'
        elif event_type in high:
            return 'high'
        elif event_type in medium:
            return 'medium'
        return 'low'
    
    @staticmethod
    def _hypothesize_root_cause(pattern_data: Dict) -> str:
        """Vytvoří hypotézu o příčině vzorce."""
        event_type = pattern_data['event_type']
        reason = pattern_data['reason']
        count = len(pattern_data['occurrences'])
        
        if 'material' in event_type or 'material' in reason:
            return f"Recurring material issues ({count}x) suggest supply chain or planning problems"
        elif 'weather' in reason:
            return f"Weather-related blocks ({count}x) suggest need for better weather contingency"
        elif 'time' in event_type:
            return f"Time deviations ({count}x) suggest estimation accuracy issues"
        elif 'blocked' in event_type:
            return f"Frequent blocks ({count}x) suggest dependency or resource planning gaps"
        
        return f"Pattern detected ({count} occurrences) - requires investigation"
    
    @staticmethod
    def _suggest_pattern_actions(pattern_data: Dict) -> List[Dict]:
        """Navrhne akce pro řešení vzorce."""
        actions = []
        event_type = pattern_data['event_type']
        impact = pattern_data['total_impact_minutes']
        
        if 'material' in event_type:
            actions.append({
                'action': 'Review material ordering process',
                'expected_improvement': f'Could save {round(impact * 0.5 / 60, 1)} hours',
                'implementation_effort': 'medium'
            })
            actions.append({
                'action': 'Increase safety stock for critical materials',
                'expected_improvement': 'Reduce blocks by 50%',
                'implementation_effort': 'low'
            })
        
        if 'time' in event_type:
            actions.append({
                'action': 'Improve estimation with historical data',
                'expected_improvement': f'Reduce deviations by 30%',
                'implementation_effort': 'medium'
            })
            actions.append({
                'action': 'Add buffer time to critical tasks',
                'expected_improvement': 'Reduce scheduling conflicts',
                'implementation_effort': 'low'
            })
        
        if 'blocked' in event_type:
            actions.append({
                'action': 'Strengthen dependency tracking',
                'expected_improvement': 'Earlier warning of blocks',
                'implementation_effort': 'high'
            })
        
        return actions
