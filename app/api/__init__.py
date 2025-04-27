from flask import Blueprint
# from flask_cors import CORS # Remover import se não usado em outro lugar neste arquivo


api_bp = Blueprint('api', __name__)

# Remover configuração CORS específica deste blueprint
# CORS(api_bp, resources={r"/*": {
#     "origins": ["http://localhost:5173", "http://localhost:3000"], 
#     "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     "allow_headers": ["Content-Type", "Authorization"],
#     "supports_credentials": True 
# }})

# Importar Blueprints dos seus respectivos módulos __init__
from app.api.auth import auth_bp
from app.api.users import bp as users_bp
from app.api.leads import bp as leads_bp
from app.api.deals import bp as deals_bp
from app.api.customers import customers_bp
from app.api.custom_fields import custom_fields_bp
from app.api.pipeline import bp as pipeline_bp

# Novos módulos implementados
from app.api.tasks import tasks_bp
from app.api.communications import communications_bp
from app.api.workflows import workflows_bp
from app.api.documents import documents_bp

# Registrar Blueprints no Blueprint principal da API
# Note que os url_prefix definidos na criação dos Blueprints serão usados
api_bp.register_blueprint(auth_bp)
api_bp.register_blueprint(users_bp)
api_bp.register_blueprint(leads_bp)
api_bp.register_blueprint(deals_bp)
api_bp.register_blueprint(customers_bp)
api_bp.register_blueprint(custom_fields_bp)
api_bp.register_blueprint(pipeline_bp)

# Registrar novos blueprints
api_bp.register_blueprint(tasks_bp)
api_bp.register_blueprint(communications_bp)
api_bp.register_blueprint(workflows_bp)
api_bp.register_blueprint(documents_bp)