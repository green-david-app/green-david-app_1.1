from datetime import datetime
import uuid as uuid_lib
import json
from app import db


class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    
    # === IDENTIFIKACE ===
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(50), nullable=False)  # work, transport, admin, inspection, maintenance
    
    # === VAZBY (povinné) ===
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    assigned_employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    
    # === ČASOVÉ OKNO (povinné) ===
    planned_start = db.Column(db.DateTime, nullable=False)
    planned_end = db.Column(db.DateTime, nullable=False)
    planned_duration_minutes = db.Column(db.Integer, nullable=False)
    
    # === LOKACE (povinná) ===
    location_type = db.Column(db.String(20), nullable=False)  # job_site, warehouse, nursery, office, travel
    location_id = db.Column(db.Integer)
    location_name = db.Column(db.String(200))
    gps_lat = db.Column(db.Float)
    gps_lng = db.Column(db.Float)
    
    # === OČEKÁVANÝ VÝSTUP (povinný) ===
    expected_outcome = db.Column(db.Text, nullable=False)
    expected_outcome_type = db.Column(db.String(50))  # installed, removed, transported, inspected, documented, planted
    expected_quantity = db.Column(db.Float)
    expected_unit = db.Column(db.String(20))
    
    # === SKUTEČNOST ===
    actual_start = db.Column(db.DateTime)
    actual_end = db.Column(db.DateTime)
    actual_duration_minutes = db.Column(db.Integer)
    
    # === STAV ===
    status = db.Column(db.String(20), nullable=False, default='planned')
    # planned -> assigned -> in_progress -> completed/partial/failed/blocked
    completion_state = db.Column(db.String(20))  # done, partial, failed, blocked
    completion_percentage = db.Column(db.Integer, default=0)
    
    # === ODCHYLKY ===
    time_deviation_minutes = db.Column(db.Integer, default=0)
    has_material_deviation = db.Column(db.Boolean, default=False)
    has_workaround = db.Column(db.Boolean, default=False)
    deviation_notes = db.Column(db.Text)
    
    # === INTEGRITA ===
    integrity_score = db.Column(db.Float, default=100.0)  # 0-100
    integrity_flags = db.Column(db.Text)  # JSON stored as TEXT in SQLite
    
    # === PRIORITY & RIZIKO ===
    priority = db.Column(db.String(20), default='normal')  # critical, high, normal, low
    risk_level = db.Column(db.String(20), default='low')
    risk_factors = db.Column(db.Text)  # JSON stored as TEXT in SQLite
    
    # === OFFLINE SUPPORT ===
    created_offline = db.Column(db.Boolean, default=False)
    last_synced_at = db.Column(db.DateTime)
    offline_changes = db.Column(db.Text)  # JSON stored as TEXT in SQLite
    sync_conflict = db.Column(db.Boolean, default=False)
    
    # === AUDIT ===
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    version = db.Column(db.Integer, default=1)
    
    # === RELATIONSHIPS ===
    # Note: Job and Employee models may not exist as SQLAlchemy models, so we use strings
    # job = db.relationship('Job', backref=db.backref('tasks', lazy='dynamic'))
    assigned_employee = db.relationship('Employee', foreign_keys=[assigned_employee_id], backref='assigned_tasks')
    created_by = db.relationship('Employee', foreign_keys=[created_by_id])
    materials = db.relationship('TaskMaterial', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    evidences = db.relationship('TaskEvidence', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    # === INDEXY ===
    __table_args__ = (
        db.Index('idx_task_job_status', 'job_id', 'status'),
        db.Index('idx_task_employee_date', 'assigned_employee_id', 'planned_start'),
        db.Index('idx_task_status_date', 'status', 'planned_start'),
        # Note: CheckConstraint may not work in SQLite, validation should be done in application code
    )
    
    def calculate_planned_duration(self):
        if self.planned_start and self.planned_end:
            delta = self.planned_end - self.planned_start
            self.planned_duration_minutes = int(delta.total_seconds() / 60)
    
    def calculate_time_deviation(self):
        if self.actual_duration_minutes and self.planned_duration_minutes:
            self.time_deviation_minutes = self.actual_duration_minutes - self.planned_duration_minutes
    
    @property
    def is_overdue(self):
        if self.status in ['completed', 'failed', 'cancelled']:
            return False
        if not self.planned_end:
            return False
        # Handle both datetime objects and ISO format strings from SQLite
        if isinstance(self.planned_end, str):
            try:
                planned_end_dt = datetime.fromisoformat(self.planned_end.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return False
        else:
            planned_end_dt = self.planned_end
        return datetime.utcnow() > planned_end_dt
    
    @property
    def integrity_flags_list(self):
        """Parse integrity_flags from JSON string to list"""
        if not self.integrity_flags:
            return []
        try:
            return json.loads(self.integrity_flags) if isinstance(self.integrity_flags, str) else self.integrity_flags
        except (json.JSONDecodeError, TypeError):
            return []
    
    @integrity_flags_list.setter
    def integrity_flags_list(self, value):
        """Set integrity_flags from list to JSON string"""
        self.integrity_flags = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def risk_factors_list(self):
        """Parse risk_factors from JSON string to list"""
        if not self.risk_factors:
            return []
        try:
            return json.loads(self.risk_factors) if isinstance(self.risk_factors, str) else self.risk_factors
        except (json.JSONDecodeError, TypeError):
            return []
    
    @risk_factors_list.setter
    def risk_factors_list(self, value):
        """Set risk_factors from list to JSON string"""
        self.risk_factors = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def offline_changes_dict(self):
        """Parse offline_changes from JSON string to dict"""
        if not self.offline_changes:
            return {}
        try:
            return json.loads(self.offline_changes) if isinstance(self.offline_changes, str) else self.offline_changes
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @offline_changes_dict.setter
    def offline_changes_dict(self, value):
        """Set offline_changes from dict to JSON string"""
        self.offline_changes = json.dumps(value) if isinstance(value, dict) else value
    
    def to_dict(self, include_relations=False):
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'job_id': self.job_id,
            'assigned_employee_id': self.assigned_employee_id,
            'created_by_id': self.created_by_id,
            'planned_start': self.planned_start.isoformat() if isinstance(self.planned_start, datetime) else self.planned_start,
            'planned_end': self.planned_end.isoformat() if isinstance(self.planned_end, datetime) else self.planned_end,
            'planned_duration_minutes': self.planned_duration_minutes,
            'actual_start': self.actual_start.isoformat() if isinstance(self.actual_start, datetime) else self.actual_start,
            'actual_end': self.actual_end.isoformat() if isinstance(self.actual_end, datetime) else self.actual_end,
            'actual_duration_minutes': self.actual_duration_minutes,
            'status': self.status,
            'completion_state': self.completion_state,
            'completion_percentage': self.completion_percentage,
            'location_type': self.location_type,
            'location_id': self.location_id,
            'location_name': self.location_name,
            'gps_lat': self.gps_lat,
            'gps_lng': self.gps_lng,
            'expected_outcome': self.expected_outcome,
            'expected_outcome_type': self.expected_outcome_type,
            'expected_quantity': self.expected_quantity,
            'expected_unit': self.expected_unit,
            'integrity_score': self.integrity_score,
            'integrity_flags': self.integrity_flags_list,
            'priority': self.priority,
            'risk_level': self.risk_level,
            'risk_factors': self.risk_factors_list,
            'time_deviation_minutes': self.time_deviation_minutes,
            'has_material_deviation': self.has_material_deviation,
            'has_workaround': self.has_workaround,
            'deviation_notes': self.deviation_notes,
            'created_offline': self.created_offline,
            'last_synced_at': self.last_synced_at.isoformat() if isinstance(self.last_synced_at, datetime) else self.last_synced_at,
            'offline_changes': self.offline_changes_dict,
            'sync_conflict': self.sync_conflict,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            'version': self.version
        }
        if include_relations:
            data['materials'] = [m.to_dict() for m in self.materials]
            data['evidences'] = [e.to_dict() for e in self.evidences]
        return data
