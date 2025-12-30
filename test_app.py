#!/usr/bin/env python3
"""
Test Suite - Green David App
Základní testy pro validaci bezpečnostních oprav
"""

import sys
import os

# Přidat main.py do path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test že všechny importy fungují"""
    print("✓ Testing imports...")
    try:
        import main
        print("  ✅ Main module imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_env_validation():
    """Test validace environment variables"""
    print("\n✓ Testing environment validation...")
    
    # Test že SECRET_KEY je vyžadován v produkci
    os.environ['FLASK_ENV'] = 'production'
    os.environ.pop('SECRET_KEY', None)
    
    try:
        import importlib
        import main as m
        importlib.reload(m)
        print("  ❌ Should have raised ValueError for missing SECRET_KEY")
        return False
    except ValueError as e:
        if "SECRET_KEY must be set" in str(e):
            print("  ✅ Correctly validates SECRET_KEY in production")
            return True
        else:
            print(f"  ❌ Wrong error: {e}")
            return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False
    finally:
        # Cleanup
        os.environ.pop('FLASK_ENV', None)


def test_validation_functions():
    """Test validačních funkcí"""
    print("\n✓ Testing validation functions...")
    
    # Reload s dev prostředím
    os.environ['FLASK_ENV'] = 'development'
    import importlib
    import main
    importlib.reload(main)
    
    # Test validate_hours
    valid, result = main.validate_hours(8)
    if valid and result == 8.0:
        print("  ✅ validate_hours: valid input")
    else:
        print(f"  ❌ validate_hours failed: {result}")
        return False
    
    valid, result = main.validate_hours(25)
    if not valid:
        print("  ✅ validate_hours: rejects >24 hours")
    else:
        print("  ❌ validate_hours should reject 25 hours")
        return False
    
    valid, result = main.validate_hours(-5)
    if not valid:
        print("  ✅ validate_hours: rejects negative hours")
    else:
        print("  ❌ validate_hours should reject negative hours")
        return False
    
    # Test validate_email
    valid, result = main.validate_email("test@example.com")
    if valid and result == "test@example.com":
        print("  ✅ validate_email: valid email")
    else:
        print(f"  ❌ validate_email failed: {result}")
        return False
    
    valid, result = main.validate_email("invalid.email")
    if not valid:
        print("  ✅ validate_email: rejects invalid email")
    else:
        print("  ❌ validate_email should reject invalid email")
        return False
    
    # Test sanitize_filename
    safe = main.sanitize_filename("../../etc/passwd")
    if "/" not in safe and ".." not in safe:
        print("  ✅ sanitize_filename: prevents path traversal")
    else:
        print(f"  ❌ sanitize_filename unsafe: {safe}")
        return False
    
    return True


def test_date_normalization():
    """Test normalizace datumů"""
    print("\n✓ Testing date normalization...")
    
    os.environ['FLASK_ENV'] = 'development'
    import importlib
    import main
    importlib.reload(main)
    
    # Test ISO formát
    result = main._normalize_date("2024-12-30")
    if result == "2024-12-30":
        print("  ✅ ISO format preserved")
    else:
        print(f"  ❌ ISO format failed: {result}")
        return False
    
    # Test český formát
    result = main._normalize_date("30.12.2024")
    if result == "2024-12-30":
        print("  ✅ Czech format converted")
    else:
        print(f"  ❌ Czech format failed: {result}")
        return False
    
    # Test s mezerami
    result = main._normalize_date("30 12 2024")
    if result == "2024-12-30":
        print("  ✅ Space-separated format converted")
    else:
        print(f"  ❌ Space format failed: {result}")
        return False
    
    return True


def test_database_schema():
    """Test že databázové schéma se vytvoří správně"""
    print("\n✓ Testing database schema...")
    
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DB_PATH'] = ':memory:'  # In-memory DB
    
    import importlib
    import main
    importlib.reload(main)
    
    try:
        with main.app.app_context():
            db = main.get_db()
            
            # Zkontrolovat že tabulky existují
            tables = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            
            table_names = [t['name'] for t in tables]
            required_tables = [
                'users', 'employees', 'jobs', 'job_assignments',
                'job_materials', 'job_tools', 'tasks', 'timesheets',
                'calendar_events'
            ]
            
            missing = [t for t in required_tables if t not in table_names]
            if missing:
                print(f"  ❌ Missing tables: {missing}")
                return False
            
            print(f"  ✅ All {len(required_tables)} tables created")
            
            # Zkontrolovat indexy
            indexes = db.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            ).fetchall()
            
            if len(indexes) >= 6:  # Mělo by jich být min. 6
                print(f"  ✅ Performance indexes created ({len(indexes)})")
            else:
                print(f"  ⚠️  Only {len(indexes)} indexes found")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Database schema test failed: {e}")
        return False


def test_admin_creation():
    """Test vytvoření admin uživatele"""
    print("\n✓ Testing admin user creation...")
    
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DB_PATH'] = ':memory:'
    os.environ['ADMIN_EMAIL'] = 'test@example.com'
    os.environ['ADMIN_PASSWORD'] = 'testpass123'
    
    import importlib
    import main
    importlib.reload(main)
    
    try:
        with main.app.app_context():
            db = main.get_db()
            main.ensure_schema()
            main.seed_admin()
            
            # Zkontrolovat že admin existuje
            admin = db.execute(
                "SELECT * FROM users WHERE email=?",
                ('test@example.com',)
            ).fetchone()
            
            if not admin:
                print("  ❌ Admin user not created")
                return False
            
            print("  ✅ Admin user created")
            
            # Zkontrolovat že heslo je hashované
            if admin['password_hash'] == 'testpass123':
                print("  ❌ Password not hashed!")
                return False
            
            print("  ✅ Password properly hashed")
            
            # Zkontrolovat že admin má správnou roli
            if admin['role'] != 'admin':
                print(f"  ❌ Wrong role: {admin['role']}")
                return False
            
            print("  ✅ Admin has correct role")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Admin creation test failed: {e}")
        return False
    finally:
        # Cleanup
        os.environ.pop('ADMIN_EMAIL', None)
        os.environ.pop('ADMIN_PASSWORD', None)


def run_all_tests():
    """Spustit všechny testy"""
    print("=" * 70)
    print("🧪 GREEN DAVID APP - TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Imports", test_imports),
        ("Environment Validation", test_env_validation),
        ("Validation Functions", test_validation_functions),
        ("Date Normalization", test_date_normalization),
        ("Database Schema", test_database_schema),
        ("Admin Creation", test_admin_creation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("=" * 70)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
