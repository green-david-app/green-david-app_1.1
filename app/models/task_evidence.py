from datetime import datetime
from app import db


class TaskEvidence(db.Model):
    __tablename__ = 'task_evidence'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    evidence_type = db.Column(db.String(20), nullable=False)  # photo, note, measurement, gps_checkin
    
    file_path = db.Column(db.String(500))
    file_name = db.Column(db.String(200))
    note_text = db.Column(db.Text)
    measurement_value = db.Column(db.Float)
    measurement_unit = db.Column(db.String(20))
    gps_lat = db.Column(db.Float)
    gps_lng = db.Column(db.Float)
    
    captured_at = db.Column(db.DateTime, nullable=False)
    captured_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    captured_offline = db.Column(db.Boolean, default=False)
    
    is_validated = db.Column(db.Boolean, default=False)
    validated_by_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    validated_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Note: Employee model may not exist as SQLAlchemy model, so we use strings
    # captured_by = db.relationship('Employee', foreign_keys=[captured_by_id])
    # validated_by = db.relationship('Employee', foreign_keys=[validated_by_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'evidence_type': self.evidence_type,
            'file_path': self.file_path,
            'note_text': self.note_text,
            'captured_at': self.captured_at.isoformat() if self.captured_at else None,
            'is_validated': self.is_validated
        }
