from typing import List, Dict
from datetime import datetime
import sys
import os
import importlib.util

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import DependencyGraphService directly without going through app module
_dependency_graph_path = os.path.join(os.path.dirname(__file__), 'dependency_graph_service.py')
spec = importlib.util.spec_from_file_location("dependency_graph_service", _dependency_graph_path)
dependency_graph_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dependency_graph_module)
DependencyGraphService = dependency_graph_module.DependencyGraphService


class RiskPropagationService:
    
    @staticmethod
    def propagate_delay(task_id: int, delay_minutes: int) -> Dict:
        """Když task má zpoždění, propaguj riziko downstream."""
        db = get_db()
        
        task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task_row:
            return {'error': 'Task not found'}
        
        downstream = DependencyGraphService.get_downstream_tasks(task_id)
        
        affected_tasks = []
        critical_path_impacted = False
        total_cascade_impact = 0
        
        for downstream_task in downstream:
            dep_row = db.execute("""
                SELECT * FROM task_dependencies 
                WHERE predecessor_task_id = ? AND successor_task_id = ?
            """, (task_id, downstream_task['task_id'])).fetchone()
            
            if not dep_row:
                continue
            
            dep = dict(dep_row)
            risk_weight = dep.get('risk_weight', 1.0)
            impact_minutes = int(delay_minutes * risk_weight)
            
            new_risk_level = 'low'
            if impact_minutes > 120:
                new_risk_level = 'critical'
            elif impact_minutes > 60:
                new_risk_level = 'high'
            elif impact_minutes > 30:
                new_risk_level = 'medium'
            
            # Update dependency risk level
            db.execute("""
                UPDATE task_dependencies 
                SET current_risk_level = ?
                WHERE id = ?
            """, (new_risk_level, dep['id']))
            
            if dep.get('is_critical'):
                critical_path_impacted = True
            
            total_cascade_impact += impact_minutes
            
            affected_tasks.append({
                'task_id': downstream_task['task_id'],
                'title': downstream_task['title'],
                'impact_minutes': impact_minutes,
                'new_risk_level': new_risk_level,
                'is_critical': dep.get('is_critical', False)
            })
        
        db.commit()
        
        # Emit event
        if affected_tasks:
            try:
                import sys
                import os
                import importlib.util
                
                # Import TaskEventService directly
                _event_service_path = os.path.join(os.path.dirname(__file__), 'task_event_service.py')
                spec = importlib.util.spec_from_file_location("task_event_service", _event_service_path)
                event_service_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(event_service_module)
                TaskEventService = event_service_module.TaskEventService
                
                # Import TaskEventType directly
                _event_types_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'event_types.py')
                spec = importlib.util.spec_from_file_location("event_types", _event_types_path)
                event_types_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(event_types_module)
                TaskEventType = event_types_module.TaskEventType
                
                TaskEventService.emit(
                    task_id=task_id,
                    event_type=TaskEventType.TASK_RISK_PROPAGATED,
                    payload={
                        'source_task_id': task_id,
                        'risk_type': 'delay',
                        'delay_minutes': delay_minutes,
                        'affected_tasks_count': len(affected_tasks),
                        'estimated_impact_hours': round(total_cascade_impact / 60, 1),
                        'critical_path_impacted': critical_path_impacted
                    },
                    source='system'
                )
            except Exception as e:
                print(f"[WARNING] Failed to emit risk propagation event: {e}")
        
        return {
            'source_task_id': task_id,
            'delay_minutes': delay_minutes,
            'affected_tasks': affected_tasks,
            'critical_path_impacted': critical_path_impacted,
            'total_cascade_impact_minutes': total_cascade_impact,
            'mitigation_options': RiskPropagationService._suggest_mitigations(delay_minutes, affected_tasks)
        }
    
    @staticmethod
    def propagate_failure(task_id: int) -> Dict:
        """Když task selže, propaguj důsledky."""
        db = get_db()
        downstream = DependencyGraphService.get_downstream_tasks(task_id)
        
        violated_dependencies = []
        blocked_tasks = []
        
        for downstream_task in downstream:
            dep_row = db.execute("""
                SELECT * FROM task_dependencies 
                WHERE predecessor_task_id = ? AND successor_task_id = ?
            """, (task_id, downstream_task['task_id'])).fetchone()
            
            if dep_row:
                dep = dict(dep_row)
                if dep.get('is_hard'):
                    # Update dependency status
                    db.execute("""
                        UPDATE task_dependencies 
                        SET status = 'violated', 
                            violated_at = ?,
                            current_risk_level = 'critical'
                        WHERE id = ?
                    """, (datetime.utcnow().isoformat(), dep['id']))
                    
                    violated_dependencies.append(dep['id'])
                    
                    succ_id = downstream_task['task_id']
                    succ_task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (succ_id,)).fetchone()
                    if succ_task_row:
                        succ_task = dict(succ_task_row)
                        if succ_task.get('status') in ['planned', 'assigned']:
                            blocked_tasks.append({
                                'task_id': succ_task['id'],
                                'title': succ_task.get('title', 'Unknown')
                            })
        
        db.commit()
        
        return {
            'source_task_id': task_id,
            'violated_dependencies': violated_dependencies,
            'blocked_tasks': blocked_tasks,
            'total_affected': len(downstream),
            'recovery_options': ['Retry failed task', 'Find alternative approach', 'Reschedule dependent tasks']
        }
    
    @staticmethod
    def calculate_job_risk_score(job_id: int) -> Dict:
        """Celkové riziko zakázky."""
        db = get_db()
        
        try:
            import sys
            import os
            import importlib.util
            
            # Import AggregatedIntegrityService
            _integrity_service_path = os.path.join(os.path.dirname(__file__), 'aggregated_integrity_service.py')
            spec = importlib.util.spec_from_file_location("aggregated_integrity_service", _integrity_service_path)
            integrity_service_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(integrity_service_module)
            AggregatedIntegrityService = integrity_service_module.AggregatedIntegrityService
            
            integrity_data = AggregatedIntegrityService.job_integrity_score(job_id)
        except Exception as e:
            print(f"[WARNING] Failed to get integrity data: {e}")
            integrity_data = {'average_score': None}
        
        dependencies = DependencyGraphService.get_job_dependencies(job_id)
        
        violated_count = sum(1 for d in dependencies if d.get('status') == 'violated')
        critical_risk_count = sum(1 for d in dependencies if d.get('current_risk_level') == 'critical')
        
        tasks_rows = db.execute("SELECT * FROM tasks WHERE job_id = ?", (job_id,)).fetchall()
        tasks = [dict(t) for t in tasks_rows]
        
        blocked_count = sum(1 for t in tasks if t.get('status') == 'blocked')
        
        # Check overdue tasks
        overdue_count = 0
        for task in tasks:
            planned_end_str = task.get('planned_end')
            if planned_end_str:
                try:
                    if isinstance(planned_end_str, str):
                        planned_end = datetime.fromisoformat(planned_end_str.replace('Z', '+00:00'))
                    else:
                        planned_end = planned_end_str
                    
                    status = task.get('status', 'planned')
                    if status not in ['completed', 'failed', 'cancelled']:
                        if datetime.utcnow() > planned_end:
                            overdue_count += 1
                except:
                    pass
        
        risk_score = 0
        risk_factors = []
        
        if integrity_data.get('average_score'):
            integrity_risk = 100 - integrity_data['average_score']
            risk_score += integrity_risk * 0.3
            if integrity_risk > 30:
                risk_factors.append(f"Low integrity: {integrity_data['average_score']:.0f}")
        
        if violated_count > 0:
            risk_score += min(30, violated_count * 10)
            risk_factors.append(f"{violated_count} violated dependencies")
        
        if blocked_count > 0:
            risk_score += min(15, blocked_count * 5)
            risk_factors.append(f"{blocked_count} blocked tasks")
        
        if overdue_count > 0:
            risk_score += min(15, overdue_count * 5)
            risk_factors.append(f"{overdue_count} overdue tasks")
        
        risk_score = min(100, risk_score)
        
        if risk_score >= 70:
            risk_level = 'critical'
        elif risk_score >= 50:
            risk_level = 'high'
        elif risk_score >= 30:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        return {
            'job_id': job_id,
            'risk_score': round(risk_score, 1),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'violated_dependencies': violated_count,
            'critical_risks': critical_risk_count,
            'blocked_tasks': blocked_count,
            'overdue_tasks': overdue_count
        }
    
    @staticmethod
    def _suggest_mitigations(delay_minutes: int, affected_tasks: List) -> List[str]:
        suggestions = []
        if delay_minutes <= 60:
            suggestions.append("Overtime work to catch up")
        if delay_minutes > 60:
            suggestions.append("Add additional workers")
        if len(affected_tasks) > 3:
            suggestions.append("Parallel execution of non-dependent tasks")
        critical_count = sum(1 for t in affected_tasks if t.get('is_critical'))
        if critical_count > 0:
            suggestions.append("Review critical path - find alternative sequence")
            suggestions.append("Escalate to project manager")
        return suggestions
