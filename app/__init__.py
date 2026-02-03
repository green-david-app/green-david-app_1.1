
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JSON_AS_ASCII"] = False

    CORS(app, resources={r"/gd/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)

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
    with app.app_context():
        db.create_all()

    return app
