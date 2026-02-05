# Green David App
from flask import Blueprint, jsonify, request, send_from_directory, render_template
from datetime import datetime
from app.database import get_db
from app.utils.permissions import require_auth, require_role

nursery_bp = Blueprint('nursery', __name__)


@nursery_bp.route("/nursery")
def nursery_page():
    return send_from_directory(".", "nursery.html")


@nursery_bp.route("/plant-database")
def plant_database_page():
    return send_from_directory(".", "plant-database.html")


# Nursery routes from main.py

# Nursery routes from main.py

# Nursery routes from main.py

# Additional routes from main.py
@nursery_bp.route('/api/nursery/overview')
def api_nursery_overview():
    return ext_api.get_nursery_overview()

@nursery_bp.route('/api/nursery/plants')
def api_nursery_plants():
    return ext_api.get_nursery_plants()

@nursery_bp.route('/api/nursery/plants', methods=['POST'])
def api_create_nursery_plant():
    return ext_api.create_nursery_plant()

@nursery_bp.route('/api/nursery/plants/<int:plant_id>', methods=['PUT'])
def api_update_nursery_plant(plant_id):
    return ext_api.update_nursery_plant()

@nursery_bp.route('/api/nursery/plants/<int:plant_id>/to-warehouse', methods=['POST'])
def api_move_plant_to_warehouse(plant_id):
    return ext_api.move_to_warehouse()

@nursery_bp.route('/api/nursery/warehouse-transfers', methods=['GET'])
def api_get_warehouse_transfers():
    return ext_api.get_warehouse_transfer_history()

@nursery_bp.route('/api/nursery/watering', methods=['POST'])
def api_log_watering():
    return ext_api.log_watering()

# Recurring tasks 🔄
@nursery_bp.route('/recurring-tasks')
def recurring_tasks_page():
    return send_from_directory('.', 'recurring-tasks.html')

@nursery_bp.route('/api/recurring/templates')
def api_recurring_templates():
    return ext_api.get_recurring_templates()

