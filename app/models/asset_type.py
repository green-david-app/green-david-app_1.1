from datetime import datetime
import uuid as uuid_lib
import json

# Note: This is a simple class for data transfer, not SQLAlchemy model
# Actual table operations use direct SQL queries via get_db()


class AssetType:
    """
    Katalog / Šablona - co můžeme mít.
    """
    
    def __init__(self):
        self.id = None
        self.uuid = None
        self.code = None
        self.name = None
        self.latin_name = None
        self.category = None
        self.subcategory = None
        self.growth_zone = None
        self.sun_requirement = None
        self.water_requirement = None
        self.mature_height_cm = None
        self.mature_width_cm = None
        self.growth_rate = None
        self.default_unit = 'ks'
        self.default_purchase_price = None
        self.default_sell_price = None
        self.propagation_method = None
        self.production_time_months = None
        self.planting_season_start = None
        self.planting_season_end = None
        self.sale_season_start = None
        self.sale_season_end = None
        self.primary_image_url = None
        self.is_active = True
        self.created_at = None
        self.updated_at = None
    
    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'code': self.code,
            'name': self.name,
            'latin_name': self.latin_name,
            'category': self.category,
            'subcategory': self.subcategory,
            'growth_zone': self.growth_zone,
            'sun_requirement': self.sun_requirement,
            'water_requirement': self.water_requirement,
            'mature_height_cm': self.mature_height_cm,
            'mature_width_cm': self.mature_width_cm,
            'growth_rate': self.growth_rate,
            'default_unit': self.default_unit,
            'default_purchase_price': float(self.default_purchase_price) if self.default_purchase_price else None,
            'default_sell_price': float(self.default_sell_price) if self.default_sell_price else None,
            'propagation_method': self.propagation_method,
            'production_time_months': self.production_time_months,
            'planting_season_start': self.planting_season_start,
            'planting_season_end': self.planting_season_end,
            'sale_season_start': self.sale_season_start,
            'sale_season_end': self.sale_season_end,
            'primary_image_url': self.primary_image_url,
            'is_active': bool(self.is_active) if self.is_active is not None else True,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
