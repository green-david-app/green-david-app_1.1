
from flask import Flask
import os

# SQLAlchemy a Migrate jsou volitelné - aplikace používá SQLite přímo
try:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
except ImportError:
    db = None

try:
    from flask_migrate import Migrate
    migrate = Migrate()
except ImportError:
    migrate = None

try:
    from flask_cors import CORS
except ImportError:
    CORS = None

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # SQLAlchemy config je volitelný
    if db is not None:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    app.config["JSON_AS_ASCII"] = False

    if CORS is not None:
        CORS(app, resources={r"/gd/*": {"origins": "*"}})

    if db is not None:
        db.init_app(app)
    
    if migrate is not None and db is not None:
        migrate.init_app(app, db)

    # Importy modelů jsou volitelné - aplikace používá SQLite přímo
    try:
        from .models import Event  # noqa: F401
        from .models.task import Task  # noqa: F401
        from .models.task_material import TaskMaterial  # noqa: F401
        from .models.task_evidence import TaskEvidence  # noqa: F401
        from .models.task_event import TaskEvent  # noqa: F401
        from .models.task_dependency import TaskDependency  # noqa: F401
        from .views import ui_bp
        from .api import api_bp

        app.register_blueprint(ui_bp)
        app.register_blueprint(api_bp, url_prefix="/gd/api")

        # Create DB tables on first run (SQLite)
        if db is not None:
            with app.app_context():
                db.create_all()
    except ImportError:
        # Pokud modely nejsou dostupné, aplikace může fungovat bez nich
        pass

    return app
