from flask import Blueprint

bp = Blueprint('deals', __name__)

from app.api.deals import routes