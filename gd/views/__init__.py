
from flask import Blueprint
from .calendar import bp as cal_bp
from .timesheets import bp as ts_bp

views_bp = Blueprint('views', __name__)
views_bp.register_blueprint(cal_bp)
views_bp.register_blueprint(ts_bp)
