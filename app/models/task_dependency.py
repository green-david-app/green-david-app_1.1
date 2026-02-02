from datetime import datetime
import uuid as uuid_lib
import json
from app import db


class TaskDependency(db.Model):
    __tablename__ = 'task_dependencies'
    
    id = db.Column(db.Integer, primary_key=True)
    
    predecessor_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    successor_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    dependency_type = db.Column(db.String(30), nullable=False)
    
    lag_minutes = db.Column(db.Integer, default=0)
    is_critical = db.Column(db.Boolean, default=False)
    is_hard = db.Column(db.Boolean, default=True)
    
    status = db.Column(db.String(20), default='pending')  # pending, active, satisfied, violated
    satisfied_at = db.Column(db.DateTime)
    violated_at = db.Column(db.DateTime)
    violation_reason = db.Column(db.Text)
    
    risk_weight = db.Column(db.Float, default=1.0)
    current_risk_level = db.Column(db.String(20), default='low')
    
    material_id = db.Column(db.Integer, db.ForeignKey('warehouse_items.id'))
    material_quantity = db.Column(db.Float)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    auto_generated = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float)
    validated = db.Column(db.Boolean, default=False)
    
    # Note: Relationships commented out as we use direct SQL queries
    # predecessor = db.relationship('Task', foreign_keys=[predecessor_task_id], 
    #                               backref=db.backref('successor_dependencies', lazy='dynamic'))
    # successor = db.relationship('Task', foreign_keys=[successor_task_id],
    #                            backref=db.backref('predecessor_dependencies', lazy='dynamic'))
    
    __table_args__ = (
        db.Index('idx_dep_predecessor', 'predecessor_task_id'),
        db.Index('idx_dep_successor', 'successor_task_id'),
        db.Index('idx_dep_status', 'status'),
        db.Index('idx_dep_type', 'dependency_type'),
    )
    
    @property
    def is_satisfied(self) -> bool:
        return self.status == 'satisfied'
    
    def to_dict(self):
        return {
            'id': self.id,
            'predecessor_task_id': self.predecessor_task_id,
            'successor_task_id': self.successor_task_id,
            'dependency_type': self.dependency_type,
            'lag_minutes': self.lag_minutes,
            'is_critical': self.is_critical,
            'is_hard': self.is_hard,
            'status': self.status,
            'risk_weight': self.risk_weight,
            'current_risk_level': self.current_risk_level,
            'satisfied_at': self.satisfied_at.isoformat() if isinstance(self.satisfied_at, datetime) else self.satisfied_at,
            'violated_at': self.violated_at.isoformat() if isinstance(self.violated_at, datetime) else self.violated_at,
            'violation_reason': self.violation_reason,
            'material_id': self.material_id,
            'material_quantity': self.material_quantity,
            'auto_generated': self.auto_generated,
            'validated': self.validated
        }
