from typing import Dict, List, Optional
from datetime import datetime
import json

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Models are data transfer classes only, not needed here


class InventoryService:
    """Služba pro inventářové operace a přehledy."""
    
    @staticmethod
    def get_spatial_overview() -> Dict:
        """
        Vrací inventář jako prostorovou mapu.
        Hlavní přehled: lokace → agregovaná data.
        """
        db = get_db()
        
        # Get root locations (level 0 or 1)
        locations_rows = db.execute("""
            SELECT * FROM locations 
            WHERE is_active = 1 AND level <= 1
        """).fetchall()
        
        result = []
        for loc_row in locations_rows:
            loc = dict(loc_row)
            loc_id = loc['id']
            
            # Get all child IDs recursively
            child_ids = InventoryService._get_all_child_ids(db, loc_id)
            location_ids = [loc_id] + child_ids
            
            # Aggregate stats
            placeholders = ','.join(['?'] * len(location_ids))
            stats_row = db.execute(f"""
                SELECT 
                    COUNT(*) as lot_count,
                    COALESCE(SUM(quantity_total), 0) as total_qty,
                    COALESCE(SUM(quantity_available), 0) as available_qty,
                    COALESCE(SUM(quantity_reserved), 0) as reserved_qty,
                    COUNT(DISTINCT asset_type_id) as type_count
                FROM asset_lots 
                WHERE location_id IN ({placeholders}) AND quantity_total > 0
            """, location_ids).fetchone()
            
            stats = dict(stats_row)
            
            # Calculate value
            value_row = db.execute(f"""
                SELECT COALESCE(SUM(quantity_total * COALESCE(current_value_per_unit, 0)), 0)
                FROM asset_lots 
                WHERE location_id IN ({placeholders}) AND quantity_total > 0
            """, location_ids).fetchone()
            
            value = float(value_row[0]) if value_row and value_row[0] else 0
            
            occupancy_percent = None
            if loc.get('capacity_units') and loc['capacity_units'] > 0:
                occupancy_percent = round((loc.get('current_occupancy', 0) or 0) / loc['capacity_units'] * 100, 1)
            
            result.append({
                'location_id': loc_id,
                'location_code': loc.get('code'),
                'location_name': loc.get('name'),
                'location_type': loc.get('location_type'),
                'lot_count': stats.get('lot_count', 0) or 0,
                'total_quantity': stats.get('total_qty', 0) or 0,
                'available_quantity': stats.get('available_qty', 0) or 0,
                'reserved_quantity': stats.get('reserved_qty', 0) or 0,
                'type_count': stats.get('type_count', 0) or 0,
                'total_value': value,
                'occupancy_percent': occupancy_percent,
                'children_count': len(child_ids)
            })
        
        return {
            'overview': result,
            'totals': {
                'locations': len(result),
                'total_quantity': sum(r['total_quantity'] for r in result),
                'total_value': sum(r['total_value'] for r in result)
            }
        }
    
    @staticmethod
    def get_location_detail(location_id: int, include_children: bool = True) -> Dict:
        """
        Detail lokace s rozpadem podle typů.
        """
        db = get_db()
        
        location_row = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
        if not location_row:
            return None
        
        location = dict(location_row)
        
        # Get location IDs
        if include_children:
            location_ids = [location_id] + InventoryService._get_all_child_ids(db, location_id)
        else:
            location_ids = [location_id]
        
        # Aggregate by type
        placeholders = ','.join(['?'] * len(location_ids))
        type_stats_rows = db.execute(f"""
            SELECT 
                at.id,
                at.code,
                at.name,
                at.category,
                COALESCE(SUM(al.quantity_total), 0) as total_qty,
                COALESCE(SUM(al.quantity_available), 0) as available_qty,
                COALESCE(SUM(al.quantity_reserved), 0) as reserved_qty,
                COUNT(al.id) as lot_count,
                AVG(al.current_value_per_unit) as avg_value
            FROM asset_types at
            JOIN asset_lots al ON al.asset_type_id = at.id
            WHERE al.location_id IN ({placeholders}) AND al.quantity_total > 0
            GROUP BY at.id
        """, location_ids).fetchall()
        
        types_data = []
        for ts_row in type_stats_rows:
            ts = dict(ts_row)
            types_data.append({
                'type_id': ts.get('id'),
                'type_code': ts.get('code'),
                'type_name': ts.get('name'),
                'category': ts.get('category'),
                'total_quantity': ts.get('total_qty', 0) or 0,
                'available_quantity': ts.get('available_qty', 0) or 0,
                'reserved_quantity': ts.get('reserved_qty', 0) or 0,
                'lot_count': ts.get('lot_count', 0) or 0,
                'avg_value': float(ts.get('avg_value', 0)) if ts.get('avg_value') else 0
            })
        
        # Get children
        children_rows = db.execute("""
            SELECT id, code, name FROM locations 
            WHERE parent_id = ? AND is_active = 1
        """, (location_id,)).fetchall()
        
        children = [{'id': c['id'], 'code': c['code'], 'name': c['name']} for c in children_rows]
        
        return {
            'location': {
                'id': location['id'],
                'code': location.get('code'),
                'name': location.get('name'),
                'type': location.get('location_type'),
                'capacity': location.get('capacity_units'),
                'occupancy': location.get('current_occupancy', 0) or 0
            },
            'types': sorted(types_data, key=lambda x: x['total_quantity'], reverse=True),
            'children': children,
            'totals': {
                'type_count': len(types_data),
                'total_quantity': sum(t['total_quantity'] for t in types_data),
                'available_quantity': sum(t['available_quantity'] for t in types_data)
            }
        }
    
    @staticmethod
    def get_type_inventory(asset_type_id: int) -> Dict:
        """
        Inventář konkrétního typu napříč lokacemi.
        """
        db = get_db()
        
        asset_type_row = db.execute("SELECT * FROM asset_types WHERE id = ?", (asset_type_id,)).fetchone()
        if not asset_type_row:
            return None
        
        asset_type = dict(asset_type_row)
        
        # Get lots grouped by location
        lots_rows = db.execute("""
            SELECT * FROM asset_lots 
            WHERE asset_type_id = ? AND quantity_total > 0
        """, (asset_type_id,)).fetchall()
        
        by_location = {}
        for lot_row in lots_rows:
            lot = dict(lot_row)
            loc_id = lot['location_id']
            
            if loc_id not in by_location:
                # Get location
                loc_row = db.execute("SELECT * FROM locations WHERE id = ?", (loc_id,)).fetchone()
                location = dict(loc_row) if loc_row else None
                
                by_location[loc_id] = {
                    'location': {
                        'id': location['id'] if location else None,
                        'code': location.get('code') if location else None,
                        'name': location.get('name') if location else None
                    } if location else None,
                    'lots': [],
                    'total_qty': 0,
                    'available_qty': 0
                }
            
            by_location[loc_id]['lots'].append(lot)
            by_location[loc_id]['total_qty'] += lot.get('quantity_total', 0) or 0
            by_location[loc_id]['available_qty'] += lot.get('quantity_available', 0) or 0
        
        return {
            'asset_type': {
                'id': asset_type['id'],
                'code': asset_type.get('code'),
                'name': asset_type.get('name'),
                'category': asset_type.get('category')
            },
            'locations': list(by_location.values()),
            'totals': {
                'total_quantity': sum(l['total_qty'] for l in by_location.values()),
                'available_quantity': sum(l['available_qty'] for l in by_location.values()),
                'location_count': len(by_location)
            }
        }
    
    @staticmethod
    def get_lots_at_location(location_id: int, asset_type_id: int = None) -> List[Dict]:
        """
        Konkrétní šarže na lokaci (drilldown).
        """
        db = get_db()
        
        query = "SELECT * FROM asset_lots WHERE location_id = ? AND quantity_total > 0"
        params = [location_id]
        
        if asset_type_id:
            query += " AND asset_type_id = ?"
            params.append(asset_type_id)
        
        query += " ORDER BY quantity_available DESC"
        
        lots_rows = db.execute(query, params).fetchall()
        return [dict(lot) for lot in lots_rows]
    
    @staticmethod
    def quick_search(query: str, limit: int = 20) -> Dict:
        """
        Rychlé vyhledávání v inventáři.
        """
        db = get_db()
        
        results = {
            'types': [],
            'lots': [],
            'locations': []
        }
        
        # Search types
        types_rows = db.execute("""
            SELECT * FROM asset_types 
            WHERE (
                code LIKE ? OR name LIKE ? OR latin_name LIKE ?
            ) AND is_active = 1
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', limit)).fetchall()
        
        results['types'] = [dict(t) for t in types_rows]
        
        # Search lots
        lots_rows = db.execute("""
            SELECT * FROM asset_lots 
            WHERE lot_code LIKE ? AND quantity_total > 0
            LIMIT ?
        """, (f'%{query}%', limit)).fetchall()
        
        results['lots'] = [dict(l) for l in lots_rows]
        
        # Search locations
        locations_rows = db.execute("""
            SELECT * FROM locations 
            WHERE (code LIKE ? OR name LIKE ?) AND is_active = 1
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', limit)).fetchall()
        
        results['locations'] = [dict(loc) for loc in locations_rows]
        
        return results
    
    @staticmethod
    def get_low_stock_alerts(threshold_percent: float = 20) -> List[Dict]:
        """
        Položky s nízkým stavem.
        """
        db = get_db()
        
        alerts = []
        
        # Aggregate by type
        type_totals_rows = db.execute("""
            SELECT 
                at.id,
                at.name,
                COALESCE(SUM(al.quantity_total), 0) as total,
                COALESCE(SUM(al.quantity_available), 0) as available
            FROM asset_types at
            JOIN asset_lots al ON al.asset_type_id = at.id
            WHERE al.quantity_total > 0
            GROUP BY at.id
        """).fetchall()
        
        for tt_row in type_totals_rows:
            tt = dict(tt_row)
            total = tt.get('total', 0) or 0
            
            if total > 0:
                available = tt.get('available', 0) or 0
                available_percent = (available / total) * 100
                
                if available_percent < threshold_percent:
                    alerts.append({
                        'type_id': tt.get('id'),
                        'type_name': tt.get('name'),
                        'total_quantity': total,
                        'available_quantity': available,
                        'available_percent': round(available_percent, 1),
                        'severity': 'critical' if available_percent < 10 else 'warning'
                    })
        
        return sorted(alerts, key=lambda x: x['available_percent'])
    
    @staticmethod
    def _get_all_child_ids(db, location_id: int) -> List[int]:
        """Rekurzivně získá ID všech podlokací."""
        children_rows = db.execute("SELECT id FROM locations WHERE parent_id = ?", (location_id,)).fetchall()
        ids = [c[0] for c in children_rows]
        for child_id in ids:
            ids.extend(InventoryService._get_all_child_ids(db, child_id))
        return ids
