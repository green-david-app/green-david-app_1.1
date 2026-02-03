from datetime import datetime
import json

# Note: This is a simple class for data transfer, not SQLAlchemy model
# Actual table operations use direct SQL queries via get_db()


class AIAlert:
    """
    Model pro AI alerty.
    """
    
    def __init__(self):
        self.id = None
        self.alert_type = None
        self.severity = None
        self.title = None
        self.summary = None
        self.detail_data = None
        self.job_id = None
        self.task_id = None
        self.employee_id = None
        self.status = 'active'
        self.recommended_actions = None
        self.action_taken = None
        self.created_at = None
        self.acknowledged_at = None
        self.acknowledged_by_id = None
        self.resolved_at = None
        self.resolved_by_id = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'summary': self.summary,
            'detail_data': self.detail_data,
            'job_id': self.job_id,
            'task_id': self.task_id,
            'employee_id': self.employee_id,
            'status': self.status,
            'recommended_actions': self.recommended_actions,
            'action_taken': self.action_taken,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'acknowledged_at': self.acknowledged_at.isoformat() if isinstance(self.acknowledged_at, datetime) else self.acknowledged_at,
            'resolved_at': self.resolved_at.isoformat() if isinstance(self.resolved_at, datetime) else self.resolved_at
        }
