#!/usr/bin/env python3
"""
Test script for AI Operator Task Interface
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
import importlib.util

# Import AI Operator Interface
_ai_interface_path = "app/services/ai_operator_task_interface.py"
spec = importlib.util.spec_from_file_location("ai_operator_task_interface", _ai_interface_path)
ai_interface_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_interface_module)
AIOperatorTaskInterface = ai_interface_module.AIOperatorTaskInterface

def test_ai_operator():
    """Test AI Operator functionality"""
    with app.app_context():
        print("=== Testing AI Operator Task Interface ===\n")
        
        # Test 1: Get job situation report
        print("Test 1: Getting job situation report...")
        try:
            from main import get_db
            db = get_db()
            job_row = db.execute("SELECT id FROM jobs LIMIT 1").fetchone()
            
            if job_row:
                job_id = job_row[0]
                report = AIOperatorTaskInterface.get_job_situation_report(job_id)
                print(f"  ✓ Report generated for job {job_id}")
                print(f"  ✓ Task overview: {report.get('task_overview', {}).get('total', 0)} tasks")
                print(f"  ✓ AI attention items: {len(report.get('ai_attention_required', []))}")
            else:
                print("  ⚠ No jobs found in database")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Detect bottlenecks
        print("\nTest 2: Detecting bottlenecks...")
        try:
            bottlenecks = AIOperatorTaskInterface.detect_bottlenecks({'all': True})
            print(f"  ✓ Found {len(bottlenecks)} bottlenecks")
            if bottlenecks:
                print(f"  ✓ Critical bottlenecks: {sum(1 for b in bottlenecks if b['severity'] == 'critical')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: Analyze deviation patterns
        print("\nTest 3: Analyzing deviation patterns...")
        try:
            patterns = AIOperatorTaskInterface.analyze_deviation_patterns({}, min_occurrences=2)
            print(f"  ✓ Found {len(patterns)} patterns")
            if patterns:
                print(f"  ✓ Top pattern: {patterns[0].get('reason', 'N/A')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 4: Generate daily briefing
        print("\nTest 4: Generating daily briefing...")
        try:
            briefing = AIOperatorTaskInterface.generate_daily_briefing()
            print(f"  ✓ Briefing generated for {briefing.get('date')}")
            print(f"  ✓ Executive summary: {briefing.get('executive_summary', '')[:100]}...")
            print(f"  ✓ Attention items: {len(briefing.get('attention_items', []))}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 5: Get employee performance context
        print("\nTest 5: Getting employee performance context...")
        try:
            db = get_db()
            emp_row = db.execute("SELECT id FROM employees LIMIT 1").fetchone()
            
            if emp_row:
                emp_id = emp_row[0]
                context = AIOperatorTaskInterface.get_employee_performance_context(emp_id, days=30)
                print(f"  ✓ Context generated for employee {emp_id}")
                print(f"  ✓ Task statistics: {context.get('task_statistics', {}).get('total_assigned', 0)} tasks")
                print(f"  ✓ Recommendations: {len(context.get('system_recommendations', []))}")
            else:
                print("  ⚠ No employees found in database")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n=== All tests passed! ===")
        return True

if __name__ == '__main__':
    success = test_ai_operator()
    sys.exit(0 if success else 1)
