"""
Warehouse Extended Features
- Skladové lokace
- Přiřazování k zakázkám (movements)
- Vracení materiálu
- Rezervace
- Expirační datumy/Šarže
- Přejmenování/Slučování položek
- Inventurní režim
"""
from flask import jsonify, request, session
from datetime import datetime, date, timedelta
import json

get_db = None  # Will be set from main.py

# ================================================================
# DATABASE MIGRATIONS
# ================================================================

def apply_warehouse_migrations():
    """Aplikuje všechny warehouse migrace"""
    db = get_db()
    
    # 1. WAREHOUSE ITEMS - rozšíření základní tabulky
    db.executescript("""
    CREATE TABLE IF NOT EXISTS warehouse_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        sku TEXT DEFAULT '',
        category TEXT DEFAULT '',
        qty REAL NOT NULL DEFAULT 0,
        unit TEXT NOT NULL DEFAULT 'ks',
        price REAL DEFAULT 0,
        minStock REAL DEFAULT 10,
        image TEXT DEFAULT '',
        note TEXT DEFAULT '',
        
        -- NOVÉ SLOUPCE
        location TEXT DEFAULT '',              -- Skladová lokace: "Sklad A-1-B"
        batch_number TEXT DEFAULT '',          -- Číslo šarže
        expiration_date TEXT DEFAULT '',       -- Datum expirace
        
        status TEXT NOT NULL DEFAULT 'active', -- active, merged, deleted
        merged_into INTEGER,                   -- ID položky, do které byla sloučena
        
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    
    -- 2. WAREHOUSE LOCATIONS - справочник локацій
    CREATE TABLE IF NOT EXISTS warehouse_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL UNIQUE,             -- "A-1-B" nebo "Sklad-Regál-Police"
        name TEXT NOT NULL,                     -- "Sklad A, Regál 1, Police B"
        description TEXT DEFAULT '',
        capacity REAL DEFAULT 0,                -- Maximální kapacita (volitelné)
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    
    -- 3. WAREHOUSE MOVEMENTS - veškerý pohyb materiálu
    CREATE TABLE IF NOT EXISTS warehouse_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        movement_type TEXT NOT NULL,           -- in, out, return, transfer, adjustment, inventory
        qty REAL NOT NULL,
        
        -- Souvislost s zakázkou
        job_id INTEGER,                        -- Pro out/return/transfer
        
        -- Lokace
        from_location TEXT DEFAULT '',
        to_location TEXT DEFAULT '',
        
        -- Metadata
        employee_id INTEGER,                   -- Kdo provedl
        note TEXT DEFAULT '',
        batch_number TEXT DEFAULT '',          -- Pro tracking šarží
        
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        
        FOREIGN KEY (item_id) REFERENCES warehouse_items(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (employee_id) REFERENCES employees(id)
    );
    
    -- 4. WAREHOUSE RESERVATIONS - rezervace materiálu
    CREATE TABLE IF NOT EXISTS warehouse_reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER NOT NULL,
        job_id INTEGER,
        qty REAL NOT NULL,
        reserved_by INTEGER,                   -- employee_id
        reserved_from TEXT NOT NULL,           -- Datum od
        reserved_until TEXT NOT NULL,          -- Datum do
        status TEXT NOT NULL DEFAULT 'active', -- active, completed, cancelled
        note TEXT DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        
        FOREIGN KEY (item_id) REFERENCES warehouse_items(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id),
        FOREIGN KEY (reserved_by) REFERENCES employees(id)
    );
    
    -- 5. WAREHOUSE INVENTORY - inventurní záznamy
    CREATE TABLE IF NOT EXISTS warehouse_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inventory_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'in_progress', -- in_progress, completed, cancelled
        started_by INTEGER,
        completed_by INTEGER,
        note TEXT DEFAULT '',
        
        started_at TEXT NOT NULL DEFAULT (datetime('now')),
        completed_at TEXT DEFAULT '',
        
        FOREIGN KEY (started_by) REFERENCES employees(id),
        FOREIGN KEY (completed_by) REFERENCES employees(id)
    );
    
    -- 6. WAREHOUSE INVENTORY ITEMS - položky v inventuře
    CREATE TABLE IF NOT EXISTS warehouse_inventory_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inventory_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        
        expected_qty REAL NOT NULL,            -- Očekávané množství (z systému)
        counted_qty REAL,                      -- Napočítané množství
        difference REAL,                       -- Rozdíl
        
        location TEXT DEFAULT '',
        counted_by INTEGER,                    -- employee_id
        counted_at TEXT,
        note TEXT DEFAULT '',
        
        FOREIGN KEY (inventory_id) REFERENCES warehouse_inventory(id),
        FOREIGN KEY (item_id) REFERENCES warehouse_items(id),
        FOREIGN KEY (counted_by) REFERENCES employees(id)
    );
    
    -- 7. WAREHOUSE MERGE HISTORY - historie slučování
    CREATE TABLE IF NOT EXISTS warehouse_merge_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_item_id INTEGER NOT NULL,       -- Původní položka (zrušená)
        target_item_id INTEGER NOT NULL,       -- Cílová položka (zachovaná)
        merged_by INTEGER,
        merged_at TEXT NOT NULL DEFAULT (datetime('now')),
        note TEXT DEFAULT '',
        
        -- Backup dat ze source položky
        source_data_json TEXT,
        
        FOREIGN KEY (source_item_id) REFERENCES warehouse_items(id),
        FOREIGN KEY (target_item_id) REFERENCES warehouse_items(id),
        FOREIGN KEY (merged_by) REFERENCES employees(id)
    );
    
    -- INDEXY pro výkon
    CREATE INDEX IF NOT EXISTS idx_warehouse_movements_item ON warehouse_movements(item_id);
    CREATE INDEX IF NOT EXISTS idx_warehouse_movements_job ON warehouse_movements(job_id);
    CREATE INDEX IF NOT EXISTS idx_warehouse_movements_type ON warehouse_movements(movement_type);
    CREATE INDEX IF NOT EXISTS idx_warehouse_movements_date ON warehouse_movements(created_at);
    
    CREATE INDEX IF NOT EXISTS idx_warehouse_reservations_item ON warehouse_reservations(item_id);
    CREATE INDEX IF NOT EXISTS idx_warehouse_reservations_job ON warehouse_reservations(job_id);
    CREATE INDEX IF NOT EXISTS idx_warehouse_reservations_status ON warehouse_reservations(status);
    
    CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_items_inventory ON warehouse_inventory_items(inventory_id);
    CREATE INDEX IF NOT EXISTS idx_warehouse_inventory_items_item ON warehouse_inventory_items(item_id);
    """)
    
    db.commit()
    print("[WAREHOUSE] Migrations applied successfully")


