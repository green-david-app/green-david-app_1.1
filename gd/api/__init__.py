from flask import Blueprint

api_bp = Blueprint('gd_api', __name__, url_prefix='/gd/api')

# Note: employees endpoints are registered in employees.py by importing register_api below.
def register_api(app):
    from .employees import register_api as _reg
    _reg(app, api_bp)
    app.register_blueprint(api_bp)
