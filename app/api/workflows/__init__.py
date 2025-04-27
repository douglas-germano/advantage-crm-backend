from flask import Blueprint

workflows_bp = Blueprint('workflows', __name__, url_prefix='/workflows')

from . import routes
