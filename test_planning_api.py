#!/usr/bin/env python3
"""
Quick test script for Planning Module API
Run this after migration to verify everything works
"""
import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:5000"

def test_daily_endpoint():
    """Test daily planning endpoint"""
    print("\n📅 Testing Daily Planning API...")
    today = date.today().isoformat()
    
    response = requests.get(f"{BASE_URL}/api/planning/daily/{today}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"  - Tasks: {data['summary']['tasks_count']}")
        print(f"  - Action Items: {data['summary']['action_items_count']}")
        print(f"  - Deliveries: {data['summary']['deliveries_count']}")
        print(f"  - Conflicts: {data['summary']['conflicts_count']}")
    else:
        print(f"❌ Failed: {response.text}")

def test_timeline_endpoint():
    """Test timeline endpoint"""
    print("\n📊 Testing Timeline API...")
    
    response = requests.get(f"{BASE_URL}/api/planning/timeline")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"  - Projects loaded: {len(data['timeline'])}")
        if data['timeline']:
            print(f"  - First project: {data['timeline'][0]['project']['name']}")
    else:
        print(f"❌ Failed: {response.text}")

def test_week_endpoint():
    """Test weekly planning endpoint"""
    print("\n📆 Testing Weekly Planning API...")
    
    response = requests.get(f"{BASE_URL}/api/planning/week")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"  - Employees: {len(data['employees'])}")
        print(f"  - Days in week: {len(data['days'])}")
    else:
        print(f"❌ Failed: {response.text}")

def test_costs_endpoint():
    """Test costs endpoint"""
    print("\n💰 Testing Costs API...")
    
    response = requests.get(f"{BASE_URL}/api/planning/costs")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"  - Projects with costs: {len(data['projects'])}")
        if data['projects']:
            proj = data['projects'][0]
            print(f"  - Example: {proj['name']} - Budget: {proj['budget']}, Spent: {proj['spent']}")
    else:
        print(f"❌ Failed: {response.text}")

def test_frontend_pages():
    """Test that frontend pages are accessible"""
    print("\n🌐 Testing Frontend Pages...")
    
    pages = [
        "/planning/daily",
        "/planning/timeline",
        "/planning/week",
        "/planning/costs"
    ]
    
    for page in pages:
        response = requests.get(f"{BASE_URL}{page}")
        status = "✅" if response.status_code == 200 else "❌"
        print(f"  {status} {page} - Status: {response.status_code}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Planning Module API Tests")
    print("=" * 60)
    print(f"Base URL: {BASE_URL}")
    print("\nMake sure your Flask app is running!")
    print("If not, run: python3 main.py")
    print("=" * 60)
    
    try:
        # Check if server is running
        response = requests.get(BASE_URL, timeout=2)
        print("✅ Server is running!\n")
        
        # Run tests
        test_daily_endpoint()
        test_timeline_endpoint()
        test_week_endpoint()
        test_costs_endpoint()
        test_frontend_pages()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to Flask server")
        print("Please start the server first: python3 main.py")
    except Exception as e:
        print(f"❌ ERROR: {e}")
