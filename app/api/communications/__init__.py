from flask import Blueprint

communications_bp = Blueprint('communications', __name__, url_prefix='/communications')

from . import routes
