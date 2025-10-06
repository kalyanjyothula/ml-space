from flask_smorest import Blueprint

bp = Blueprint("text-api", __name__,)

@bp.route('/')
def index():
    return {
        "Test": "Ok"
    }
