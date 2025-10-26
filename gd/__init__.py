
from flask import Flask
from .db import init_db, db_session
from .api import api_bp
from .views import views_bp

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_AS_ASCII'] = False
    app.config['SECRET_KEY'] = 'change-me'

    with app.app_context():
        init_db()

    app.register_blueprint(api_bp, url_prefix='/gd/api')
    app.register_blueprint(views_bp)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    return app
