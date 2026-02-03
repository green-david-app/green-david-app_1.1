from datetime import datetime
import uuid as uuid_lib
import json

# Note: This is a simple class for data transfer, not SQLAlchemy model
# Actual table operations use direct SQL queries via get_db()


class AssetEventType:
    """Typy eventů pro Asset Core."""
    
    # === ŽIVOTNÍ CYKLUS ===
    ASSET_CREATED = 'asset_created'
    ASSET_MOVED = 'asset_moved'
    ASSET_SPLIT = 'asset_split'
    ASSET_MERGED = 'asset_merged'
    
    # === MNOŽSTVÍ ===
    QUANTITY_ADJUSTED = 'quantity_adjusted'
    QUANTITY_ADDED = 'quantity_added'
    QUANTITY_REMOVED = 'quantity_removed'
    
    # === REZERVACE ===
    ASSET_RESERVED = 'asset_reserved'
    ASSET_UNRESERVED = 'asset_unreserved'
    RESERVATION_FULFILLED = 'reservation_fulfilled'
    RESERVATION_EXPIRED = 'reservation_expired'
    
    # === SPOTŘEBA ===
    ASSET_CONSUMED = 'asset_consumed'
    ASSET_SOLD = 'asset_sold'
    ASSET_DISPOSED = 'asset_disposed'
    ASSET_DAMAGED = 'asset_damaged'
    
    # === KVALITA ===
    QUALITY_CHANGED = 'quality_changed'
    QUALITY_INSPECTION = 'quality_inspection'
    LIFECYCLE_CHANGED = 'lifecycle_changed'
    
    # === EVIDENCE ===
    PHOTO_ADDED = 'photo_added'
    NOTE_ADDED = 'note_added'
    
    # === ÚDRŽBA ===
    MAINTENANCE_PERFORMED = 'maintenance_performed'
    TREATMENT_APPLIED = 'treatment_applied'
    
    # === EKONOMIKA ===
    PRICE_UPDATED = 'price_updated'
    VALUATION_SNAPSHOT = 'valuation_snapshot'
    
    # === INVENTURA ===
    INVENTORY_COUNT = 'inventory_count'
    INVENTORY_DISCREPANCY = 'inventory_discrepancy'


class AssetEvent:
    """
    Event pro Asset Core - každá změna reality.
    """
    
    def __init__(self):
        self.id = None
        self.uuid = None
        self.event_type = None
        self.lot_id = None
        self.asset_type_id = None
        self.location_id = None
        self.job_id = None
        self.task_id = None
        self.reservation_id = None
        self.payload = {}
        self.quantity_before = None
        self.quantity_after = None
        self.quantity_delta = None
        self.from_location_id = None
        self.to_location_id = None
        self.occurred_at = None
        self.recorded_at = None
        self.triggered_by = 'user'
        self.employee_id = None
        self.device_id = None
        self.created_offline = False
        self.offline_uuid = None
        self.synced_at = None
    
    def to_dict(self):
        payload = self.payload
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except:
                payload = {}
        
        return {
            'id': self.id,
            'uuid': self.uuid,
            'event_type': self.event_type,
            'lot_id': self.lot_id,
            'asset_type_id': self.asset_type_id,
            'location_id': self.location_id,
            'job_id': self.job_id,
            'task_id': self.task_id,
            'reservation_id': self.reservation_id,
            'payload': payload,
            'quantity_before': self.quantity_before,
            'quantity_after': self.quantity_after,
            'quantity_delta': self.quantity_delta,
            'from_location_id': self.from_location_id,
            'to_location_id': self.to_location_id,
            'occurred_at': self.occurred_at.isoformat() if isinstance(self.occurred_at, datetime) else self.occurred_at,
            'recorded_at': self.recorded_at.isoformat() if isinstance(self.recorded_at, datetime) else self.recorded_at,
            'triggered_by': self.triggered_by,
            'employee_id': self.employee_id,
            'device_id': self.device_id,
            'created_offline': bool(self.created_offline) if self.created_offline is not None else False,
            'offline_uuid': self.offline_uuid,
            'synced_at': self.synced_at.isoformat() if isinstance(self.synced_at, datetime) else self.synced_at
        }
