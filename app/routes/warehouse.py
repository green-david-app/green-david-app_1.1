# Green David App
from flask import Blueprint, jsonify, request, send_from_directory, render_template
from datetime import datetime
from app.database import get_db
from app.config import WRITE_ROLES
from app.utils.permissions import require_auth, require_role, requires_role, normalize_role

try:
    import planning_extended_api as ext_api
    ext_api.get_db = get_db
except ImportError:
    ext_api = None

warehouse_bp = Blueprint('warehouse', __name__)


@warehouse_bp.route("/warehouse.html")
def warehouse_html():
    return send_from_directory(".", "warehouse.html")


@warehouse_bp.route("/warehouse")
def warehouse_page():
    return send_from_directory(".", "warehouse.html")


@warehouse_bp.route("/materials")
def materials_page():
    return send_from_directory(".", "warehouse.html")


# Warehouse routes from main.py
@warehouse_bp.route("/warehouse.html")
def page_warehouse():
    return send_from_directory(".", "warehouse.html")

@warehouse_bp.route("/finance.html")
def page_finance():
    return send_from_directory(".", "finance.html")

@warehouse_bp.route("/documents.html")
def page_documents():
    return send_from_directory(".", "documents.html")

@warehouse_bp.route("/api/warehouse/items", methods=["GET"])
def api_warehouse_items_list():
    u, err = require_auth()
    if err: return err
    try:
        db = get_db()
        low_stock_only = request.args.get('low_stock') in ('1', 'true', 'yes')
        
        if low_stock_only:
            # Return only items below minimum stock
            items = db.execute("""
                SELECT * FROM warehouse_items 
                WHERE status = 'active' AND qty <= minStock AND minStock > 0
                ORDER BY (qty * 1.0 / NULLIF(minStock, 0)) ASC, name
            """).fetchall()
        else:
            items = db.execute("""
                SELECT * FROM warehouse_items 
                WHERE status = 'active' 
                ORDER BY name
            """).fetchall()
        
        # Normalize field names for frontend
        result = []
        for i in items:
            item = dict(i)
            item['quantity'] = item.get('qty', 0)
            item['min_quantity'] = item.get('minStock', 0)
            result.append(item)
        
        return jsonify({"success": True, "ok": True, "items": result})
    except Exception as e:
        print(f"[ERROR] Warehouse items: {e}")
        return jsonify({"success": False, "ok": False, "error": str(e)}), 500

@warehouse_bp.route("/api/warehouse/items", methods=["POST"])
def api_warehouse_items_create():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    try:
        data = request.json
        db = get_db()
        cursor = db.execute("""
            INSERT INTO warehouse_items (name, sku, category, location, qty, unit, price, minStock, note, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """, (
            data.get('name'),
            data.get('sku', ''),
            data.get('category', ''),
            data.get('location', ''),
            data.get('qty', 0),
            data.get('unit', 'ks'),
            data.get('price', 0),
            data.get('minStock', 10),
            data.get('note', '')
        ))
        db.commit()
        return jsonify({"success": True, "id": cursor.lastrowid})
    except Exception as e:
        print(f"[ERROR] Create warehouse item: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@warehouse_bp.route("/api/warehouse/items/<int:item_id>", methods=["PUT"])
def api_warehouse_items_update(item_id):
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    try:
        data = request.json
        db = get_db()
        db.execute("""
            UPDATE warehouse_items 
            SET name=?, sku=?, category=?, location=?, qty=?, unit=?, price=?, minStock=?, note=?, updated_at=datetime('now')
            WHERE id=?
        """, (
            data.get('name'),
            data.get('sku', ''),
            data.get('category', ''),
            data.get('location', ''),
            data.get('qty', 0),
            data.get('unit', 'ks'),
            data.get('price', 0),
            data.get('minStock', 10),
            data.get('note', ''),
            item_id
        ))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] Update warehouse item: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@warehouse_bp.route("/api/warehouse/items/<int:item_id>", methods=["DELETE"])
def api_warehouse_items_delete(item_id):
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    try:
        db = get_db()
        db.execute("UPDATE warehouse_items SET status='deleted' WHERE id=?", (item_id,))
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------- WAREHOUSE LOCATIONS --------
@warehouse_bp.route("/api/warehouse/locations", methods=["GET"])
def api_warehouse_locations():
    u, err = require_auth()
    if err: return err
    return warehouse_extended.get_locations()

@warehouse_bp.route("/api/warehouse/locations", methods=["POST"])
def api_warehouse_locations_create():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.create_location()

