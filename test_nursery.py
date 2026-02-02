#!/usr/bin/env python3
"""
Test script pro Nursery modul
Spustit: python3 test_nursery.py
"""

import sqlite3
from datetime import datetime

def test_nursery_module():
    """Test všech funkcí nursery modulu"""
    
    print("🌸 Testing Nursery Module\n")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect('app.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Test 1: Kontrola tabulek
        print("\n✓ Test 1: Kontrola struktury databáze")
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%nursery%'
        """)
        tables = cursor.fetchall()
        
        expected_tables = ['nursery_plants', 'nursery_watering_schedule', 'nursery_watering_log']
        found_tables = [t['name'] for t in tables]
        
        for table in expected_tables:
            if table in found_tables:
                print(f"  ✅ Tabulka {table} existuje")
            else:
                print(f"  ❌ Tabulka {table} CHYBÍ!")
        
        # Test 2: Kontrola dat
        print("\n✓ Test 2: Kontrola dat")
        cursor.execute("SELECT COUNT(*) as cnt FROM nursery_plants WHERE status='active'")
        plant_count = cursor.fetchone()['cnt']
        print(f"  ✅ Celkem aktivních rostlin: {plant_count}")
        
        # Test 3: Statistiky podle fází
        print("\n✓ Test 3: Statistiky podle růstových fází")
        cursor.execute("""
            SELECT 
                stage,
                COUNT(*) as count,
                SUM(quantity) as total_qty
            FROM nursery_plants
            WHERE status='active'
            GROUP BY stage
        """)
        for row in cursor.fetchall():
            print(f"  ✅ {row['stage']:15s}: {row['count']:3d} druhů, {row['total_qty']:5d} kusů")
        
        # Test 4: Hodnota skladu
        print("\n✓ Test 4: Hodnota skladu")
        cursor.execute("""
            SELECT 
                stage,
                ROUND(SUM(quantity * COALESCE(selling_price, 0)), 2) as value
            FROM nursery_plants
            WHERE status='active'
            GROUP BY stage
        """)
        total_value = 0
        for row in cursor.fetchall():
            value = row['value']
            total_value += value
            print(f"  ✅ {row['stage']:15s}: {value:10,.2f} Kč")
        print(f"  ✅ {'CELKEM':15s}: {total_value:10,.2f} Kč")
        
        # Test 5: Rostliny k zalití
        print("\n✓ Test 5: Plán zalévání")
        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM nursery_plants np
            JOIN nursery_watering_schedule nws ON np.id = nws.plant_id
            WHERE nws.next_watering <= date('now')
            AND np.status='active'
        """)
        watering_count = cursor.fetchone()['cnt']
        print(f"  ✅ Rostlin k zalití dnes: {watering_count}")
        
        # Test 6: Historie zalévání
        print("\n✓ Test 6: Historie zalévání")
        cursor.execute("SELECT COUNT(*) as cnt FROM nursery_watering_log")
        log_count = cursor.fetchone()['cnt']
        print(f"  ✅ Záznamů o zalévání: {log_count}")
        
        # Test 7: Nízký stav
        print("\n✓ Test 7: Nízký stav zásob")
        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM nursery_plants
            WHERE quantity < 10 AND stage='prodejní' AND status='active'
        """)
        low_stock_count = cursor.fetchone()['cnt']
        print(f"  ✅ Rostlin s nízkým stavem: {low_stock_count}")
        
        if low_stock_count > 0:
            cursor.execute("""
                SELECT species, variety, quantity, location
                FROM nursery_plants
                WHERE quantity < 10 AND stage='prodejní' AND status='active'
                ORDER BY quantity ASC
                LIMIT 5
            """)
            print("\n  Top 5 nejnižší stavy:")
            for row in cursor.fetchall():
                name = row['species']
                if row['variety']:
                    name += f" '{row['variety']}'"
                print(f"    • {name:40s} {row['quantity']:2d} ks  ({row['location']})")
        
        # Test 8: TOP 5 nejhodnotnější
        print("\n✓ Test 8: TOP 5 nejhodnotnějších rostlin")
        cursor.execute("""
            SELECT 
                species,
                variety,
                quantity,
                selling_price,
                quantity * COALESCE(selling_price, 0) as total_value
            FROM nursery_plants
            WHERE status='active' AND stage='prodejní'
            ORDER BY total_value DESC
            LIMIT 5
        """)
        for i, row in enumerate(cursor.fetchall(), 1):
            name = row['species']
            if row['variety']:
                name += f" '{row['variety']}'"
            print(f"  {i}. {name:40s} {row['quantity']:3d} ks × {row['selling_price']:6.2f} Kč = {row['total_value']:8,.2f} Kč")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Všechny testy prošly!\n")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Databázová chyba: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Neočekávaná chyba: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_nursery_module()
    exit(0 if success else 1)
