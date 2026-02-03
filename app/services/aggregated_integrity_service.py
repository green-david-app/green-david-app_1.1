from typing import Dict
from datetime import datetime, timedelta
from collections import Counter
import json
import sys
import os
import importlib.util

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import TaskIntegrityService directly without going through app module
_integrity_service_path = os.path.join(os.path.dirname(__file__), 'task_integrity_service.py')
spec = importlib.util.spec_from_file_location("task_integrity_service", _integrity_service_path)
integrity_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity_service_module)
TaskIntegrityService = integrity_service_module.TaskIntegrityService


class AggregatedIntegrityService:
    
    @staticmethod
    def job_integrity_score(job_id: int) -> Dict:
        """Průměrná integrita všech tasků zakázky."""
        db = get_db()
        
        tasks_rows = db.execute("""
            SELECT * FROM tasks 
            WHERE job_id = ? AND status != 'cancelled'
        """, (job_id,)).fetchall()
        
        if not tasks_rows:
            return {'job_id': job_id, 'average_score': None, 'task_count': 0}
        
        tasks = [dict(t) for t in tasks_rows]
        scores = [t.get('integrity_score', 100.0) for t in tasks]
        average = sum(scores) / len(scores) if scores else 0
        
        distribution = {'excellent': 0, 'good': 0, 'warning': 0, 'critical': 0, 'failed': 0}
        critical_tasks = []
        
        for task in tasks:
            score = task.get('integrity_score', 100.0)
            level = TaskIntegrityService.get_integrity_level(score).lower()
            distribution[level] = distribution.get(level, 0) + 1
            if level in ['critical', 'failed']:
                critical_tasks.append({
                    'task_id': task['id'],
                    'title': task.get('title', 'Unknown'),
                    'score': score
                })
        
        return {
            'job_id': job_id,
            'average_score': round(average, 1),
            'task_count': len(tasks),
            'distribution': distribution,
            'critical_tasks': critical_tasks,
            'ai_trust_level': TaskIntegrityService.get_ai_trust_level(average)
        }
    
    @staticmethod
    def employee_integrity_trend(employee_id: int, days: int = 30) -> Dict:
        """Vývoj integrity tasků zaměstnance."""
        db = get_db()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        tasks_rows = db.execute("""
            SELECT * FROM tasks 
            WHERE assigned_employee_id = ? 
            AND created_at >= ? 
            AND status IN ('completed', 'partial', 'failed')
            ORDER BY created_at ASC
        """, (employee_id, since)).fetchall()
        
        if not tasks_rows:
            return {'employee_id': employee_id, 'task_count': 0, 'average_score': None}
        
        tasks = [dict(t) for t in tasks_rows]
        
        trend_data = []
        all_flags = []
        
        for task in tasks:
            actual_end_str = task.get('actual_end')
            created_at_str = task.get('created_at')
            
            date_str = None
            if actual_end_str:
                try:
                    if isinstance(actual_end_str, str):
                        date_obj = datetime.fromisoformat(actual_end_str.replace('Z', '+00:00'))
                    else:
                        date_obj = actual_end_str
                    date_str = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
            
            if not date_str and created_at_str:
                try:
                    if isinstance(created_at_str, str):
                        date_obj = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    else:
                        date_obj = created_at_str
                    date_str = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
            
            if date_str:
                trend_data.append({
                    'date': date_str,
                    'score': task.get('integrity_score', 100.0),
                    'task_id': task['id']
                })
            
            # Collect flags
            integrity_flags_str = task.get('integrity_flags', '[]')
            try:
                flags = json.loads(integrity_flags_str) if isinstance(integrity_flags_str, str) else integrity_flags_str
                if isinstance(flags, list):
                    all_flags.extend(flags)
            except:
                pass
        
        common_issues = Counter(all_flags).most_common(5)
        
        scores = [t.get('integrity_score', 100.0) for t in tasks]
        
        return {
            'employee_id': employee_id,
            'task_count': len(tasks),
            'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
            'min_score': min(scores) if scores else 0,
            'max_score': max(scores) if scores else 0,
            'trend_data': trend_data,
            'common_issues': [{'issue': i, 'count': c} for i, c in common_issues]
        }
    
    @staticmethod
    def system_integrity_dashboard() -> Dict:
        """Celková integrita systému pro management."""
        db = get_db()
        since = (datetime.utcnow() - timedelta(days=90)).isoformat()
        
        tasks_rows = db.execute("""
            SELECT * FROM tasks 
            WHERE created_at >= ? AND status != 'cancelled'
        """, (since,)).fetchall()
        
        if not tasks_rows:
            return {'total_tasks': 0, 'average_score': None}
        
        tasks = [dict(t) for t in tasks_rows]
        scores = [t.get('integrity_score', 100.0) for t in tasks]
        average = sum(scores) / len(scores) if scores else 0
        
        distribution = {'excellent': 0, 'good': 0, 'warning': 0, 'critical': 0, 'failed': 0}
        for score in scores:
            level = TaskIntegrityService.get_integrity_level(score).lower()
            distribution[level] += 1
        
        all_flags = []
        for task in tasks:
            integrity_flags_str = task.get('integrity_flags', '[]')
            try:
                flags = json.loads(integrity_flags_str) if isinstance(integrity_flags_str, str) else integrity_flags_str
                if isinstance(flags, list):
                    all_flags.extend(flags)
            except:
                pass
        
        top_issues = Counter(all_flags).most_common(10)
        
        return {
            'total_tasks': len(tasks),
            'average_score': round(average, 1),
            'distribution': distribution,
            'distribution_percentage': {k: round(v / len(tasks) * 100, 1) for k, v in distribution.items()} if tasks else {},
            'top_issues': [{'issue': i, 'count': c} for i, c in top_issues],
            'ai_system_trust': TaskIntegrityService.get_ai_trust_level(average)
        }