@warehouse_bp.route("/api/warehouse/locations/<int:location_id>", methods=["PATCH"])
def api_warehouse_locations_update(location_id):
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.update_location(location_id)

@warehouse_bp.route("/api/warehouse/locations/<int:location_id>", methods=["DELETE"])
def api_warehouse_locations_delete(location_id):
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.delete_location(location_id)

# -------- WAREHOUSE MOVEMENTS --------
@warehouse_bp.route("/api/warehouse/movements", methods=["GET"])
def api_warehouse_movements():
    u, err = require_auth()
    if err: return err
    return warehouse_extended.get_movements()

@warehouse_bp.route("/api/warehouse/movements", methods=["POST"])
def api_warehouse_movements_create():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.create_movement()

@warehouse_bp.route("/api/warehouse/jobs/<int:job_id>/materials", methods=["GET"])
def api_warehouse_job_materials(job_id):
    u, err = require_auth()
    if err: return err
    return warehouse_extended.get_job_materials(job_id)

# -------- WAREHOUSE RESERVATIONS --------
@warehouse_bp.route("/api/warehouse/reservations", methods=["GET"])
def api_warehouse_reservations():
    u, err = require_auth()
    if err: return err
    return warehouse_extended.get_reservations()

@warehouse_bp.route("/api/warehouse/reservations", methods=["POST"])
def api_warehouse_reservations_create():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.create_reservation()

@warehouse_bp.route("/api/warehouse/reservations/<int:reservation_id>", methods=["PATCH"])
def api_warehouse_reservations_update(reservation_id):
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.update_reservation(reservation_id)

# -------- WAREHOUSE INVENTORY --------
@warehouse_bp.route("/api/warehouse/inventory", methods=["GET"])
def api_warehouse_inventory():
    u, err = require_auth()
    if err: return err
    return warehouse_extended.get_inventories()

@warehouse_bp.route("/api/warehouse/inventory/start", methods=["POST"])
def api_warehouse_inventory_start():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.start_inventory()

@warehouse_bp.route("/api/warehouse/inventory/<int:inventory_id>/items", methods=["GET"])
def api_warehouse_inventory_items(inventory_id):
    u, err = require_auth()
    if err: return err
    return warehouse_extended.get_inventory_items(inventory_id)

@warehouse_bp.route("/api/warehouse/inventory/items/<int:inventory_item_id>", methods=["PATCH"])
def api_warehouse_inventory_items_update(inventory_item_id):
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.update_inventory_item(inventory_item_id)

@warehouse_bp.route("/api/warehouse/inventory/<int:inventory_id>/complete", methods=["POST"])
def api_warehouse_inventory_complete(inventory_id):
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.complete_inventory(inventory_id)

# -------- WAREHOUSE MERGE & RENAME --------
@warehouse_bp.route("/api/warehouse/items/merge", methods=["POST"])
def api_warehouse_items_merge():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.merge_items()

@warehouse_bp.route("/api/warehouse/items/<int:item_id>/rename", methods=["PATCH"])
def api_warehouse_items_rename(item_id):
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    return warehouse_extended.rename_item(item_id)

# -------- WAREHOUSE STATS --------
@warehouse_bp.route("/api/warehouse/stats", methods=["GET"])
def api_warehouse_stats():
    u, err = require_auth()
    if err: return err
    return warehouse_extended.get_warehouse_stats()


