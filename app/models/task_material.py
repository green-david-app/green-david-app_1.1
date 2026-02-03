from datetime import datetime
from app import db


class TaskMaterial(db.Model):
    __tablename__ = 'task_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    
    material_id = db.Column(db.Integer, db.ForeignKey('warehouse_items.id'))
    material_name = db.Column(db.String(200), nullable=False)
    planned_quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    
    actual_quantity = db.Column(db.Float)
    was_available = db.Column(db.Boolean)
    substitute_used = db.Column(db.Boolean, default=False)
    substitute_material_id = db.Column(db.Integer, db.ForeignKey('warehouse_items.id'))
    substitute_notes = db.Column(db.Text)
    
    reservation_id = db.Column(db.Integer, db.ForeignKey('material_reservations.id'))
    reservation_status = db.Column(db.String(20))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Note: WarehouseItem may not exist as SQLAlchemy model, so we use strings
    # material = db.relationship('WarehouseItem', foreign_keys=[material_id])
    
    @property
    def quantity_deviation(self):
        if self.actual_quantity is None:
            return None
        return self.actual_quantity - self.planned_quantity
    
    def to_dict(self):
        return {
            'id': self.id,
            'material_id': self.material_id,
            'material_name': self.material_name,
            'planned_quantity': self.planned_quantity,
            'actual_quantity': self.actual_quantity,
            'unit': self.unit,
            'substitute_used': self.substitute_used
        }
