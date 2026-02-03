#!/usr/bin/env python3
"""
Test script for TaskEvent system
"""
import sys
import os
from datetime import datetime
import uuid as uuid_lib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import directly from modules to avoid Flask-SQLAlchemy dependency
from main import app, get_db

# Import service and types directly
import importlib.util
spec = importlib.util.spec_from_file_location("event_types", "app/utils/event_types.py")
event_types_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(event_types_module)
TaskEventType = event_types_module.TaskEventType

spec = importlib.util.spec_from_file_location("task_event_service", "app/services/task_event_service.py")
service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service_module)
TaskEventService = service_module.TaskEventService

def test_task_events():
    """Test TaskEvent functionality"""
    with app.app_context():
        print("=== Testing TaskEvent System ===\n")
        
        # Get a task to test with
        db = get_db()
        task_row = db.execute("SELECT id FROM tasks LIMIT 1").fetchone()
        
        if not task_row:
            print("⚠ No tasks found in database. Creating a test task...")
            # Create a test task
            db.execute("""
                INSERT INTO tasks (
                    uuid, title, description, task_type, job_id, assigned_employee_id, created_by_id,
                    planned_start, planned_end, planned_duration_minutes, location_type, expected_outcome
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid_lib.uuid4()),
                "Test Task",
                "Test task for event system",
                "work",
                1,  # Assuming job_id 1 exists
                1,  # Assuming employee_id 1 exists
                1,  # Assuming employee_id 1 exists
                datetime.utcnow().isoformat(),
                (datetime.utcnow().replace(hour=17)).isoformat(),
                480,
                "job_site",
                "Complete test task"
            ))
            db.commit()
            task_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"✓ Created test task with id: {task_id}\n")
        else:
            task_id = task_row[0]
            print(f"✓ Using existing task id: {task_id}\n")
        
        # Test 1: Emit a task_created event
        print("Test 1: Emitting task_created event...")
        try:
            event = TaskEventService.emit(
                task_id=task_id,
                event_type=TaskEventType.TASK_CREATED,
                payload={
                    "created_by": "system",
                    "initial_status": "planned"
                },
                employee_id=1,
                source="web_app"
            )
            print(f"✓ Event created: {event.uuid} ({event.event_type})")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Emit a task_started event
        print("\nTest 2: Emitting task_started event...")
        try:
            event = TaskEventService.emit(
                task_id=task_id,
                event_type=TaskEventType.TASK_STARTED,
                payload={
                    "actual_start": datetime.utcnow().isoformat(),
                    "planned_start": datetime.utcnow().isoformat(),
                    "delay_minutes": 0,
                    "gps_lat": 49.6892,
                    "gps_lng": 14.0105
                },
                employee_id=1,
                source="mobile_app"
            )
            print(f"✓ Event created: {event.uuid} ({event.event_type})")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: Get task history
        print("\nTest 3: Getting task history...")
        try:
            history = TaskEventService.get_task_history(task_id, limit=10)
            print(f"✓ Retrieved {len(history)} events")
            for event in history:
                print(f"  - {event.event_type} at {event.occurred_at}")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 4: Get unprocessed events for AI
        print("\nTest 4: Getting unprocessed events for AI...")
        try:
            unprocessed = TaskEventService.get_unprocessed_for_ai(limit=10)
            print(f"✓ Found {len(unprocessed)} unprocessed events")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Analyze patterns
        print("\nTest 5: Analyzing event patterns...")
        try:
            patterns = TaskEventService.analyze_patterns(days=30)
            print(f"✓ Patterns analyzed:")
            print(f"  - Total events: {patterns['total_events']}")
            print(f"  - Event types: {dict(patterns['by_type'])}")
            print(f"  - Blocked count: {patterns['blocked_count']}")
            print(f"  - Deviation count: {patterns['deviation_count']}")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n=== All tests passed! ===")
        return True

if __name__ == '__main__':
    import uuid as uuid_lib
    success = test_task_events()
    sys.exit(0 if success else 1)
