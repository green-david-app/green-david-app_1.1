#!/usr/bin/env python3
"""
Test script for Task Dependencies system
"""
import sys
import os
from datetime import datetime
import uuid as uuid_lib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app, get_db
import importlib.util

# Import services directly
_dependency_graph_path = "app/services/dependency_graph_service.py"
spec = importlib.util.spec_from_file_location("dependency_graph_service", _dependency_graph_path)
dependency_graph_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dependency_graph_module)
DependencyGraphService = dependency_graph_module.DependencyGraphService

_risk_propagation_path = "app/services/risk_propagation_service.py"
spec = importlib.util.spec_from_file_location("risk_propagation_service", _risk_propagation_path)
risk_propagation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(risk_propagation_module)
RiskPropagationService = risk_propagation_module.RiskPropagationService

_dependency_types_path = "app/utils/dependency_types.py"
spec = importlib.util.spec_from_file_location("dependency_types", _dependency_types_path)
dependency_types_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dependency_types_module)
DependencyType = dependency_types_module.DependencyType

def test_task_dependencies():
    """Test Task Dependencies functionality"""
    with app.app_context():
        print("=== Testing Task Dependencies System ===\n")
        
        db = get_db()
        
        # Get or create test tasks
        task_rows = db.execute("SELECT id FROM tasks LIMIT 2").fetchall()
        
        if len(task_rows) < 2:
            print("⚠ Creating test tasks...")
            job_id = 1
            employee_id = 1
            
            # Create task 1
            db.execute("""
                INSERT INTO tasks (
                    uuid, title, description, task_type, job_id, assigned_employee_id, created_by_id,
                    planned_start, planned_end, planned_duration_minutes, location_type, expected_outcome,
                    status, integrity_score, integrity_flags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid_lib.uuid4()),
                "Task A - Prepare Site",
                "Prepare site for work",
                "work",
                job_id,
                employee_id,
                employee_id,
                datetime.utcnow().isoformat(),
                (datetime.utcnow().replace(hour=12)).isoformat(),
                240,
                "job_site",
                "Site prepared",
                "completed",
                100.0,
                '[]'
            ))
            db.commit()
            task1_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Create task 2
            db.execute("""
                INSERT INTO tasks (
                    uuid, title, description, task_type, job_id, assigned_employee_id, created_by_id,
                    planned_start, planned_end, planned_duration_minutes, location_type, expected_outcome,
                    status, integrity_score, integrity_flags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid_lib.uuid4()),
                "Task B - Install Plants",
                "Install plants after site preparation",
                "work",
                job_id,
                employee_id,
                employee_id,
                (datetime.utcnow().replace(hour=13)).isoformat(),
                (datetime.utcnow().replace(hour=17)).isoformat(),
                240,
                "job_site",
                "Plants installed",
                "planned",
                100.0,
                '[]'
            ))
            db.commit()
            task2_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            print(f"✓ Created test tasks: {task1_id} and {task2_id}\n")
        else:
            task1_id = task_rows[0][0]
            task2_id = task_rows[1][0]
            print(f"✓ Using existing tasks: {task1_id} and {task2_id}\n")
        
        # Test 1: Create dependency
        print("Test 1: Creating task dependency...")
        try:
            db.execute("""
                INSERT INTO task_dependencies (
                    predecessor_task_id, successor_task_id, dependency_type,
                    is_critical, is_hard, status, risk_weight
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task1_id,
                task2_id,
                DependencyType.TEMPORAL_FINISH_TO_START.value,
                1,  # is_critical
                1,  # is_hard
                'satisfied',
                1.0
            ))
            db.commit()
            dep_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"  ✓ Created dependency: {dep_id}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Get job dependencies
        print("\nTest 2: Getting job dependencies...")
        try:
            job_row = db.execute("SELECT job_id FROM tasks WHERE id = ?", (task1_id,)).fetchone()
            job_id = job_row[0] if job_row else 1
            
            deps = DependencyGraphService.get_job_dependencies(job_id)
            print(f"  ✓ Found {len(deps)} dependencies for job {job_id}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: Build adjacency list
        print("\nTest 3: Building adjacency list...")
        try:
            adj_list = DependencyGraphService.build_adjacency_list(job_id)
            print(f"  ✓ Adjacency list: {adj_list}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 4: Detect cycles
        print("\nTest 4: Detecting cycles...")
        try:
            cycles = DependencyGraphService.detect_cycles(job_id)
            print(f"  ✓ Found {len(cycles)} cycles: {cycles}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Topological sort
        print("\nTest 5: Topological sort...")
        try:
            topo_order = DependencyGraphService.topological_sort(job_id)
            if topo_order:
                print(f"  ✓ Topological order: {topo_order}")
            else:
                print(f"  ⚠ No valid topological order (cycles detected)")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 6: Get downstream tasks
        print("\nTest 6: Getting downstream tasks...")
        try:
            downstream = DependencyGraphService.get_downstream_tasks(task1_id)
            print(f"  ✓ Downstream tasks: {len(downstream)}")
            for task in downstream:
                print(f"    - {task['title']} (depth: {task['depth']})")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 7: Get upstream tasks
        print("\nTest 7: Getting upstream tasks...")
        try:
            upstream = DependencyGraphService.get_upstream_tasks(task2_id)
            print(f"  ✓ Upstream tasks: {len(upstream)}")
            for task in upstream:
                print(f"    - {task['title']} (depth: {task['depth']})")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 8: Check can start
        print("\nTest 8: Checking if task can start...")
        try:
            can_start = DependencyGraphService.check_can_start(task2_id)
            print(f"  ✓ Can start: {can_start['can_start']}")
            print(f"  ✓ Blocking dependencies: {len(can_start['blocking_dependencies'])}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 9: Update dependency status
        print("\nTest 9: Updating dependency status...")
        try:
            updated = DependencyGraphService.update_dependency_status(dep_id)
            if updated:
                print(f"  ✓ Updated dependency status: {updated.get('status')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 10: Propagate delay
        print("\nTest 10: Propagating delay...")
        try:
            result = RiskPropagationService.propagate_delay(task1_id, 60)
            print(f"  ✓ Delay propagated: {result.get('delay_minutes')} minutes")
            print(f"  ✓ Affected tasks: {len(result.get('affected_tasks', []))}")
            print(f"  ✓ Mitigation options: {len(result.get('mitigation_options', []))}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 11: Calculate job risk score
        print("\nTest 11: Calculating job risk score...")
        try:
            risk_score = RiskPropagationService.calculate_job_risk_score(job_id)
            print(f"  ✓ Risk score: {risk_score.get('risk_score', 0):.1f}")
            print(f"  ✓ Risk level: {risk_score.get('risk_level', 'unknown')}")
            print(f"  ✓ Risk factors: {len(risk_score.get('risk_factors', []))}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n=== All tests passed! ===")
        return True

if __name__ == '__main__':
    success = test_task_dependencies()
    sys.exit(0 if success else 1)
