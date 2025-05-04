from flask import Blueprint

api_bp = Blueprint('api', __name__)

# Importar Blueprints dos seus respectivos módulos __init__
from app.api.auth import auth_bp
from app.api.users import bp as users_bp
from app.api.leads import bp as leads_bp
from app.api.deals import bp as deals_bp
from app.api.customers import customers_bp
from app.api.custom_fields import custom_fields_bp
from app.api.pipeline import bp as pipeline_bp
from app.api.tasks import tasks_bp
from app.api.communications import communications_bp
from app.api.workflows import workflows_bp
from app.api.documents import documents_bp

# Registrar Blueprints no Blueprint principal da API com os respectivos url_prefix
api_bp.register_blueprint(auth_bp, url_prefix='/auth')
api_bp.register_blueprint(users_bp, url_prefix='/users')
api_bp.register_blueprint(leads_bp, url_prefix='/leads')
api_bp.register_blueprint(deals_bp, url_prefix='/deals')
api_bp.register_blueprint(customers_bp, url_prefix='/customers')
api_bp.register_blueprint(custom_fields_bp, url_prefix='/custom-fields')
api_bp.register_blueprint(pipeline_bp, url_prefix='/pipeline')
api_bp.register_blueprint(tasks_bp, url_prefix='/tasks')
api_bp.register_blueprint(communications_bp, url_prefix='/communications')
api_bp.register_blueprint(workflows_bp, url_prefix='/workflows')
api_bp.register_blueprint(documents_bp, url_prefix='/documents')

# Nota: Após esta modificação, todas as rotas terão seus prefixos corretamente configurados
# Exemplo: /api/users/me, /api/leads/, /api/auth/login, etc.