# -------- WAREHOUSE ITEMS CRUD --------
@warehouse_bp.route("/api/items", methods=["GET"])
def api_warehouse_get_items():
    u, err = require_auth()
    if err: return err
    try:
        db = get_db()
        site = request.args.get('site', '')
        
        if site == 'warehouse':
            try:
                items = db.execute("SELECT * FROM warehouse_items WHERE status = 'active' ORDER BY name").fetchall()
                return jsonify({"success": True, "items": [dict(i) for i in items]})
            except Exception as e:
                print(f"[ERROR] Loading warehouse_items: {e}")
                return jsonify({"success": True, "items": []})
        else:
            return jsonify({"success": True, "items": []})
    except Exception as e:
        print(f"[ERROR] api_get_items: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@warehouse_bp.route("/api/warehouse/search", methods=["GET"])
def api_warehouse_search():
    """Vyhledání položek ve skladu pro autocomplete"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({"items": []})
        
        # Vyhledej položky podle názvu
        sql = """
            SELECT 
                id, name, sku, category, qty, unit, price, location,
                reserved_qty,
                (qty - COALESCE(reserved_qty, 0)) as available_qty
            FROM warehouse_items 
            WHERE status = 'active' 
            AND (name LIKE ? OR sku LIKE ? OR category LIKE ?)
            ORDER BY name
            LIMIT 20
        """
        
        pattern = f"%{query}%"
        items = db.execute(sql, (pattern, pattern, pattern)).fetchall()
        
        result = []
        for item in items:
            result.append({
                "id": item["id"],
                "name": item["name"],
                "sku": item["sku"],
                "category": item["category"],
                "qty": item["qty"],
                "unit": item["unit"],
                "price": item["price"],
                "location": item["location"],
                "reserved_qty": item["reserved_qty"] or 0,
                "available_qty": item["available_qty"] or item["qty"]
            })
        
        return jsonify({"items": result})
    except Exception as e:
        print(f"[ERROR] warehouse_search: {e}")
        return jsonify({"error": str(e)}), 500
@warehouse_bp.route("/api/warehouse/items/<int:item_id>/reservations", methods=["GET"])
def api_warehouse_item_reservations(item_id):
    """Zobrazení všech rezervací pro položku skladu"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        
        reservations = db.execute("""
            SELECT 
                jm.id, jm.job_id, jm.qty, jm.reserved_qty,
                j.title as job_title, j.code as job_code, j.status as job_status
            FROM job_materials jm
            JOIN jobs j ON jm.job_id = j.id
            WHERE jm.warehouse_item_id = ?
            ORDER BY j.date DESC
        """, (item_id,)).fetchall()
        
        result = []
        for r in reservations:
            result.append({
                "id": r["id"],
                "job_id": r["job_id"],
                "job_title": r["job_title"],
                "job_code": r["job_code"],
                "job_status": r["job_status"],
                "qty": r["qty"],
                "reserved_qty": r["reserved_qty"]
            })
        
        return jsonify({"reservations": result})
    except Exception as e:
        print(f"[ERROR] get_reservations: {e}")
        return jsonify({"error": str(e)}), 500



# ========== PLANT CATALOG API ==========


# Additional routes from main.py
@warehouse_bp.route("/gd/api/warehouse/items", methods=["GET"])
def gd_api_warehouse_items():
    """Get warehouse items for autocomplete"""
    u, err = require_role(write=False)
    if err:
        return err
    db = get_db()
    
    try:
        search = request.args.get("search", "").strip()
        limit = request.args.get("limit", type=int) or 50
        
        q = "SELECT id, name, sku, category, quantity, unit, unit_price, location FROM warehouse_items WHERE quantity > 0"
        params = []
        
        if search:
            q += " AND (name LIKE ? OR sku LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        q += " ORDER BY name ASC LIMIT ?"
        params.append(limit)
        
        rows = db.execute(q, params).fetchall()
        items = []
        for row in rows:
            items.append({
                "id": row["id"],
                "name": row["name"],
                "sku": row.get("sku"),
                "category": row.get("category"),
                "quantity": float(row["quantity"] or 0),
                "unit": row.get("unit", "ks"),
                "unit_price": float(row.get("unit_price") or 0),
                "location": row.get("location")
            })
        
        return jsonify({"ok": True, "items": items})
    except Exception as e:
        print(f"✗ Error getting warehouse items: {e}")
        return jsonify({"ok": False, "error": "server_error", "message": str(e)}), 500

# ----------------- Training Service Functions -----------------
@warehouse_bp.route('/api/nursery/warehouse-transfers', methods=['GET'])
def api_get_warehouse_transfers():
    return ext_api.get_warehouse_transfer_history()

@warehouse_bp.route('/api/nursery/watering', methods=['POST'])
def api_log_watering():
    return ext_api.log_watering()

# Recurring tasks 🔄
@warehouse_bp.route('/recurring-tasks')
def recurring_tasks_page():
    return send_from_directory('.', 'recurring-tasks.html')

@warehouse_bp.route('/api/materials', methods=['POST'])
def api_create_material():
    return ext_api.create_material()

@warehouse_bp.route('/api/materials/<int:material_id>', methods=['PUT'])
def api_update_material(material_id):
    request.view_args = {'material_id': material_id}
    return ext_api.update_material()

@warehouse_bp.route('/api/materials/movement', methods=['POST'])
def api_material_movement():
    return ext_api.add_material_movement()

@warehouse_bp.route('/api/materials/movements')
def api_material_movements():
    return ext_api.get_material_movements()

# Photos 📸
@warehouse_bp.route('/api/tasks/<int:task_id>/photos', methods=['POST'])
def api_upload_task_photo(task_id):
    request.view_args = {'task_id': task_id}
    return ext_api.upload_task_photo()

# Additional routes from main.py
@warehouse_bp.route("/api/items", methods=["POST"])
def api_warehouse_create_item():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        data = request.json
        db = get_db()
        
        cursor = db.execute(
            "INSERT INTO warehouse_items (name, sku, category, location, qty, unit, price, minStock, batch_number, expiration_date, image, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data.get('name', ''), data.get('sku', ''), data.get('category', ''), data.get('location', ''),
             float(data.get('qty', 0)), data.get('unit', 'ks'), float(data.get('price', 0)),
             float(data.get('minStock', 10)), data.get('batch_number', ''), data.get('expiration_date', ''),
             data.get('image', ''), data.get('note', ''))
        )
        
        db.commit()
        print(f"[SUCCESS] Created warehouse item: {data.get('name')} (ID: {cursor.lastrowid})")
        return jsonify({"success": True, "item_id": cursor.lastrowid})
    except Exception as e:
        print(f"[ERROR] api_create_item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@warehouse_bp.route("/api/items", methods=["PATCH"])
def api_warehouse_update_item():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        data = request.json
        db = get_db()
        item_id = data.get('id')
        
        db.execute(
            "UPDATE warehouse_items SET name = ?, sku = ?, category = ?, location = ?, qty = ?, unit = ?, price = ?, minStock = ?, batch_number = ?, expiration_date = ?, image = ?, note = ?, updated_at = datetime('now') WHERE id = ?",
            (data.get('name', ''), data.get('sku', ''), data.get('category', ''), data.get('location', ''),
             float(data.get('qty', 0)), data.get('unit', 'ks'), float(data.get('price', 0)),
             float(data.get('minStock', 10)), data.get('batch_number', ''), data.get('expiration_date', ''),
             data.get('image', ''), data.get('note', ''), item_id)
        )
        
        db.commit()
        print(f"[SUCCESS] Updated warehouse item ID: {item_id}")
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] api_update_item: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


