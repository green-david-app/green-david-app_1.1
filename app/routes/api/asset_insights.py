from flask import Blueprint, jsonify, request
import sys
import os
import importlib.util

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

# Import service
_insights_service_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'asset_insights_service.py')
spec = importlib.util.spec_from_file_location("asset_insights_service", _insights_service_path)
insights_service_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(insights_service_module)
AssetInsightsService = insights_service_module.AssetInsightsService
InsightType = insights_service_module.InsightType

insights_bp = Blueprint('asset_insights_api', __name__, url_prefix='/api/assets/insights')


@insights_bp.route('', methods=['GET'])
def get_all_insights():
    """Vrací všechny aktuální insights."""
    insights = AssetInsightsService.generate_all_insights()
    
    return jsonify({
        'success': True,
        'data': {
            'insights': insights,
            'summary': {
                'total': len(insights),
                'critical': len([i for i in insights if i['severity'] == 'critical']),
                'high': len([i for i in insights if i['severity'] == 'high']),
                'medium': len([i for i in insights if i['severity'] == 'medium']),
                'low': len([i for i in insights if i['severity'] == 'low'])
            }
        }
    })


@insights_bp.route('/type/<insight_type>', methods=['GET'])
def get_insights_by_type(insight_type):
    """Vrací insights konkrétního typu."""
    all_insights = AssetInsightsService.generate_all_insights()
    filtered = [i for i in all_insights if i['type'] == insight_type]
    
    return jsonify({
        'success': True,
        'data': filtered
    })
