from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from celery import Celery

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
celery = None  # ✅ Fix: Prevent circular import issue

def make_celery(app):
    """Initialize Celery with Flask app context."""
    celery_instance = Celery(
        app.import_name,
        backend=app.config["CELERY_RESULT_BACKEND"],
        broker=app.config["CELERY_BROKER_URL"]
    )
    celery_instance.conf.update(app.config)

    class ContextTask(celery_instance.Task):
        """Ensure Celery tasks run within Flask app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_instance.Task = ContextTask
    return celery_instance

def create_app():
    """Flask App Factory Pattern."""
    app = Flask(__name__)

    # ✅ Flask Config
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///rewards.db"
    app.config["SECRET_KEY"] = "mysecret"

    # ✅ Celery Config
    app.config["CELERY_BROKER_URL"] = "redis://localhost:6379/0"
    app.config["CELERY_RESULT_BACKEND"] = "redis://localhost:6379/0"

    # ✅ Initialize Flask Extensions
    db.init_app(app)
    login_manager.init_app(app)

    # ✅ Initialize Celery globally (Fix circular import)
    global celery
    celery = make_celery(app)

    # ✅ Enable CORS (optional for API access)
    CORS(app)

    # ✅ Register Blueprints
    from .routes import main
    app.register_blueprint(main)

    return app
