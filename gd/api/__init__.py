from flask import Blueprint
api_bp = Blueprint('gd_api', __name__, url_prefix='/gd/api')

def register_api(app):
    from .employees import register_api as _reg
    _reg(app, api_bp)
    app.register_blueprint(api_bp)