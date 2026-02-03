from datetime import datetime
import uuid as uuid_lib
import json

# Note: This is a simple class for data transfer, not SQLAlchemy model
# Actual table operations use direct SQL queries via get_db()


class AssetLot:
    """
    Fyzická realita - šarže/kusy na konkrétním místě.
    """
    
    def __init__(self):
        self.id = None
        self.uuid = None
        self.asset_type_id = None
        self.location_id = None
        self.lot_code = None
        self.batch_date = None
        self.source = None
        self.quantity_total = 0
        self.quantity_available = 0
        self.quantity_reserved = 0
        self.quantity_damaged = 0
        self.unit = 'ks'
        self.lifecycle_stage = 'growing'
        self.availability_status = 'available'
        self.quality_grade = 'A'
        self.quality_notes = None
        self.last_quality_check = None
        self.current_height_cm = None
        self.container_size = None
        self.root_status = None
        self.purchase_price_per_unit = None
        self.current_value_per_unit = None
        self.sell_price_per_unit = None
        self.qr_code = None
        self.created_at = None
        self.updated_at = None
        self.created_by_id = None
        self.last_synced_at = None
    
    def update_available(self):
        """Přepočítá dostupné množství."""
        self.quantity_available = self.quantity_total - (self.quantity_reserved or 0) - (self.quantity_damaged or 0)
        if self.quantity_available < 0:
            self.quantity_available = 0
    
    def to_dict(self, include_type=False, include_location=False):
        result = {
            'id': self.id,
            'uuid': self.uuid,
            'asset_type_id': self.asset_type_id,
            'location_id': self.location_id,
            'lot_code': self.lot_code,
            'batch_date': self.batch_date.isoformat() if isinstance(self.batch_date, datetime) else self.batch_date,
            'source': self.source,
            'quantity_total': self.quantity_total or 0,
            'quantity_available': self.quantity_available or 0,
            'quantity_reserved': self.quantity_reserved or 0,
            'quantity_damaged': self.quantity_damaged or 0,
            'unit': self.unit,
            'lifecycle_stage': self.lifecycle_stage,
            'availability_status': self.availability_status,
            'quality_grade': self.quality_grade,
            'quality_notes': self.quality_notes,
            'last_quality_check': self.last_quality_check.isoformat() if isinstance(self.last_quality_check, datetime) else self.last_quality_check,
            'current_height_cm': self.current_height_cm,
            'container_size': self.container_size,
            'root_status': self.root_status,
            'purchase_price_per_unit': float(self.purchase_price_per_unit) if self.purchase_price_per_unit else None,
            'current_value_per_unit': float(self.current_value_per_unit) if self.current_value_per_unit else None,
            'sell_price_per_unit': float(self.sell_price_per_unit) if self.sell_price_per_unit else None,
            'qr_code': self.qr_code,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
        
        if include_type and hasattr(self, 'asset_type'):
            result['asset_type'] = self.asset_type.to_dict() if hasattr(self.asset_type, 'to_dict') else None
        
        if include_location and hasattr(self, 'location'):
            result['location'] = self.location.to_dict() if hasattr(self.location, 'to_dict') else None
        
        return result