# ================================================================
# API ENDPOINTS
# ================================================================

# ------------ LOCATIONS ------------

def get_locations():
    """GET /api/warehouse/locations"""
    try:
        db = get_db()
        locations = db.execute("""
            SELECT l.*, 
                   COUNT(DISTINCT wi.id) as items_count
            FROM warehouse_locations l
            LEFT JOIN warehouse_items wi ON wi.location = l.code AND wi.status = 'active'
            GROUP BY l.id
            ORDER BY l.code
        """).fetchall()
        
        return jsonify({
            'success': True,
            'locations': [dict(loc) for loc in locations]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def create_location():
    """POST /api/warehouse/locations"""
    try:
        data = request.json
        db = get_db()
        
        cursor = db.execute("""
            INSERT INTO warehouse_locations (code, name, description, capacity)
            VALUES (?, ?, ?, ?)
        """, (
            data.get('code', ''),
            data.get('name', ''),
            data.get('description', ''),
            float(data.get('capacity', 0))
        ))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'location_id': cursor.lastrowid
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def update_location(location_id):
    """PATCH /api/warehouse/locations/<id>"""
    try:
        data = request.json
        db = get_db()
        
        db.execute("""
            UPDATE warehouse_locations
            SET name = ?, description = ?, capacity = ?
            WHERE id = ?
        """, (
            data.get('name', ''),
            data.get('description', ''),
            float(data.get('capacity', 0)),
            location_id
        ))
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def delete_location(location_id):
    """DELETE /api/warehouse/locations/<id>"""
    try:
        db = get_db()
        
        # Zkontroluj, zda nejsou položky na této lokaci
        items = db.execute("""
            SELECT COUNT(*) as cnt
            FROM warehouse_items
            WHERE location = (SELECT code FROM warehouse_locations WHERE id = ?)
            AND status = 'active'
        """, (location_id,)).fetchone()
        
        if items['cnt'] > 0:
            return jsonify({
                'success': False,
                'error': f'Na této lokaci je {items["cnt"]} aktivních položek. Nejprve je přesuňte.'
            }), 400
        
        db.execute("DELETE FROM warehouse_locations WHERE id = ?", (location_id,))
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------ MOVEMENTS (Přiřazování k zakázkám) ------------

def get_movements():
    """GET /api/warehouse/movements?item_id=X&job_id=Y"""
    try:
        db = get_db()
        item_id = request.args.get('item_id')
        job_id = request.args.get('job_id')
        limit = int(request.args.get('limit', 100))
        
        query = """
            SELECT wm.*,
                   wi.name as item_name,
                   wi.unit as item_unit,
                   j.title as job_title,
                   e.name as employee_name
            FROM warehouse_movements wm
            LEFT JOIN warehouse_items wi ON wm.item_id = wi.id
            LEFT JOIN jobs j ON wm.job_id = j.id
            LEFT JOIN employees e ON wm.employee_id = e.id
            WHERE 1=1
        """
        params = []
        
        if item_id:
            query += " AND wm.item_id = ?"
            params.append(int(item_id))
        
        if job_id:
            query += " AND wm.job_id = ?"
            params.append(int(job_id))
        
        query += " ORDER BY wm.created_at DESC LIMIT ?"
        params.append(limit)
        
        movements = db.execute(query, params).fetchall()
        
        return jsonify({
            'success': True,
            'movements': [dict(m) for m in movements]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def create_movement():
    """POST /api/warehouse/movements
    
    Types:
    - in: Příjem (nákup)
    - out: Výdej na zakázku
    - return: Vrácení ze zakázky
    - transfer: Přesun mezi lokacemi
    - adjustment: Korekce (inventura, ztráta)
    - inventory: Inventurní záznam
    """
    try:
        data = request.json
        db = get_db()
        
        item_id = int(data.get('item_id'))
        movement_type = data.get('movement_type')
        qty = float(data.get('qty'))
        
        # Validace
        if movement_type not in ['in', 'out', 'return', 'transfer', 'adjustment', 'inventory']:
            return jsonify({'success': False, 'error': 'Neplatný typ pohybu'}), 400
        
        # Vytvoř movement
        cursor = db.execute("""
            INSERT INTO warehouse_movements 
            (item_id, movement_type, qty, job_id, from_location, to_location, 
             employee_id, note, batch_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id,
            movement_type,
            qty,
            data.get('job_id'),
            data.get('from_location', ''),
            data.get('to_location', ''),
            data.get('employee_id'),
            data.get('note', ''),
            data.get('batch_number', '')
        ))
        
        # Aktualizuj množství v položce
        if movement_type in ['in', 'return', 'adjustment']:
            # Přičti
            db.execute("""
                UPDATE warehouse_items
                SET qty = qty + ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (qty, item_id))
        elif movement_type in ['out', 'transfer']:
            # Odečti
            db.execute("""
                UPDATE warehouse_items
                SET qty = qty - ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (qty, item_id))
        
        # Aktualizuj lokaci pokud je transfer
        if movement_type == 'transfer' and data.get('to_location'):
            db.execute("""
                UPDATE warehouse_items
                SET location = ?
                WHERE id = ?
            """, (data.get('to_location'), item_id))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'movement_id': cursor.lastrowid
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


def get_job_materials(job_id):
    """GET /api/warehouse/jobs/<job_id>/materials
    
    Vrátí všechen materiál použitý na zakázce
    """
    try:
        db = get_db()
        
        materials = db.execute("""
            SELECT 
                wi.id as item_id,
                wi.name,
                wi.unit,
                wi.price,
                SUM(CASE 
                    WHEN wm.movement_type = 'out' THEN wm.qty 
                    WHEN wm.movement_type = 'return' THEN -wm.qty 
                    ELSE 0 
                END) as total_qty,
                SUM(CASE 
                    WHEN wm.movement_type = 'out' THEN wm.qty * wi.price
                    WHEN wm.movement_type = 'return' THEN -wm.qty * wi.price
                    ELSE 0 
                END) as total_cost
            FROM warehouse_movements wm
            JOIN warehouse_items wi ON wm.item_id = wi.id
            WHERE wm.job_id = ?
            AND wm.movement_type IN ('out', 'return')
            GROUP BY wi.id
            HAVING total_qty > 0
            ORDER BY wi.name
        """, (job_id,)).fetchall()
        
        return jsonify({
            'success': True,
            'materials': [dict(m) for m in materials]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------ RESERVATIONS ------------

def get_reservations():
    """GET /api/warehouse/reservations?item_id=X&job_id=Y&status=active"""
    try:
        db = get_db()
        item_id = request.args.get('item_id')
        job_id = request.args.get('job_id')
        status = request.args.get('status', 'active')
        
        query = """
            SELECT wr.*,
                   wi.name as item_name,
                   wi.unit as item_unit,
                   j.title as job_title,
                   e.name as reserved_by_name
            FROM warehouse_reservations wr
            LEFT JOIN warehouse_items wi ON wr.item_id = wi.id
            LEFT JOIN jobs j ON wr.job_id = j.id
            LEFT JOIN employees e ON wr.reserved_by = e.id
            WHERE wr.status = ?
        """
        params = [status]
        
        if item_id:
            query += " AND wr.item_id = ?"
            params.append(int(item_id))
        
        if job_id:
            query += " AND wr.job_id = ?"
            params.append(int(job_id))
        
        query += " ORDER BY wr.reserved_from"
        
        reservations = db.execute(query, params).fetchall()
        
        return jsonify({
            'success': True,
            'reservations': [dict(r) for r in reservations]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def create_reservation():
    """POST /api/warehouse/reservations"""
    try:
        data = request.json
        db = get_db()
        
        item_id = int(data.get('item_id'))
        qty = float(data.get('qty'))
        
        # Zkontroluj dostupné množství
        item = db.execute("""
            SELECT qty,
                   COALESCE(
                       (SELECT SUM(qty) 
                        FROM warehouse_reservations 
                        WHERE item_id = ? 
                        AND status = 'active'
                        AND reserved_until >= date('now')),
                       0
                   ) as reserved_qty
            FROM warehouse_items
            WHERE id = ?
        """, (item_id, item_id)).fetchone()
        
        available = item['qty'] - item['reserved_qty']
        
        if qty > available:
            return jsonify({
                'success': False,
                'error': f'Nedostatečné množství. Dostupné: {available} {data.get("unit", "")}'
            }), 400
        
        # Vytvoř rezervaci
        cursor = db.execute("""
            INSERT INTO warehouse_reservations
            (item_id, job_id, qty, reserved_by, reserved_from, reserved_until, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id,
            data.get('job_id'),
            qty,
            data.get('reserved_by'),
            data.get('reserved_from'),
            data.get('reserved_until'),
            data.get('note', '')
        ))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'reservation_id': cursor.lastrowid
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def update_reservation(reservation_id):
    """PATCH /api/warehouse/reservations/<id>"""
    try:
        data = request.json
        db = get_db()
        
        # Povol pouze změnu statusu nebo dat
        db.execute("""
            UPDATE warehouse_reservations
            SET status = ?,
                reserved_from = COALESCE(?, reserved_from),
                reserved_until = COALESCE(?, reserved_until),
                note = COALESCE(?, note)
            WHERE id = ?
        """, (
            data.get('status', 'active'),
            data.get('reserved_from'),
            data.get('reserved_until'),
            data.get('note'),
            reservation_id
        ))
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------ INVENTORY ------------

def get_inventories():
    """GET /api/warehouse/inventory"""
    try:
        db = get_db()
        
        inventories = db.execute("""
            SELECT i.*,
                   e1.name as started_by_name,
                   e2.name as completed_by_name,
                   COUNT(ii.id) as items_count,
                   SUM(CASE WHEN ii.counted_qty IS NOT NULL THEN 1 ELSE 0 END) as counted_items
            FROM warehouse_inventory i
            LEFT JOIN employees e1 ON i.started_by = e1.id
            LEFT JOIN employees e2 ON i.completed_by = e2.id
            LEFT JOIN warehouse_inventory_items ii ON i.id = ii.inventory_id
            GROUP BY i.id
            ORDER BY i.started_at DESC
        """).fetchall()
        
        return jsonify({
            'success': True,
            'inventories': [dict(inv) for inv in inventories]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def start_inventory():
    """POST /api/warehouse/inventory/start"""
    try:
        data = request.json
        db = get_db()
        
        # Zkontroluj, zda není rozpracovaná inventura
        existing = db.execute("""
            SELECT id FROM warehouse_inventory
            WHERE status = 'in_progress'
        """).fetchone()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'Již existuje rozpracovaná inventura'
            }), 400
        
        # Vytvoř novou inventuru
        cursor = db.execute("""
            INSERT INTO warehouse_inventory
            (inventory_date, started_by, note)
            VALUES (date('now'), ?, ?)
        """, (
            data.get('started_by'),
            data.get('note', '')
        ))
        
        inventory_id = cursor.lastrowid
        
        # Vytvoř položky pro všechny aktivní warehouse items
        db.execute("""
            INSERT INTO warehouse_inventory_items
            (inventory_id, item_id, expected_qty, location)
            SELECT ?, id, qty, location
            FROM warehouse_items
            WHERE status = 'active'
        """, (inventory_id,))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'inventory_id': inventory_id
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


def get_inventory_items(inventory_id):
    """GET /api/warehouse/inventory/<id>/items"""
    try:
        db = get_db()
        
        items = db.execute("""
            SELECT ii.*,
                   wi.name as item_name,
                   wi.unit as item_unit,
                   wi.sku,
                   wi.category,
                   e.name as counted_by_name
            FROM warehouse_inventory_items ii
            JOIN warehouse_items wi ON ii.item_id = wi.id
            LEFT JOIN employees e ON ii.counted_by = e.id
            WHERE ii.inventory_id = ?
            ORDER BY wi.category, wi.name
        """, (inventory_id,)).fetchall()
        
        return jsonify({
            'success': True,
            'items': [dict(item) for item in items]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def update_inventory_item(inventory_item_id):
    """PATCH /api/warehouse/inventory/items/<id>
    
    Zaznamená napočítané množství
    """
    try:
        data = request.json
        db = get_db()
        
        counted_qty = float(data.get('counted_qty'))
        
        # Získej expected_qty
        item = db.execute("""
            SELECT expected_qty FROM warehouse_inventory_items
            WHERE id = ?
        """, (inventory_item_id,)).fetchone()
        
        difference = counted_qty - item['expected_qty']
        
        # Aktualizuj
        db.execute("""
            UPDATE warehouse_inventory_items
            SET counted_qty = ?,
                difference = ?,
                counted_by = ?,
                counted_at = datetime('now'),
                note = ?
            WHERE id = ?
        """, (
            counted_qty,
            difference,
            data.get('counted_by'),
            data.get('note', ''),
            inventory_item_id
        ))
        
        db.commit()
        
        return jsonify({'success': True, 'difference': difference})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def complete_inventory(inventory_id):
    """POST /api/warehouse/inventory/<id>/complete
    
    Ukončí inventuru a aplikuje rozdíly
    """
    try:
        data = request.json
        db = get_db()
        
        # Získej všechny položky s rozdíly
        items = db.execute("""
            SELECT item_id, difference, note
            FROM warehouse_inventory_items
            WHERE inventory_id = ?
            AND counted_qty IS NOT NULL
            AND difference != 0
        """, (inventory_id,)).fetchall()
        
        # Aplikuj každý rozdíl jako adjustment movement
        for item in items:
            # Vytvoř movement
            db.execute("""
                INSERT INTO warehouse_movements
                (item_id, movement_type, qty, note)
                VALUES (?, 'adjustment', ?, ?)
            """, (
                item['item_id'],
                item['difference'],
                f"Inventura {inventory_id}: {item['note'] or 'Korekce stavu'}"
            ))
            
            # Aktualizuj qty v items
            db.execute("""
                UPDATE warehouse_items
                SET qty = qty + ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (item['difference'], item['item_id']))
        
        # Označ inventuru jako dokončenou
        db.execute("""
            UPDATE warehouse_inventory
            SET status = 'completed',
                completed_by = ?,
                completed_at = datetime('now')
            WHERE id = ?
        """, (data.get('completed_by'), inventory_id))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'adjustments_count': len(items)
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------ MERGE ITEMS ------------

def merge_items():
    """POST /api/warehouse/items/merge
    
    Sloučí source_item_id do target_item_id
    """
    try:
        data = request.json
        db = get_db()
        
        source_id = int(data.get('source_item_id'))
        target_id = int(data.get('target_item_id'))
        
        if source_id == target_id:
            return jsonify({'success': False, 'error': 'Nelze sloučit položku samu do sebe'}), 400
        
        # Získej data obou položek
        source = db.execute("SELECT * FROM warehouse_items WHERE id = ?", (source_id,)).fetchone()
        target = db.execute("SELECT * FROM warehouse_items WHERE id = ?", (target_id,)).fetchone()
        
        if not source or not target:
            return jsonify({'success': False, 'error': 'Položka nenalezena'}), 404
        
        # Přesuň množství
        db.execute("""
            UPDATE warehouse_items
            SET qty = qty + ?
            WHERE id = ?
        """, (source['qty'], target_id))
        
        # Přesuň všechny movements
        db.execute("""
            UPDATE warehouse_movements
            SET item_id = ?
            WHERE item_id = ?
        """, (target_id, source_id))
        
        # Přesuň rezervace
        db.execute("""
            UPDATE warehouse_reservations
            SET item_id = ?
            WHERE item_id = ?
        """, (target_id, source_id))
        
        # Označ source jako merged
        db.execute("""
            UPDATE warehouse_items
            SET status = 'merged',
                merged_into = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (target_id, source_id))
        
        # Zaznamenej do historie
        db.execute("""
            INSERT INTO warehouse_merge_history
            (source_item_id, target_item_id, merged_by, note, source_data_json)
            VALUES (?, ?, ?, ?, ?)
        """, (
            source_id,
            target_id,
            data.get('merged_by'),
            data.get('note', ''),
            json.dumps(dict(source), ensure_ascii=False)
        ))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Položka sloučena. Celkové množství: {source["qty"] + target["qty"]} {target["unit"]}'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


def rename_item(item_id):
    """PATCH /api/warehouse/items/<id>/rename"""
    try:
        data = request.json
        db = get_db()
        
        new_name = data.get('name', '').strip()
        if not new_name:
            return jsonify({'success': False, 'error': 'Název nemůže být prázdný'}), 400
        
        db.execute("""
            UPDATE warehouse_items
            SET name = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (new_name, item_id))
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ------------ STATS ------------

def get_warehouse_stats():
    """GET /api/warehouse/stats"""
    try:
        db = get_db()
        
        # Celková hodnota
        total_value = db.execute("""
            SELECT COALESCE(SUM(qty * price), 0) as total
            FROM warehouse_items
            WHERE status = 'active'
        """).fetchone()['total']
        
        # Celkem položek
        total_items = db.execute("""
            SELECT COUNT(*) as cnt
            FROM warehouse_items
            WHERE status = 'active'
        """).fetchone()['cnt']
        
        # Nízký stav
        low_stock = db.execute("""
            SELECT COUNT(*) as cnt
            FROM warehouse_items
            WHERE status = 'active'
            AND qty > 0
            AND qty < minStock
        """).fetchone()['cnt']
        
        # Nedostupné
        out_of_stock = db.execute("""
            SELECT COUNT(*) as cnt
            FROM warehouse_items
            WHERE status = 'active'
            AND qty <= 0
        """).fetchone()['cnt']
        
        # Expirující položky (do 30 dnů)
        expiring_soon = db.execute("""
            SELECT COUNT(*) as cnt
            FROM warehouse_items
            WHERE status = 'active'
            AND expiration_date != ''
            AND date(expiration_date) <= date('now', '+30 days')
            AND date(expiration_date) > date('now')
        """).fetchone()['cnt']
        
        # Již expirované
        expired = db.execute("""
            SELECT COUNT(*) as cnt
            FROM warehouse_items
            WHERE status = 'active'
            AND expiration_date != ''
            AND date(expiration_date) <= date('now')
        """).fetchone()['cnt']
        
        # Rezervované množství
        reserved = db.execute("""
            SELECT COALESCE(SUM(qty), 0) as total
            FROM warehouse_reservations
            WHERE status = 'active'
            AND reserved_until >= date('now')
        """).fetchone()['total']
        
        return jsonify({
            'success': True,
            'stats': {
                'total_value': round(total_value, 2),
                'total_items': total_items,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock,
                'expiring_soon': expiring_soon,
                'expired': expired,
                'reserved': round(reserved, 2)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
