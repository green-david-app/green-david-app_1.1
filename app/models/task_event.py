from datetime import datetime
import uuid as uuid_lib
import json
from app import db


class TaskEvent(db.Model):
    __tablename__ = 'task_events'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    payload = db.Column(db.Text, nullable=False, default='{}')  # JSON stored as TEXT in SQLite
    
    occurred_at = db.Column(db.DateTime, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    occurred_offline = db.Column(db.Boolean, default=False)
    synced_at = db.Column(db.DateTime)
    
    source = db.Column(db.String(20), nullable=False, default='web_app')  # mobile_app, web_app, system, ai_operator
    source_device_id = db.Column(db.String(100))
    
    ai_processed = db.Column(db.Boolean, default=False)
    ai_processed_at = db.Column(db.DateTime)
    ai_insights = db.Column(db.Text)  # JSON stored as TEXT in SQLite
    
    # Note: Relationships may not work if Job/Employee models don't exist as SQLAlchemy models
    # task = db.relationship('Task', backref=db.backref('events', lazy='dynamic', order_by='TaskEvent.occurred_at.desc()'))
    # job = db.relationship('Job', backref=db.backref('task_events', lazy='dynamic'))
    # employee = db.relationship('Employee', foreign_keys=[employee_id], backref='triggered_events')
    
    # === INDEXY ===
    __table_args__ = (
        db.Index('idx_event_task_type', 'task_id', 'event_type'),
        db.Index('idx_event_job_time', 'job_id', 'occurred_at'),
        db.Index('idx_event_type_time', 'event_type', 'occurred_at'),
        db.Index('idx_event_ai_unprocessed', 'ai_processed'),
        db.Index('idx_event_task_time', 'task_id', 'occurred_at'),
    )
    
    @property
    def payload_dict(self):
        """Parse payload from JSON string to dict"""
        if not self.payload:
            return {}
        try:
            return json.loads(self.payload) if isinstance(self.payload, str) else self.payload
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @payload_dict.setter
    def payload_dict(self, value):
        """Set payload from dict to JSON string"""
        self.payload = json.dumps(value) if isinstance(value, dict) else value
    
    @property
    def ai_insights_dict(self):
        """Parse ai_insights from JSON string to dict"""
        if not self.ai_insights:
            return {}
        try:
            return json.loads(self.ai_insights) if isinstance(self.ai_insights, str) else self.ai_insights
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @ai_insights_dict.setter
    def ai_insights_dict(self, value):
        """Set ai_insights from dict to JSON string"""
        self.ai_insights = json.dumps(value) if isinstance(value, dict) else value
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'task_id': self.task_id,
            'event_type': self.event_type,
            'job_id': self.job_id,
            'employee_id': self.employee_id,
            'payload': self.payload_dict,
            'occurred_at': self.occurred_at.isoformat() if isinstance(self.occurred_at, datetime) else self.occurred_at,
            'recorded_at': self.recorded_at.isoformat() if isinstance(self.recorded_at, datetime) else self.recorded_at,
            'occurred_offline': self.occurred_offline,
            'synced_at': self.synced_at.isoformat() if isinstance(self.synced_at, datetime) else self.synced_at,
            'source': self.source,
            'source_device_id': self.source_device_id,
            'ai_processed': self.ai_processed,
            'ai_processed_at': self.ai_processed_at.isoformat() if isinstance(self.ai_processed_at, datetime) else self.ai_processed_at,
            'ai_insights': self.ai_insights_dict
        }
