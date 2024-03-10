from flask import Flask
from resources.users import users_namespace
from resources.session import session_namespace
from resources.util import util_namespace
from resources.chats import chats_namespace
from resources.presets import presets_namespace
from resources.tasks import tasks_namespace
from extensions import db, api
from jwt_auth import jwt
import redis

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object("config.Config")

    # Initialize SQLAlchemy
    db.init_app(app)

    # Initialize JWT
    jwt.init_app(app)

    # Initialize Flask-RESTX
    api.init_app(app)

    # Initialize Redis
    redis_client = redis.Redis(host=app.config["REDIS_HOST"], port=app.config["REDIS_PORT"], db=app.config["REDIS_DB"], password=app.config["REDIS_PASSWORD"] if app.config["REDIS_PASSWORD"] else None, decode_responses=True)
    app.config["REDIS_CLIENT"] = redis_client

    # Add resources
    api.add_namespace(users_namespace)
    api.add_namespace(session_namespace)
    api.add_namespace(chats_namespace)
    api.add_namespace(presets_namespace)
    api.add_namespace(tasks_namespace)

    # Handle uncaught exceptions
    @app.errorhandler(Exception)
    def handle_exception(e):
        return {"message": str(e)}, 500
    
    # Debug-only routes
    if app.config["DEBUG"]:
        api.add_namespace(util_namespace)
        
    return app