from flask import Flask
# from flask_cors import CORS
import os
from .extensions import api
from .config import Config
from dotenv import load_dotenv
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

def create_app(config_object: type[Config] | None = None):
    app = Flask(__name__)
    # CORS(app,
    #      resources={r"/*": {"origins": [
    #         "http://localhost:3000",
    #         "http://127.0.0.1:3000",
    #         "https://kalyanjyothula.fun"
    #      ]}}
    # )


    app.config.from_object(config_object or Config)

    # Initialize extensions
    api.init_app(app)
    load_dotenv()
    hf_token = os.getenv('HF_TOKEN')
    openai_key = os.getenv('OPEN_AI_API_KEY')
    os.environ['HF_TOKEN'] = hf_token  
    os.environ['OPENAI_API_KEY'] = openai_key  


    # Register blueprints (import here to avoid circulars)
    from text_api.text_api import bp
    api.register_blueprint(bp, url_prefix="/api")

    from gf_ai_chat.gf_ai_chat import bp as gf_chat_bp
    api.register_blueprint(gf_chat_bp, url_prefix="/gf")

    from story_api.story_api import bp as story_bp
    api.register_blueprint(story_bp, url_prefix="/story")

    from rag_on_doc.rag_on_doc import bp as doc_bp
    api.register_blueprint(doc_bp, url_prefix="/pdf")

    from excel_companion.excel_companion import bp as excel_bp
    api.register_blueprint(excel_bp, url_prefix="/excel")

    @app.get("/")
    def health():
        return {"status": "ok"}

    return app
