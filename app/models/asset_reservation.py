from datetime import datetime
import uuid as uuid_lib
import json

# Note: This is a simple class for data transfer, not SQLAlchemy model
# Actual table operations use direct SQL queries via get_db()


class AssetReservation:
    """
    Rezervace pro zakázky.
    """
    
    def __init__(self):
        self.id = None
        self.uuid = None
        self.lot_id = None
        self.job_id = None
        self.task_id = None
        self.quantity = 0
        self.unit = 'ks'
        self.status = 'active'
        self.reserved_at = None
        self.needed_by = None
        self.expires_at = None
        self.fulfilled_quantity = 0
        self.fulfilled_at = None
        self.created_by_id = None
        self.notes = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'lot_id': self.lot_id,
            'job_id': self.job_id,
            'task_id': self.task_id,
            'quantity': self.quantity or 0,
            'unit': self.unit,
            'status': self.status,
            'reserved_at': self.reserved_at.isoformat() if isinstance(self.reserved_at, datetime) else self.reserved_at,
            'needed_by': self.needed_by.isoformat() if isinstance(self.needed_by, datetime) else self.needed_by,
            'expires_at': self.expires_at.isoformat() if isinstance(self.expires_at, datetime) else self.expires_at,
            'fulfilled_quantity': self.fulfilled_quantity or 0,
            'fulfilled_at': self.fulfilled_at.isoformat() if isinstance(self.fulfilled_at, datetime) else self.fulfilled_at,
            'created_by_id': self.created_by_id,
            'notes': self.notes
        }
