from typing import Optional, Dict, List
from datetime import datetime, timedelta
import json
import uuid as uuid_lib

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

from app.models.asset_event import AssetEvent, AssetEventType


class AssetEventService:
    """Služba pro emitování a dotazování asset eventů."""
    
    @staticmethod
    def emit(
        event_type: str,
        lot_id: int = None,
        asset_type_id: int = None,
        location_id: int = None,
        payload: Dict = None,
        quantity_before: int = None,
        quantity_after: int = None,
        from_location_id: int = None,
        to_location_id: int = None,
        job_id: int = None,
        task_id: int = None,
        reservation_id: int = None,
        employee_id: int = None,
        triggered_by: str = 'user',
        occurred_at: datetime = None,
        offline: bool = False,
        offline_uuid: str = None
    ) -> AssetEvent:
        """Emituje nový event."""
        
        db = get_db()
        
        quantity_delta = None
        if quantity_before is not None and quantity_after is not None:
            quantity_delta = quantity_after - quantity_before
        
        occurred_at_str = (occurred_at or datetime.utcnow()).isoformat()
        recorded_at_str = datetime.utcnow().isoformat()
        payload_json = json.dumps(payload or {})
        
        db.execute("""
            INSERT INTO asset_events (
                uuid, event_type, lot_id, asset_type_id, location_id,
                job_id, task_id, reservation_id, payload,
                quantity_before, quantity_after, quantity_delta,
                from_location_id, to_location_id,
                occurred_at, recorded_at, triggered_by, employee_id, device_id,
                created_offline, offline_uuid
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid_lib.uuid4()),
            event_type,
            lot_id,
            asset_type_id,
            location_id,
            job_id,
            task_id,
            reservation_id,
            payload_json,
            quantity_before,
            quantity_after,
            quantity_delta,
            from_location_id,
            to_location_id,
            occurred_at_str,
            recorded_at_str,
            triggered_by,
            employee_id,
            None,  # device_id
            1 if offline else 0,
            offline_uuid
        ))
        
        db.commit()
        
        # Get created event
        event_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        event_row = db.execute("SELECT * FROM asset_events WHERE id = ?", (event_id,)).fetchone()
        
        return AssetEventService._row_to_event(event_row)
    
    @staticmethod
    def get_lot_history(lot_id: int, limit: int = 50, event_types: List[str] = None) -> List[AssetEvent]:
        """Vrací historii eventů pro lot."""
        db = get_db()
        
        query = "SELECT * FROM asset_events WHERE lot_id = ?"
        params = [lot_id]
        
        if event_types:
            placeholders = ','.join(['?'] * len(event_types))
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)
        
        query += " ORDER BY occurred_at DESC LIMIT ?"
        params.append(limit)
        
        rows = db.execute(query, params).fetchall()
        return [AssetEventService._row_to_event(row) for row in rows]
    
    @staticmethod
    def get_location_activity(location_id: int, days: int = 7) -> List[AssetEvent]:
        """Vrací aktivitu na lokaci."""
        db = get_db()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        rows = db.execute("""
            SELECT * FROM asset_events 
            WHERE (
                location_id = ? OR from_location_id = ? OR to_location_id = ?
            ) AND occurred_at >= ?
            ORDER BY occurred_at DESC
        """, (location_id, location_id, location_id, since)).fetchall()
        
        return [AssetEventService._row_to_event(row) for row in rows]
    
    @staticmethod
    def get_job_asset_events(job_id: int) -> List[AssetEvent]:
        """Vrací všechny asset eventy pro zakázku."""
        db = get_db()
        
        rows = db.execute("""
            SELECT * FROM asset_events 
            WHERE job_id = ?
            ORDER BY occurred_at ASC
        """, (job_id,)).fetchall()
        
        return [AssetEventService._row_to_event(row) for row in rows]
    
    @staticmethod
    def aggregate_movements(location_id: int = None, days: int = 30) -> Dict:
        """Agreguje pohyby za období."""
        db = get_db()
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = """
            SELECT * FROM asset_events 
            WHERE occurred_at >= ? AND quantity_delta IS NOT NULL
        """
        params = [since]
        
        if location_id:
            query += " AND location_id = ?"
            params.append(location_id)
        
        rows = db.execute(query, params).fetchall()
        events = [AssetEventService._row_to_event(row) for row in rows]
        
        total_in = sum(e.quantity_delta for e in events if e.quantity_delta and e.quantity_delta > 0)
        total_out = sum(abs(e.quantity_delta) for e in events if e.quantity_delta and e.quantity_delta < 0)
        
        by_type = {}
        for e in events:
            if e.event_type not in by_type:
                by_type[e.event_type] = {'count': 0, 'quantity': 0}
            by_type[e.event_type]['count'] += 1
            by_type[e.event_type]['quantity'] += e.quantity_delta or 0
        
        return {
            'period_days': days,
            'total_events': len(events),
            'total_in': total_in,
            'total_out': total_out,
            'net_change': total_in - total_out,
            'by_event_type': by_type
        }
    
    @staticmethod
    def _row_to_event(row) -> AssetEvent:
        """Převede SQLite row na AssetEvent objekt."""
        if not row:
            return None
        
        event = AssetEvent()
        event.id = row[0]
        event.uuid = row[1]
        event.event_type = row[2]
        event.lot_id = row[3]
        event.asset_type_id = row[4]
        event.location_id = row[5]
        event.job_id = row[6]
        event.task_id = row[7]
        event.reservation_id = row[8]
        
        # Parse payload
        payload_str = row[9]
        try:
            event.payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
        except:
            event.payload = {}
        
        event.quantity_before = row[10]
        event.quantity_after = row[11]
        event.quantity_delta = row[12]
        event.from_location_id = row[13]
        event.to_location_id = row[14]
        
        # Parse dates
        occurred_at_str = row[15]
        if occurred_at_str:
            try:
                event.occurred_at = datetime.fromisoformat(occurred_at_str.replace('Z', '+00:00'))
            except:
                event.occurred_at = occurred_at_str
        
        recorded_at_str = row[16]
        if recorded_at_str:
            try:
                event.recorded_at = datetime.fromisoformat(recorded_at_str.replace('Z', '+00:00'))
            except:
                event.recorded_at = recorded_at_str
        
        event.triggered_by = row[17]
        event.employee_id = row[18]
        event.device_id = row[19]
        event.created_offline = bool(row[20]) if row[20] is not None else False
        event.offline_uuid = row[21]
        
        synced_at_str = row[22] if len(row) > 22 else None
        if synced_at_str:
            try:
                event.synced_at = datetime.fromisoformat(synced_at_str.replace('Z', '+00:00'))
            except:
                event.synced_at = synced_at_str
        
        return event
