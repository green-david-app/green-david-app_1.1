
from datetime import datetime, date
from . import db

class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False, default="note")  # note|task|job
    color = db.Column(db.String(20), nullable=False, default="#2e7d32")
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "title": self.title,
            "type": self.type,
            "color": self.color,
            "details": self.details or "",
        }
