from datetime import datetime
import json

# Note: This is a simple class for data transfer, not SQLAlchemy model
# Actual table operations use direct SQL queries via get_db()


class DailyBriefing:
    """
    Model pro denní briefings.
    """
    
    def __init__(self):
        self.id = None
        self.briefing_date = None
        self.generated_at = None
        self.executive_summary = None
        self.full_data = None
        self.total_tasks = None
        self.critical_items = None
        self.integrity_average = None
        self.notified = False
        self.notified_at = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'briefing_date': self.briefing_date.isoformat() if isinstance(self.briefing_date, datetime) else self.briefing_date,
            'generated_at': self.generated_at.isoformat() if isinstance(self.generated_at, datetime) else self.generated_at,
            'executive_summary': self.executive_summary,
            'total_tasks': self.total_tasks,
            'critical_items': self.critical_items,
            'integrity_average': self.integrity_average,
            'full_data': self.full_data,
            'notified': self.notified,
            'notified_at': self.notified_at.isoformat() if isinstance(self.notified_at, datetime) else self.notified_at
        }
