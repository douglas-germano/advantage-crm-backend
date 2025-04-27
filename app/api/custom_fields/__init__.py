from flask import Blueprint

custom_fields_bp = Blueprint('custom_fields', __name__, url_prefix='/custom-fields')

from . import routes
