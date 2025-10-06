from flask import Flask
from .extensions import api
from .config import Config

def create_app(config_object: type[Config] | None = None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    # Initialize extensions
    api.init_app(app)

    # Register blueprints (import here to avoid circulars)
    from text_api.text_api import bp
    api.register_blueprint(bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
