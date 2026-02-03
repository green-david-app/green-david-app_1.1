from datetime import datetime
import uuid as uuid_lib
import json

# Note: This is a simple class for data transfer, not SQLAlchemy model
# Actual table operations use direct SQL queries via get_db()


class Location:
    """
    Zóna / Místo - hierarchická struktura lokací.
    """
    
    def __init__(self):
        self.id = None
        self.uuid = None
        self.parent_id = None
        self.path = None
        self.level = 0
        self.code = None
        self.name = None
        self.location_type = None
        self.capacity_units = None
        self.current_occupancy = 0
        self.sun_exposure = None
        self.irrigation = False
        self.heated = False
        self.gps_lat = None
        self.gps_lng = None
        self.qr_code = None
        self.is_active = True
        self.created_at = None
        self.updated_at = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'parent_id': self.parent_id,
            'path': self.path,
            'level': self.level,
            'code': self.code,
            'name': self.name,
            'location_type': self.location_type,
            'capacity_units': self.capacity_units,
            'current_occupancy': self.current_occupancy or 0,
            'sun_exposure': self.sun_exposure,
            'irrigation': bool(self.irrigation) if self.irrigation is not None else False,
            'heated': bool(self.heated) if self.heated is not None else False,
            'gps_lat': float(self.gps_lat) if self.gps_lat else None,
            'gps_lng': float(self.gps_lng) if self.gps_lng else None,
            'qr_code': self.qr_code,
            'is_active': bool(self.is_active) if self.is_active is not None else True,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
