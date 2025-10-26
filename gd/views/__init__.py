
from flask import Blueprint, redirect, url_for, jsonify
from .calendar import bp as cal_bp
from .timesheets import bp as ts_bp

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    return redirect(url_for('calendar.calendar_page'))

@views_bp.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

views_bp.register_blueprint(cal_bp)
views_bp.register_blueprint(ts_bp)
