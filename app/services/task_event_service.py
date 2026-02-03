from datetime import datetime, timedelta
from typing import List, Optional
from collections import Counter
import json
import uuid as uuid_lib
import sys
import os
import importlib.util

# Import TaskEventType directly without going through app module
_event_types_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'event_types.py')
spec = importlib.util.spec_from_file_location("event_types", _event_types_path)
event_types_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_types_module)
TaskEventType = event_types_module.TaskEventType

# TaskEvent model will be created dynamically when needed


class TaskEventService:
    
    @staticmethod
    def emit(
        task_id: int, 
        event_type: TaskEventType, 
        payload: dict = None,
        employee_id: int = None,
        source: str = 'web_app',
        occurred_at: datetime = None,
        offline: bool = False,
        device_id: str = None
    ):
        """Emituje nový event pro task."""
        # Note: In this project, we use direct SQL queries instead of SQLAlchemy ORM
        # So we'll use get_db() instead of Task.query.get()
        def get_db():
            from main import get_db as _get_db
            return _get_db()
        
        db_conn = get_db()
        
        # Get task to verify it exists and get job_id
        task_row = db_conn.execute(
            "SELECT id, job_id FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()
        
        if not task_row:
            raise ValueError(f"Task {task_id} not found")
        
        job_id = task_row[1] if len(task_row) > 1 else None
        
        # Prepare payload as JSON string
        payload_json = json.dumps(payload or {})
        occurred_at_str = (occurred_at or datetime.utcnow()).isoformat()
        recorded_at_str = datetime.utcnow().isoformat()
        
        # Insert event
        db_conn.execute("""
            INSERT INTO task_events (
                uuid, task_id, event_type, job_id, employee_id, payload,
                occurred_at, recorded_at, occurred_offline, source, source_device_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid_lib.uuid4()),
            task_id,
            event_type.value,
            job_id,
            employee_id,
            payload_json,
            occurred_at_str,
            recorded_at_str,
            1 if offline else 0,
            source,
            device_id
        ))
        
        db_conn.commit()
        
        # Get created event
        event_id = db_conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        event_row = db_conn.execute(
            "SELECT * FROM task_events WHERE id = ?",
            (event_id,)
        ).fetchone()
        
        # Create a simple dict-like object for compatibility
        class EventDict:
            def __init__(self, row):
                self.id = row[0]
                self.uuid = row[1]
                self.task_id = row[2]
                self.event_type = row[3]
                self.job_id = row[4]
                self.employee_id = row[5]
                self.payload = row[6]
                self.occurred_at = datetime.fromisoformat(row[7]) if isinstance(row[7], str) else row[7]
                self.recorded_at = datetime.fromisoformat(row[8]) if isinstance(row[8], str) else row[8]
                self.occurred_offline = bool(row[9])
                self.synced_at = datetime.fromisoformat(row[10]) if row[10] and isinstance(row[10], str) else row[10]
                self.source = row[11]
                self.source_device_id = row[12]
                self.ai_processed = bool(row[13])
                self.ai_processed_at = datetime.fromisoformat(row[14]) if row[14] and isinstance(row[14], str) else row[14]
                self.ai_insights = row[15]
        
        return EventDict(event_row)
    
    @staticmethod
    def emit_batch(events: List[dict]) -> List:
        """Pro offline sync - bulk insert eventů."""
        from main import get_db
        
        db_conn = get_db()
        created_events = []
        
        for event_data in events:
            payload_json = json.dumps(event_data.get('payload', {}))
            occurred_at_str = event_data.get('occurred_at', datetime.utcnow())
            if isinstance(occurred_at_str, datetime):
                occurred_at_str = occurred_at_str.isoformat()
            
            db_conn.execute("""
                INSERT INTO task_events (
                    uuid, task_id, event_type, job_id, employee_id, payload,
                    occurred_at, recorded_at, occurred_offline, source, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid_lib.uuid4()),
                event_data['task_id'],
                event_data['event_type'],
                event_data.get('job_id'),
                event_data.get('employee_id'),
                payload_json,
                occurred_at_str,
                datetime.utcnow().isoformat(),
                1,  # offline
                event_data.get('source', 'mobile_app'),
                datetime.utcnow().isoformat()
            ))
        
        db_conn.commit()
        return created_events
    
    @staticmethod
    def get_task_history(
        task_id: int,
        event_types: List[str] = None,
        since: datetime = None,
        limit: int = 100
    ) -> List:
        """Vrací historii eventů pro task."""
        from main import get_db
        
        db_conn = get_db()
        
        query = "SELECT * FROM task_events WHERE task_id = ?"
        params = [task_id]
        
        if event_types:
            placeholders = ','.join(['?'] * len(event_types))
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_types)
        
        if since:
            query += " AND occurred_at >= ?"
            params.append(since.isoformat())
        
        query += " ORDER BY occurred_at DESC LIMIT ?"
        params.append(limit)
        
        rows = db_conn.execute(query, params).fetchall()
        
        # Convert rows to dict-like objects
        class EventDict:
            def __init__(self, row):
                self.id = row[0]
                self.uuid = row[1]
                self.task_id = row[2]
                self.event_type = row[3]
                self.job_id = row[4]
                self.employee_id = row[5]
                self.payload = row[6]
                self.occurred_at = datetime.fromisoformat(row[7]) if isinstance(row[7], str) else row[7]
                self.recorded_at = datetime.fromisoformat(row[8]) if isinstance(row[8], str) else row[8]
                self.occurred_offline = bool(row[9])
                self.synced_at = datetime.fromisoformat(row[10]) if row[10] and isinstance(row[10], str) else row[10]
                self.source = row[11]
                self.source_device_id = row[12]
                self.ai_processed = bool(row[13])
                self.ai_processed_at = datetime.fromisoformat(row[14]) if row[14] and isinstance(row[14], str) else row[14]
                self.ai_insights = row[15]
        
        events = [EventDict(row) for row in rows]
        return events
    
    @staticmethod
    def get_job_event_stream(
        job_id: int,
        since: datetime = None,
        limit: int = 100
    ) -> List:
        """Vrací stream eventů pro celou zakázku."""
        from main import get_db
        
        db_conn = get_db()
        
        query = "SELECT * FROM task_events WHERE job_id = ?"
        params = [job_id]
        
        if since:
            query += " AND occurred_at >= ?"
            params.append(since.isoformat())
        
        query += " ORDER BY occurred_at DESC LIMIT ?"
        params.append(limit)
        
        rows = db_conn.execute(query, params).fetchall()
        
        # Convert rows to dict-like objects (same as get_task_history)
        class EventDict:
            def __init__(self, row):
                self.id = row[0]
                self.uuid = row[1]
                self.task_id = row[2]
                self.event_type = row[3]
                self.job_id = row[4]
                self.employee_id = row[5]
                self.payload = row[6]
                self.occurred_at = datetime.fromisoformat(row[7]) if isinstance(row[7], str) else row[7]
                self.recorded_at = datetime.fromisoformat(row[8]) if isinstance(row[8], str) else row[8]
                self.occurred_offline = bool(row[9])
                self.synced_at = datetime.fromisoformat(row[10]) if row[10] and isinstance(row[10], str) else row[10]
                self.source = row[11]
                self.source_device_id = row[12]
                self.ai_processed = bool(row[13])
                self.ai_processed_at = datetime.fromisoformat(row[14]) if row[14] and isinstance(row[14], str) else row[14]
                self.ai_insights = row[15]
        
        events = [EventDict(row) for row in rows]
        return events
    
    @staticmethod
    def get_unprocessed_for_ai(limit: int = 100) -> List:
        """Vrací eventy které AI ještě nezpracovala."""
        from main import get_db
        
        db_conn = get_db()
        
        rows = db_conn.execute("""
            SELECT * FROM task_events 
            WHERE ai_processed = 0 
            ORDER BY occurred_at ASC 
            LIMIT ?
        """, (limit,)).fetchall()
        
        # Convert rows to dict-like objects
        class EventDict:
            def __init__(self, row):
                self.id = row[0]
                self.uuid = row[1]
                self.task_id = row[2]
                self.event_type = row[3]
                self.job_id = row[4]
                self.employee_id = row[5]
                self.payload = row[6]
                self.occurred_at = datetime.fromisoformat(row[7]) if isinstance(row[7], str) else row[7]
                self.recorded_at = datetime.fromisoformat(row[8]) if isinstance(row[8], str) else row[8]
                self.occurred_offline = bool(row[9])
                self.synced_at = datetime.fromisoformat(row[10]) if row[10] and isinstance(row[10], str) else row[10]
                self.source = row[11]
                self.source_device_id = row[12]
                self.ai_processed = bool(row[13])
                self.ai_processed_at = datetime.fromisoformat(row[14]) if row[14] and isinstance(row[14], str) else row[14]
                self.ai_insights = row[15]
        
        events = [EventDict(row) for row in rows]
        return events
    
    @staticmethod
    def mark_ai_processed(event_ids: List[int], insights: dict = None):
        """Označí eventy jako zpracované AI."""
        from main import get_db
        import json
        
        db_conn = get_db()
        
        insights_json = json.dumps(insights) if insights else None
        processed_at = datetime.utcnow().isoformat()
        
        placeholders = ','.join(['?'] * len(event_ids))
        db_conn.execute(f"""
            UPDATE task_events 
            SET ai_processed = 1, 
                ai_processed_at = ?,
                ai_insights = ?
            WHERE id IN ({placeholders})
        """, [processed_at, insights_json] + event_ids)
        
        db_conn.commit()
    
    @staticmethod
    def analyze_patterns(job_id: int = None, employee_id: int = None, days: int = 30) -> dict:
        """Analyzuje vzorce v eventech."""
        from main import get_db
        
        db_conn = get_db()
        
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = "SELECT event_type, payload FROM task_events WHERE occurred_at >= ?"
        params = [since]
        
        if job_id:
            query += " AND job_id = ?"
            params.append(job_id)
        if employee_id:
            query += " AND employee_id = ?"
            params.append(employee_id)
        
        rows = db_conn.execute(query, params).fetchall()
        
        events = [{'event_type': r[0], 'payload': r[1]} for r in rows]
        
        patterns = {
            'total_events': len(events),
            'by_type': Counter(e['event_type'] for e in events),
            'blocked_count': sum(1 for e in events if 'blocked' in e['event_type']),
            'deviation_count': sum(1 for e in events if 'deviation' in e['event_type']),
        }
        
        # Extract block reasons
        block_reasons = []
        for e in events:
            if 'blocked' in e['event_type']:
                try:
                    payload = json.loads(e['payload']) if isinstance(e['payload'], str) else e['payload']
                    reason = payload.get('block_reason')
                    if reason:
                        block_reasons.append(reason)
                except:
                    pass
        
        patterns['common_block_reasons'] = Counter(block_reasons).most_common(5)
        
        return patterns