@nursery_bp.route('/api/nursery/plants', methods=['POST'])
def api_nursery_add_plant():
    """Přidání nové rostliny do školky"""
    u, err = require_auth()
    if err: return err
    
    if u["role"] not in ["owner", "manager", "employee"]:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        data = request.get_json()
        
        # Validace povinných polí
        if not data.get('species'):
            return jsonify({
                'success': False,
                'message': 'Chybí název rostliny (species)'
            }), 400
        
        if not data.get('quantity'):
            return jsonify({
                'success': False,
                'message': 'Chybí počet kusů (quantity)'
            }), 400
        
        db = get_db()
        
        # Vlož rostlinu do databáze
        cursor = db.execute('''
            INSERT INTO nursery_plants (
                species, variety, quantity, unit, stage, location,
                planted_date, ready_date, selling_price, purchase_price,
                notes, flower_color, flowering_time, height,
                light_requirements, leaf_color, hardiness_zone,
                site_type, plants_per_m2, botanical_notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('species'),
            data.get('variety'),
            data.get('quantity', 0),
            data.get('unit', 'ks'),
            data.get('stage', 'sazenice'),
            data.get('location'),
            data.get('planted_date'),
            data.get('ready_date'),
            data.get('selling_price'),
            data.get('purchase_price'),
            data.get('notes'),
            data.get('flower_color'),
            data.get('flowering_time'),
            data.get('height'),
            data.get('light_requirements'),
            data.get('leaf_color'),
            data.get('hardiness_zone'),
            data.get('site_type'),
            data.get('plants_per_m2'),
            data.get('botanical_notes'),
            'active'
        ))
        
        plant_id = cursor.lastrowid
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rostlina byla úspěšně přidána',
            'plant_id': plant_id
        })
        
    except Exception as e:
        print(f"[ERROR] api_nursery_add_plant: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Chyba při ukládání: {str(e)}'
        }), 500


@nursery_bp.route('/api/nursery/plants', methods=['GET'])
def api_nursery_list_plants():
    """Seznam všech rostlin ve školce"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        
        # Filtry z query parametrů
        stage = request.args.get('stage')
        status = request.args.get('status', 'active')
        location = request.args.get('location')
        
        query = 'SELECT * FROM nursery_plants WHERE status = ?'
        params = [status]
        
        if stage:
            query += ' AND stage = ?'
            params.append(stage)
        
        if location:
            query += ' AND location = ?'
            params.append(location)
        
        query += ' ORDER BY created_at DESC'
        
        plants = db.execute(query, params).fetchall()
        
        result = []
        for p in plants:
            result.append({
                'id': p['id'],
                'species': p['species'],
                'variety': p['variety'],
                'quantity': p['quantity'],
                'unit': p['unit'],
                'stage': p['stage'],
                'location': p['location'],
                'planted_date': p['planted_date'],
                'selling_price': p['selling_price'],
                'flower_color': p['flower_color'],
                'flowering_time': p['flowering_time'],
                'height': p['height'],
                'created_at': p['created_at']
            })
        
        return jsonify({
            'success': True,
            'plants': result,
            'count': len(result)
        })
        
    except Exception as e:
        print(f"[ERROR] api_nursery_list_plants: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500


@nursery_bp.route('/api/nursery/plants/<int:plant_id>', methods=['GET'])
def api_nursery_get_plant(plant_id):
    """Detail rostliny"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        plant = db.execute('SELECT * FROM nursery_plants WHERE id = ?', (plant_id,)).fetchone()
        
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Rostlina nenalezena'
            }), 404
        
        return jsonify({
            'success': True,
            'plant': dict(plant)
        })
        
    except Exception as e:
        print(f"[ERROR] api_nursery_get_plant: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500


@nursery_bp.route('/api/nursery/plants/<int:plant_id>', methods=['PUT'])
def api_nursery_update_plant(plant_id):
    """Aktualizace rostliny"""
    u, err = require_auth()
    if err: return err
    
    if u["role"] not in ["owner", "manager", "employee"]:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        data = request.get_json()
        db = get_db()
        
        # Zkontroluj, že rostlina existuje
        plant = db.execute('SELECT id FROM nursery_plants WHERE id = ?', (plant_id,)).fetchone()
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Rostlina nenalezena'
            }), 404
        
        # Aktualizuj rostlinu
        db.execute('''
            UPDATE nursery_plants SET
                species = ?, variety = ?, quantity = ?, stage = ?,
                location = ?, planted_date = ?, selling_price = ?,
                notes = ?, flower_color = ?, flowering_time = ?,
                height = ?, light_requirements = ?, leaf_color = ?,
                hardiness_zone = ?, site_type = ?, plants_per_m2 = ?,
                botanical_notes = ?
            WHERE id = ?
        ''', (
            data.get('species'),
            data.get('variety'),
            data.get('quantity'),
            data.get('stage'),
            data.get('location'),
            data.get('planted_date'),
            data.get('selling_price'),
            data.get('notes'),
            data.get('flower_color'),
            data.get('flowering_time'),
            data.get('height'),
            data.get('light_requirements'),
            data.get('leaf_color'),
            data.get('hardiness_zone'),
            data.get('site_type'),
            data.get('plants_per_m2'),
            data.get('botanical_notes'),
            plant_id
        ))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rostlina byla aktualizována'
        })
        
    except Exception as e:
        print(f"[ERROR] api_nursery_update_plant: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500


@nursery_bp.route('/api/nursery/plants/<int:plant_id>', methods=['DELETE'])
def api_nursery_delete_plant(plant_id):
    """Smazání rostliny (soft delete)"""
    u, err = require_auth()
    if err: return err
    
    if u["role"] not in ["owner", "manager"]:
        return jsonify({"error": "Forbidden"}), 403
    
    try:
        db = get_db()
        
        # Soft delete - změň status na 'deleted'
        result = db.execute(
            'UPDATE nursery_plants SET status = ? WHERE id = ?',
            ('deleted', plant_id)
        )
        
        if result.rowcount == 0:
            return jsonify({
                'success': False,
                'message': 'Rostlina nenalezena'
            }), 404
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rostlina byla smazána'
        })
        
    except Exception as e:
        print(f"[ERROR] api_nursery_delete_plant: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500


# ==================== WEATHER API ====================

# Additional routes from main.py
@nursery_bp.route('/api/contracts')
def api_contracts():
    return ext_api.get_maintenance_contracts()

# Seasonal planner 🌱
@nursery_bp.route('/api/seasonal-tasks')
@nursery_bp.route('/api/plant-catalog/<int:plant_id>', methods=['GET'])
def api_plant_catalog_detail(plant_id):
    """Detail rostliny z katalogu"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        plant = db.execute('''
            SELECT * FROM plant_catalog WHERE id = ?
        ''', (plant_id,)).fetchone()
        
        if not plant:
            return jsonify({
                'success': False,
                'message': 'Rostlina nenalezena'
            }), 404
        
        return jsonify({
            'success': True,
            'plant': dict(plant)
        })
        
    except Exception as e:
        print(f"[ERROR] plant_catalog_detail: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba při načítání: {str(e)}'
        }), 500


@nursery_bp.route('/api/plant-catalog/stats', methods=['GET'])
def api_plant_catalog_stats():
    """Statistiky katalogu"""
    u, err = require_auth()
    if err: return err
    
    try:
        db = get_db()
        
        stats = db.execute('''
            SELECT 
                COUNT(*) as total_plants,
                COUNT(DISTINCT latin_name) as species_count,
                COUNT(DISTINCT CASE WHEN variety IS NOT NULL THEN latin_name END) as varieties_count
            FROM plant_catalog
        ''').fetchone()
        
        return jsonify({
            'success': True,
            'stats': dict(stats)
        })
        
    except Exception as e:
        print(f"[ERROR] plant_catalog_stats: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500


@nursery_bp.route('/api/plant-catalog/by-name', methods=['GET'])
def api_plant_catalog_by_name():
    """Najdi rostlinu přesně podle názvu a odrůdy"""
    u, err = require_auth()
    if err: return err
    
    latin = request.args.get('latin', '').strip()
    variety = request.args.get('variety', '').strip() or None
    
    if not latin:
        return jsonify({
            'success': False,
            'message': 'Chybí latinský název'
        }), 400
    
    try:
        db = get_db()
        
        if variety:
            plant = db.execute('''
                SELECT * FROM plant_catalog 
                WHERE latin_name = ? AND variety = ?
                LIMIT 1
            ''', (latin, variety)).fetchone()
        else:
            plant = db.execute('''
                SELECT * FROM plant_catalog 
                WHERE latin_name = ? AND variety IS NULL
                LIMIT 1
            ''', (latin,)).fetchone()
        
        if plant:
            return jsonify({
                'success': True,
                'plant': dict(plant)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Rostlina v katalogu nenalezena'
            }), 404
            
    except Exception as e:
        print(f"[ERROR] plant_catalog_by_name: {e}")
        return jsonify({
            'success': False,
            'message': f'Chyba: {str(e)}'
        }), 500


# ========== NURSERY PLANTS API ==========

