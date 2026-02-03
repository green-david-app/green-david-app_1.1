from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import uuid as uuid_lib

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import services dynamically to avoid circular imports
import sys
import os
import importlib.util

_asset_event_path = os.path.join(os.path.dirname(__file__), 'asset_event_service.py')
spec = importlib.util.spec_from_file_location("asset_event_service", _asset_event_path)
asset_event_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asset_event_service_module)
AssetEventService = asset_event_service_module.AssetEventService

_asset_event_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'asset_event.py')
spec = importlib.util.spec_from_file_location("asset_event", _asset_event_model_path)
asset_event_model_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asset_event_model_module)
AssetEventType = asset_event_model_module.AssetEventType


class QRService:
    """Služba pro QR operace v terénu."""
    
    @staticmethod
    def generate_qr_payload(entity_type: str, entity_id: int) -> Dict:
        """
        Generuje QR payload pro entitu.
        """
        payload = {
            'v': 1,  # version
            't': entity_type[:3].upper(),  # LOT, LOC, TYP
            'id': entity_id,
            'ts': int(datetime.utcnow().timestamp())
        }
        
        # Compact string for QR
        qr_string = f"GD:{payload['t']}:{payload['id']}"
        
        return {
            'payload': payload,
            'qr_string': qr_string,
            'qr_url': f"https://app.greendavid.cz/scan/{qr_string}"
        }
    
    @staticmethod
    def parse_qr(qr_string: str) -> Dict:
        """
        Parsuje naskenovaný QR kód.
        """
        if not qr_string.startswith('GD:'):
            return {'valid': False, 'error': 'Invalid QR format'}
        
        parts = qr_string.split(':')
        if len(parts) < 3:
            return {'valid': False, 'error': 'Invalid QR format'}
        
        try:
            return {
                'valid': True,
                'entity_type': parts[1],  # LOT, LOC, TYP
                'entity_id': int(parts[2])
            }
        except ValueError:
            return {'valid': False, 'error': 'Invalid entity ID'}
    
    @staticmethod
    def get_scan_context(entity_type: str, entity_id: int, employee_id: int = None) -> Dict:
        """
        Vrací kompletní kontext po naskenování + doporučené akce.
        """
        if entity_type == 'LOT':
            return QRService._get_lot_context(entity_id, employee_id)
        elif entity_type == 'LOC':
            return QRService._get_location_context(entity_id, employee_id)
        else:
            return {'error': 'Unknown entity type'}
    
    @staticmethod
    def _get_lot_context(lot_id: int, employee_id: int = None) -> Dict:
        """Kontext pro naskenovaný lot."""
        db = get_db()
        
        lot_row = db.execute("SELECT * FROM asset_lots WHERE id = ?", (lot_id,)).fetchone()
        if not lot_row:
            return {'error': 'Lot not found'}
        
        lot = dict(lot_row)
        
        # Get asset type
        asset_type = None
        if lot.get('asset_type_id'):
            type_row = db.execute("SELECT * FROM asset_types WHERE id = ?", (lot['asset_type_id'],)).fetchone()
            asset_type = dict(type_row) if type_row else None
        
        # Get location
        location = None
        if lot.get('location_id'):
            loc_row = db.execute("SELECT * FROM locations WHERE id = ?", (lot['location_id'],)).fetchone()
            location = dict(loc_row) if loc_row else None
        
        # Basic info
        context = {
            'entity_type': 'lot',
            'lot': lot,
            'asset_type': asset_type,
            'location': location,
        }
        
        # Recent activity
        try:
            recent_events = AssetEventService.get_lot_history(lot_id, limit=5)
            context['recent_activity'] = [e.to_dict() for e in recent_events]
        except:
            context['recent_activity'] = []
        
        # Reservations
        reservations_rows = db.execute("""
            SELECT * FROM asset_reservations 
            WHERE lot_id = ? AND status = 'active'
        """, (lot_id,)).fetchall()
        context['reservations'] = [dict(r) for r in reservations_rows]
        
        # === SUGGESTED ACTIONS ===
        actions = []
        
        # 1. Always offer photo documentation
        actions.append({
            'action': 'add_photo',
            'label': 'Přidat foto',
            'icon': 'camera',
            'priority': 2
        })
        
        # 2. If low quality, offer check
        quality_grade = lot.get('quality_grade', 'A')
        last_check = lot.get('last_quality_check')
        if quality_grade in ['C', 'D'] or not last_check:
            actions.append({
                'action': 'quality_check',
                'label': 'Kontrola kvality',
                'icon': 'clipboard-check',
                'priority': 1
            })
        
        # 3. If available, offer move
        quantity_available = lot.get('quantity_available', 0) or 0
        if quantity_available > 0:
            actions.append({
                'action': 'move',
                'label': f'Přesunout ({quantity_available} ks)',
                'icon': 'arrow-right',
                'priority': 3
            })
        
        # 4. If has reservations, offer fulfillment
        if reservations_rows:
            res = dict(reservations_rows[0])
            actions.append({
                'action': 'fulfill_reservation',
                'label': f'Vydat pro zakázku ({res.get("quantity", 0)} ks)',
                'icon': 'truck',
                'priority': 1,
                'reservation_id': res.get('id')
            })
        
        # 5. Maintenance
        actions.append({
            'action': 'maintenance',
            'label': 'Zaznamenat údržbu',
            'icon': 'droplet',
            'priority': 4
        })
        
        # 6. Quantity adjustment
        actions.append({
            'action': 'adjust_quantity',
            'label': 'Upravit množství',
            'icon': 'edit',
            'priority': 5
        })
        
        # Sort by priority
        context['suggested_actions'] = sorted(actions, key=lambda x: x['priority'])[:4]
        
        return context
    
    @staticmethod
    def _get_location_context(location_id: int, employee_id: int = None) -> Dict:
        """Kontext pro naskenovanou lokaci."""
        db = get_db()
        
        location_row = db.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
        if not location_row:
            return {'error': 'Location not found'}
        
        location = dict(location_row)
        
        # What's at location
        lots_rows = db.execute("""
            SELECT * FROM asset_lots 
            WHERE location_id = ? AND quantity_total > 0
        """, (location_id,)).fetchall()
        
        context = {
            'entity_type': 'location',
            'location': location,
            'lots_count': len(lots_rows),
            'lots_summary': []
        }
        
        # Get asset types for summary
        for lot_row in lots_rows[:10]:  # max 10
            lot = dict(lot_row)
            type_row = None
            if lot.get('asset_type_id'):
                type_row = db.execute("SELECT name FROM asset_types WHERE id = ?", (lot['asset_type_id'],)).fetchone()
            
            context['lots_summary'].append({
                'type_name': type_row[0] if type_row else 'Unknown',
                'quantity': lot.get('quantity_total', 0) or 0,
                'lot_id': lot.get('id')
            })
        
        # Recent activity on location
        try:
            recent = AssetEventService.get_location_activity(location_id, days=7)
            context['recent_activity'] = [e.to_dict() for e in recent[:10]]
        except:
            context['recent_activity'] = []
        
        # === SUGGESTED ACTIONS ===
        actions = []
        
        # 1. Inventory count
        actions.append({
            'action': 'inventory_count',
            'label': 'Provést inventuru',
            'icon': 'list-check',
            'priority': 1
        })
        
        # 2. Add new lot
        actions.append({
            'action': 'add_lot',
            'label': 'Přidat novou šarži',
            'icon': 'plus',
            'priority': 2
        })
        
        # 3. Bulk maintenance
        if lots_rows:
            actions.append({
                'action': 'bulk_maintenance',
                'label': f'Údržba ({len(lots_rows)} položek)',
                'icon': 'droplet',
                'priority': 3
            })
        
        # 4. Photo documentation
        actions.append({
            'action': 'add_photo',
            'label': 'Foto lokace',
            'icon': 'camera',
            'priority': 4
        })
        
        context['suggested_actions'] = sorted(actions, key=lambda x: x['priority'])[:4]
        
        return context
    
    @staticmethod
    def execute_quick_action(
        action: str,
        entity_type: str,
        entity_id: int,
        employee_id: int,
        data: Dict = None
    ) -> Dict:
        """
        Provede rychlou akci z QR kontextu.
        """
        data = data or {}
        
        if action == 'add_photo':
            return QRService._action_add_photo(entity_type, entity_id, employee_id, data)
        elif action == 'quality_check':
            return QRService._action_quality_check(entity_id, employee_id, data)
        elif action == 'move':
            return QRService._action_move(entity_id, employee_id, data)
        elif action == 'maintenance':
            return QRService._action_maintenance(entity_id, employee_id, data)
        elif action == 'adjust_quantity':
            return QRService._action_adjust_quantity(entity_id, employee_id, data)
        elif action == 'inventory_count':
            return QRService._action_inventory_count(entity_id, employee_id, data)
        else:
            return {'success': False, 'error': 'Unknown action'}
    
    @staticmethod
    def _action_add_photo(entity_type: str, entity_id: int, employee_id: int, data: Dict) -> Dict:
        event_type = AssetEventType.PHOTO_ADDED
        lot_id = entity_id if entity_type == 'LOT' else None
        location_id = entity_id if entity_type == 'LOC' else None
        
        event = AssetEventService.emit(
            event_type=event_type,
            lot_id=lot_id,
            location_id=location_id,
            employee_id=employee_id,
            payload={
                'photo_url': data.get('photo_url'),
                'note': data.get('note')
            },
            triggered_by='qr_scan'
        )
        
        return {'success': True, 'event_id': event.id}
    
    @staticmethod
    def _action_quality_check(lot_id: int, employee_id: int, data: Dict) -> Dict:
        db = get_db()
        
        lot_row = db.execute("SELECT * FROM asset_lots WHERE id = ?", (lot_id,)).fetchone()
        if not lot_row:
            return {'success': False, 'error': 'Lot not found'}
        
        lot = dict(lot_row)
        old_grade = lot.get('quality_grade', 'A')
        new_grade = data.get('grade', old_grade)
        
        db.execute("""
            UPDATE asset_lots 
            SET quality_grade = ?, quality_notes = ?, last_quality_check = ?
            WHERE id = ?
        """, (new_grade, data.get('notes'), datetime.utcnow().isoformat(), lot_id))
        db.commit()
        
        AssetEventService.emit(
            event_type=AssetEventType.QUALITY_INSPECTION,
            lot_id=lot_id,
            employee_id=employee_id,
            payload={
                'previous_grade': old_grade,
                'new_grade': new_grade,
                'notes': data.get('notes'),
                'photo_url': data.get('photo_url')
            },
            triggered_by='qr_scan'
        )
        
        return {'success': True, 'new_grade': new_grade}
    
    @staticmethod
    def _action_move(lot_id: int, employee_id: int, data: Dict) -> Dict:
        db = get_db()
        
        lot_row = db.execute("SELECT * FROM asset_lots WHERE id = ?", (lot_id,)).fetchone()
        if not lot_row:
            return {'success': False, 'error': 'Lot not found'}
        
        lot = dict(lot_row)
        to_location_id = data.get('to_location_id')
        if not to_location_id:
            return {'success': False, 'error': 'Target location required'}
        
        from_location_id = lot.get('location_id')
        quantity = data.get('quantity', lot.get('quantity_total', 0))
        
        # If partial move, create new lot (simplified - in production would handle split properly)
        if quantity < (lot.get('quantity_total', 0) or 0):
            # Update existing lot
            db.execute("""
                UPDATE asset_lots 
                SET quantity_total = quantity_total - ?, 
                    quantity_available = quantity_available - ?
                WHERE id = ?
            """, (quantity, quantity, lot_id))
            
            # Create new lot at new location
            new_lot_code = f"{lot.get('lot_code', 'LOT')}-SPLIT-{datetime.utcnow().strftime('%Y%m%d')}"
            db.execute("""
                INSERT INTO asset_lots (
                    asset_type_id, location_id, lot_code, quantity_total, quantity_available,
                    quality_grade, lifecycle_stage, availability_status, unit
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lot.get('asset_type_id'),
                to_location_id,
                new_lot_code,
                quantity,
                quantity,
                lot.get('quality_grade', 'A'),
                lot.get('lifecycle_stage', 'growing'),
                lot.get('availability_status', 'available'),
                lot.get('unit', 'ks')
            ))
        else:
            # Full move
            db.execute("""
                UPDATE asset_lots SET location_id = ? WHERE id = ?
            """, (to_location_id, lot_id))
        
        db.commit()
        
        AssetEventService.emit(
            event_type=AssetEventType.ASSET_MOVED,
            lot_id=lot_id,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            employee_id=employee_id,
            payload={'quantity': quantity},
            triggered_by='qr_scan'
        )
        
        return {'success': True, 'moved_quantity': quantity}
    
    @staticmethod
    def _action_maintenance(lot_id: int, employee_id: int, data: Dict) -> Dict:
        AssetEventService.emit(
            event_type=AssetEventType.MAINTENANCE_PERFORMED,
            lot_id=lot_id,
            employee_id=employee_id,
            payload={
                'maintenance_type': data.get('type', 'general'),
                'product_used': data.get('product'),
                'notes': data.get('notes'),
                'photo_url': data.get('photo_url')
            },
            triggered_by='qr_scan'
        )
        
        return {'success': True}
    
    @staticmethod
    def _action_adjust_quantity(lot_id: int, employee_id: int, data: Dict) -> Dict:
        db = get_db()
        
        lot_row = db.execute("SELECT * FROM asset_lots WHERE id = ?", (lot_id,)).fetchone()
        if not lot_row:
            return {'success': False, 'error': 'Lot not found'}
        
        lot = dict(lot_row)
        old_qty = lot.get('quantity_total', 0) or 0
        new_qty = data.get('quantity')
        
        if new_qty is None:
            return {'success': False, 'error': 'Quantity required'}
        
        db.execute("""
            UPDATE asset_lots 
            SET quantity_total = ?, 
                quantity_available = quantity_total - COALESCE(quantity_reserved, 0) - COALESCE(quantity_damaged, 0)
            WHERE id = ?
        """, (new_qty, lot_id))
        db.commit()
        
        AssetEventService.emit(
            event_type=AssetEventType.QUANTITY_ADJUSTED,
            lot_id=lot_id,
            employee_id=employee_id,
            quantity_before=old_qty,
            quantity_after=new_qty,
            payload={
                'reason': data.get('reason', 'manual_adjustment'),
                'notes': data.get('notes')
            },
            triggered_by='qr_scan'
        )
        
        return {'success': True, 'old_quantity': old_qty, 'new_quantity': new_qty}
    
    @staticmethod
    def _action_inventory_count(location_id: int, employee_id: int, data: Dict) -> Dict:
        db = get_db()
        counts = data.get('counts', [])
        # Format: [{'lot_id': 1, 'counted': 50}, ...]
        
        discrepancies = []
        for count in counts:
            lot_id = count.get('lot_id')
            counted = count.get('counted')
            
            if not lot_id or counted is None:
                continue
            
            lot_row = db.execute("SELECT * FROM asset_lots WHERE id = ? AND location_id = ?", (lot_id, location_id)).fetchone()
            if lot_row:
                lot = dict(lot_row)
                expected = lot.get('quantity_total', 0) or 0
                
                if expected != counted:
                    discrepancies.append({
                        'lot_id': lot_id,
                        'expected': expected,
                        'counted': counted,
                        'difference': counted - expected
                    })
                
                AssetEventService.emit(
                    event_type=AssetEventType.INVENTORY_COUNT,
                    lot_id=lot_id,
                    location_id=location_id,
                    employee_id=employee_id,
                    quantity_before=expected,
                    quantity_after=counted,
                    payload={'counted_by': employee_id},
                    triggered_by='qr_scan'
                )
        
        return {
            'success': True,
            'items_counted': len(counts),
            'discrepancies': discrepancies
        }
