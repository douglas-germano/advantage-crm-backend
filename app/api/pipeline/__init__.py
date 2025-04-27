from flask import Blueprint

bp = Blueprint('pipeline', __name__)

from app.api.pipeline import routes 