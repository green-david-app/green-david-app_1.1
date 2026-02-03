from flask import Blueprint, request, jsonify
import sys
import os
import importlib.util

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import service
_inventory_service_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'inventory_service.py')
spec = importlib.util.spec_from_file_location("inventory_service", _inventory_service_path)
inventory_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory_service_module)
InventoryService = inventory_service_module.InventoryService

inventory_bp = Blueprint('inventory_api', __name__, url_prefix='/api/inventory')


@inventory_bp.route('/overview', methods=['GET'])
def get_overview():
    """Prostorový přehled inventáře."""
    data = InventoryService.get_spatial_overview()
    return jsonify({'success': True, 'data': data})


@inventory_bp.route('/location/<int:location_id>', methods=['GET'])
def get_location_detail(location_id):
    """Detail lokace s rozpadem podle typů."""
    include_children = request.args.get('include_children', 'true').lower() == 'true'
    data = InventoryService.get_location_detail(location_id, include_children)
    if not data:
        return jsonify({'success': False, 'error': 'Location not found'}), 404
    return jsonify({'success': True, 'data': data})


@inventory_bp.route('/type/<int:type_id>', methods=['GET'])
def get_type_inventory(type_id):
    """Inventář typu napříč lokacemi."""
    data = InventoryService.get_type_inventory(type_id)
    if not data:
        return jsonify({'success': False, 'error': 'Type not found'}), 404
    return jsonify({'success': True, 'data': data})


@inventory_bp.route('/location/<int:location_id>/lots', methods=['GET'])
def get_lots(location_id):
    """Šarže na lokaci (drilldown)."""
    type_id = request.args.get('type_id', type=int)
    data = InventoryService.get_lots_at_location(location_id, type_id)
    return jsonify({'success': True, 'data': data})


@inventory_bp.route('/search', methods=['GET'])
def quick_search():
    """Rychlé vyhledávání."""
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify({'success': False, 'error': 'Query too short'}), 400
    data = InventoryService.quick_search(q)
    return jsonify({'success': True, 'data': data})


@inventory_bp.route('/alerts/low-stock', methods=['GET'])
def get_low_stock():
    """Položky s nízkým stavem."""
    threshold = request.args.get('threshold', 20, type=float)
    data = InventoryService.get_low_stock_alerts(threshold)
    return jsonify({'success': True, 'data': data})
