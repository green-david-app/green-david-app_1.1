#!/usr/bin/env python3
"""
Test script for Task API endpoints
"""
import sys
import os
import json
from datetime import datetime
import uuid as uuid_lib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app

def test_task_api():
    """Test Task API endpoints"""
    with app.test_client() as client:
        print("=== Testing Task API ===\n")
        
        # Test 1: Create task
        print("Test 1: Creating task via API...")
        try:
            task_data = {
                "job_id": 1,
                "title": "Test Task via API",
                "task_type": "work",
                "assigned_employee_id": 1,
                "planned_start": datetime.utcnow().isoformat(),
                "planned_end": (datetime.utcnow().replace(hour=17)).isoformat(),
                "location_type": "job_site",
                "expected_outcome": "Complete test task via API",
                "description": "Testing API endpoint",
                "priority": "normal",
                "materials": [
                    {
                        "material_name": "Test Material",
                        "planned_quantity": 10.0,
                        "unit": "ks"
                    }
                ]
            }
            
            response = client.post('/api/tasks', 
                                  json=task_data,
                                  content_type='application/json')
            
            if response.status_code == 201:
                result = json.loads(response.data)
                print(f"  ✓ Task created: {result.get('data', {}).get('task', {}).get('id')}")
                task_id = result.get('data', {}).get('task', {}).get('id')
            else:
                print(f"  ✗ Error: {response.status_code}")
                print(f"  Response: {response.data.decode()}")
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 2: Get task
        print("\nTest 2: Getting task detail...")
        try:
            response = client.get(f'/api/tasks/{task_id}')
            if response.status_code == 200:
                result = json.loads(response.data)
                print(f"  ✓ Task retrieved: {result.get('data', {}).get('title', 'N/A')}")
            else:
                print(f"  ✗ Error: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
        
        # Test 3: Start task
        print("\nTest 3: Starting task...")
        try:
            response = client.post(f'/api/tasks/{task_id}/start',
                                  json={'gps_lat': 49.6892, 'gps_lng': 14.0105},
                                  content_type='application/json')
            if response.status_code == 200:
                result = json.loads(response.data)
                print(f"  ✓ Task started: {result.get('data', {}).get('task', {}).get('status')}")
            else:
                print(f"  ✗ Error: {response.status_code}")
                print(f"  Response: {response.data.decode()}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # Test 4: Complete task
        print("\nTest 4: Completing task...")
        try:
            response = client.post(f'/api/tasks/{task_id}/complete',
                                  json={
                                      'completion_state': 'done',
                                      'completion_percentage': 100,
                                      'gps_lat': 49.6892,
                                      'gps_lng': 14.0105
                                  },
                                  content_type='application/json')
            if response.status_code == 200:
                result = json.loads(response.data)
                print(f"  ✓ Task completed: {result.get('data', {}).get('task', {}).get('status')}")
            else:
                print(f"  ✗ Error: {response.status_code}")
                print(f"  Response: {response.data.decode()}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # Test 5: Get job tasks
        print("\nTest 5: Getting job tasks...")
        try:
            response = client.get('/api/tasks/job/1')
            if response.status_code == 200:
                result = json.loads(response.data)
                print(f"  ✓ Found {result.get('data', {}).get('count', 0)} tasks for job")
            else:
                print(f"  ✗ Error: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        # Test 6: Get my today tasks
        print("\nTest 6: Getting my today tasks...")
        try:
            response = client.get('/api/tasks/my-today?employee_id=1')
            if response.status_code == 200:
                result = json.loads(response.data)
                print(f"  ✓ Found {result.get('data', {}).get('count', 0)} tasks for today")
            else:
                print(f"  ✗ Error: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        
        print("\n=== API tests completed! ===")
        return True

if __name__ == '__main__':
    success = test_task_api()
    sys.exit(0 if success else 1)
