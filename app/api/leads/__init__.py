from flask import Blueprint

bp = Blueprint('leads', __name__, url_prefix='/leads')

from app.api.leads import routes 