print("✅ Warehouse Extended Routes loaded")

# ----------------- Main Entry Point -----------------
# -------- WAREHOUSE ITEMS CRUD --------
@warehouse_bp.route("/api/items", methods=["GET"])
def api_get_items():
    u, err = require_auth()
    if err: return err
    try:
        db = get_db()
        site = request.args.get('site', '')
        
        if site == 'warehouse':
            try:
                items = db.execute("SELECT * FROM warehouse_items WHERE status = 'active' ORDER BY name").fetchall()
                return jsonify({"success": True, "items": [dict(i) for i in items]})
            except Exception:
                return jsonify({"success": True, "items": []})
        else:
            return jsonify({"success": True, "items": []})
    except Exception as e:
        print(f"[ERROR] api_get_items: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@warehouse_bp.route("/api/items", methods=["POST"])
def api_create_item():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        data = request.json
        db = get_db()
        
        cursor = db.execute(
            "INSERT INTO warehouse_items (name, sku, category, location, qty, unit, price, minStock, batch_number, expiration_date, image, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (data.get('name', ''), data.get('sku', ''), data.get('category', ''), data.get('location', ''),
             float(data.get('qty', 0)), data.get('unit', 'ks'), float(data.get('price', 0)),
             float(data.get('minStock', 10)), data.get('batch_number', ''), data.get('expiration_date', ''),
             data.get('image', ''), data.get('note', ''))
        )
        
        db.commit()
        return jsonify({"success": True, "item_id": cursor.lastrowid})
    except Exception as e:
        print(f"[ERROR] api_create_item: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@warehouse_bp.route("/api/items", methods=["PATCH"])
def api_update_item():
    u, err = require_auth()
    if err: return err
    if normalize_role(u.get("role")) not in WRITE_ROLES:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        data = request.json
        db = get_db()
        item_id = data.get('id')
        
        db.execute(
            "UPDATE warehouse_items SET name = ?, sku = ?, category = ?, location = ?, qty = ?, unit = ?, price = ?, minStock = ?, batch_number = ?, expiration_date = ?, image = ?, note = ?, updated_at = datetime('now') WHERE id = ?",
            (data.get('name', ''), data.get('sku', ''), data.get('category', ''), data.get('location', ''),
             float(data.get('qty', 0)), data.get('unit', 'ks'), float(data.get('price', 0)),
             float(data.get('minStock', 10)), data.get('batch_number', ''), data.get('expiration_date', ''),
             data.get('image', ''), data.get('note', ''), item_id)
        )
        
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"[ERROR] api_update_item: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

print("✅ Warehouse Items API loaded")

# PŘIDEJ DO main.py před 
# ========================================
# ============ WAREHOUSE <-> JOBS INTEGRATION ============

