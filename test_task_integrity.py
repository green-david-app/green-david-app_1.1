#!/usr/bin/env python3
"""
Test script for Task Integrity Score system
"""
import sys
import os
from datetime import datetime
import uuid as uuid_lib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, get_db
import importlib.util

# Import services directly without going through app module
_integrity_service_path = "app/services/task_integrity_service.py"
spec = importlib.util.spec_from_file_location("task_integrity_service", _integrity_service_path)
integrity_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integrity_service_module)
TaskIntegrityService = integrity_service_module.TaskIntegrityService
IntegrityMetric = integrity_service_module.IntegrityMetric

_aggregated_service_path = "app/services/aggregated_integrity_service.py"
spec = importlib.util.spec_from_file_location("aggregated_integrity_service", _aggregated_service_path)
aggregated_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aggregated_service_module)
AggregatedIntegrityService = aggregated_service_module.AggregatedIntegrityService

def test_task_integrity():
    """Test Task Integrity Score functionality"""
    with app.app_context():
        print("=== Testing Task Integrity Score System ===\n")
        
        db = get_db()
        
        # Get or create a test task
        task_row = db.execute("SELECT id FROM tasks LIMIT 1").fetchone()
        
        if not task_row:
            print("⚠ No tasks found. Creating a test task...")
            db.execute("""
                INSERT INTO tasks (
                    uuid, title, description, task_type, job_id, assigned_employee_id, created_by_id,
                    planned_start, planned_end, planned_duration_minutes, location_type, expected_outcome,
                    status, integrity_score, integrity_flags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid_lib.uuid4()),
                "Test Task for Integrity",
                "Testing integrity score calculation",
                "work",
                1,
                1,
                1,
                datetime.utcnow().isoformat(),
                (datetime.utcnow().replace(hour=17)).isoformat(),
                480,
                "job_site",
                "Complete test task",
                "completed",
                100.0,
                '[]'
            ))
            db.commit()
            task_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"✓ Created test task with id: {task_id}\n")
        else:
            task_id = task_row[0]
            print(f"✓ Using existing task id: {task_id}\n")
        
        # Get task data
        task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        task_dict = dict(task_row)
        
        # Test 1: Calculate individual metrics
        print("Test 1: Calculating individual integrity metrics...")
        try:
            data_completeness_score, data_flags = TaskIntegrityService.calculate_data_completeness(task_dict)
            print(f"  ✓ Data Completeness: {data_completeness_score:.1f} (flags: {len(data_flags)})")
            
            time_accuracy_score, time_flags = TaskIntegrityService.calculate_time_accuracy(task_dict)
            print(f"  ✓ Time Accuracy: {time_accuracy_score:.1f} (flags: {len(time_flags)})")
            
            evidence_score, evidence_flags = TaskIntegrityService.calculate_evidence_quality(task_dict, evidences=[])
            print(f"  ✓ Evidence Quality: {evidence_score:.1f} (flags: {len(evidence_flags)})")
            
            material_score, material_flags = TaskIntegrityService.calculate_material_consistency(task_dict, materials=[])
            print(f"  ✓ Material Consistency: {material_score:.1f} (flags: {len(material_flags)})")
            
            process_score, process_flags = TaskIntegrityService.calculate_process_compliance(task_dict)
            print(f"  ✓ Process Compliance: {process_score:.1f} (flags: {len(process_flags)})")
            
            location_score, location_flags = TaskIntegrityService.calculate_location_validity(task_dict)
            print(f"  ✓ Location Validity: {location_score:.1f} (flags: {len(location_flags)})")
            
            dependency_score, dependency_flags = TaskIntegrityService.calculate_dependency_integrity(task_dict)
            print(f"  ✓ Dependency Integrity: {dependency_score:.1f} (flags: {len(dependency_flags)})")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Calculate full integrity score
        print("\nTest 2: Calculating full integrity score...")
        try:
            full_score, all_flags, breakdown = TaskIntegrityService.calculate_full_integrity(
                task_dict, evidences=[], materials=[]
            )
            print(f"  ✓ Full Integrity Score: {full_score:.1f}")
            print(f"  ✓ Total Flags: {len(all_flags)}")
            print(f"  ✓ Breakdown: {breakdown}")
            
            level = TaskIntegrityService.get_integrity_level(full_score)
            print(f"  ✓ Integrity Level: {level}")
            
            trust_level = TaskIntegrityService.get_ai_trust_level(full_score)
            print(f"  ✓ AI Trust Level: {trust_level:.2f}")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: Recalculate and update
        print("\nTest 3: Recalculating and updating task integrity...")
        try:
            updated_task = TaskIntegrityService.recalculate_and_update(task_id, emit_events=False)
            new_score = updated_task.get('integrity_score', 0)
            print(f"  ✓ Updated Integrity Score: {new_score:.1f}")
            
            # Check integrity_flags
            flags_str = updated_task.get('integrity_flags', '[]')
            flags = json.loads(flags_str) if isinstance(flags_str, str) else flags_str
            print(f"  ✓ Integrity Flags: {len(flags)} flags")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 4: Job integrity score
        print("\nTest 4: Calculating job integrity score...")
        try:
            job_id = task_dict.get('job_id', 1)
            job_integrity = AggregatedIntegrityService.job_integrity_score(job_id)
            print(f"  ✓ Job ID: {job_integrity['job_id']}")
            print(f"  ✓ Average Score: {job_integrity.get('average_score', 'N/A')}")
            print(f"  ✓ Task Count: {job_integrity['task_count']}")
            print(f"  ✓ Distribution: {job_integrity.get('distribution', {})}")
            print(f"  ✓ AI Trust Level: {job_integrity.get('ai_trust_level', 0):.2f}")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: System integrity dashboard
        print("\nTest 5: Getting system integrity dashboard...")
        try:
            dashboard = AggregatedIntegrityService.system_integrity_dashboard()
            print(f"  ✓ Total Tasks: {dashboard.get('total_tasks', 0)}")
            print(f"  ✓ Average Score: {dashboard.get('average_score', 'N/A')}")
            print(f"  ✓ Distribution: {dashboard.get('distribution', {})}")
            print(f"  ✓ Top Issues: {len(dashboard.get('top_issues', []))} issues")
            print(f"  ✓ AI System Trust: {dashboard.get('ai_system_trust', 0):.2f}")
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n=== All tests passed! ===")
        return True

if __name__ == '__main__':
    import json
    success = test_task_integrity()
    sys.exit(0 if success else 1)
