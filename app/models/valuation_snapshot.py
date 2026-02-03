from datetime import datetime
import json

# Note: This is a simple class for data transfer, not SQLAlchemy model
# Actual table operations use direct SQL queries via get_db()


class ValuationSnapshot:
    """
    Ekonomický snapshot v čase.
    """
    
    def __init__(self):
        self.id = None
        self.snapshot_type = None
        self.snapshot_date = None
        self.lot_id = None
        self.asset_type_id = None
        self.location_id = None
        self.total_quantity = None
        self.total_purchase_value = None
        self.total_current_value = None
        self.total_sell_value = None
        self.avg_quality_score = None
        self.dead_stock_quantity = None
        self.slow_moving_quantity = None
        self.created_at = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'snapshot_type': self.snapshot_type,
            'snapshot_date': self.snapshot_date.isoformat() if isinstance(self.snapshot_date, datetime) else self.snapshot_date,
            'lot_id': self.lot_id,
            'asset_type_id': self.asset_type_id,
            'location_id': self.location_id,
            'total_quantity': self.total_quantity,
            'total_purchase_value': float(self.total_purchase_value) if self.total_purchase_value else None,
            'total_current_value': float(self.total_current_value) if self.total_current_value else None,
            'total_sell_value': float(self.total_sell_value) if self.total_sell_value else None,
            'avg_quality_score': float(self.avg_quality_score) if self.avg_quality_score else None,
            'dead_stock_quantity': self.dead_stock_quantity,
            'slow_moving_quantity': self.slow_moving_quantity,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
