"""
Módulo de inicialização da aplicação Flask para o sistema CRM.

Este módulo configura todas as extensões necessárias, gerencia o ciclo
de vida da aplicação e registra blueprints e handlers de erro.
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restful import Api
import click
import os

# Inicializar extensões globais
db = SQLAlchemy()  # ORM para banco de dados
migrate = Migrate()  # Gerenciamento de migrações do banco de dados
jwt = JWTManager()  # Gerenciamento de autenticação JWT


def create_app(config=None):
    """
    Factory function que cria e configura a aplicação Flask.
    
    Args:
        config: Objeto de configuração opcional. Se não fornecido, usa get_config()
    
    Returns:
        Flask app: Aplicação Flask configurada e pronta para uso
    """
    app = Flask(__name__)
    
    # Carregar configurações
    _configure_app(app, config)
    
    # Inicializar extensões com a aplicação
    _initialize_extensions(app)
    
    # Configurar handlers de erro JWT
    _configure_jwt_handlers(app)
    
    # Configurar CORS para acesso de origens permitidas
    _configure_cors(app)
    
    # Configurar endpoint de health check
    _register_health_check(app)
    
    # Registrar blueprints dos módulos da API
    _register_blueprints(app)
    
    # Configurar handlers globais de erro
    _register_error_handlers(app)
    
    # Registrar comandos CLI
    _register_commands(app)
    
    return app


def _configure_app(app, config):
    """
    Configura a aplicação com as configurações apropriadas.
    
    Args:
        app: Instância da aplicação Flask
        config: Objeto de configuração ou None
    """
    if config:
        app.config.from_object(config)
    else:
        from config import get_config
        app.config.from_object(get_config())
    
    # Configurações específicas do JWT
    app.config['JWT_IDENTITY_CLAIM'] = 'sub'
    app.config['JWT_ERROR_MESSAGE_KEY'] = 'error'
    app.config['JWT_TOKEN_LOCATION'] = ['headers', 'query_string']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Garantir que o diretório de uploads exista
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        os.makedirs(os.path.join(upload_folder, 'documents'), exist_ok=True)
        os.makedirs(os.path.join(upload_folder, 'communications'), exist_ok=True)


def _initialize_extensions(app):
    """
    Inicializa todas as extensões Flask com a aplicação.
    
    Args:
        app: Instância da aplicação Flask
    """
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)


def _configure_cors(app):
    origins = [
        "http://localhost:8080",
        "http://localhost:8081", 
        "http://192.168.15.4:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081"
    ]
    
    # Configuração simplificada de CORS para evitar headers duplicados
    CORS(app, 
         resources={r"/api/*": {"origins": origins}},
         supports_credentials=True,
         expose_headers=["Content-Type", "Authorization"],
         allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin", 
                       "Access-Control-Allow-Credentials"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )


def _configure_jwt_handlers(app):
    """
    Configura handlers personalizados para erros de autenticação JWT.
    
    Args:
        app: Instância da aplicação Flask
    """
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handler para tokens expirados"""
        return jsonify({
            'error': 'Token expirado',
            'description': 'O token fornecido expirou'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handler para tokens inválidos"""
        return jsonify({
            'error': 'Token inválido',
            'description': 'O token fornecido é inválido',
            'error_details': str(error)
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handler para ausência de token"""
        return jsonify({
            'error': 'Token ausente',
            'description': 'Token de autorização não fornecido',
            'error_details': str(error)
        }), 401


def _register_health_check(app):
    """
    Registra um endpoint simples para verificação de saúde da API.
    
    Args:
        app: Instância da aplicação Flask
    """
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Endpoint para verificar se a API está funcionando"""
        return {"status": "ok", "version": "1.0.0"}, 200


def _register_blueprints(app):
    """
    Registra todos os blueprints da aplicação.
    
    Args:
        app: Instância da aplicação Flask
    """
    with app.app_context():
        # Importar modelos para garantir que o Flask-Migrate os detecte
        from app.models import User, Customer, CustomField, CustomFieldValue, Lead
        from app.models.pipeline import PipelineStage
        from app.models.deal import Deal
        
        # Novos modelos implementados
        from app.models import Task, Communication, Workflow, WorkflowAction, Document
        
        # API principal
        from app.api import api_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        
        # Blueprints específicos (removendo example_bp)
        # from app.api.example import example_bp 
        # app.register_blueprint(example_bp, url_prefix='/api') 
        
        # Os blueprints de módulos já estão registrados dentro de api_bp
        # Não é necessário registrá-los novamente aqui diretamente no app
        # A linha app.register_blueprint(api_bp, url_prefix='/api') acima
        # já registra todos os blueprints aninhados (auth, users, leads, etc.)
        # sob o prefixo /api.
        
        # Remover registros individuais que estavam aqui, pois agora estão no api_bp
        # from app.api.leads import bp as leads_bp
        # app.register_blueprint(leads_bp, url_prefix='/api/leads')
        # 
        # from app.api.users import bp as users_bp
        # app.register_blueprint(users_bp, url_prefix='/api/users')
        # 
        # from app.api.deals import bp as deals_bp
        # app.register_blueprint(deals_bp, url_prefix='/api/deals')
        
        # Criar estágios padrão do pipeline para novos sistemas
        # Esta chamada pode ser movida para o comando init-db se fizer mais sentido
        # PipelineStage.create_default_stages() # Comentado para evitar erro antes da migração


def _register_error_handlers(app):
    """
    Registra handlers para erros HTTP comuns.
    
    Args:
        app: Instância da aplicação Flask
    """
    @app.errorhandler(404)
    def not_found(error):
        """Handler para recursos não encontrados"""
        return {"error": "Not found", "path": request.path}, 404
    
    @app.errorhandler(500)
    def server_error(error):
        """Handler para erros internos do servidor"""
        app.logger.error(f"Erro interno do servidor: {str(error)}")
        return {"error": "Server error", "details": str(error)}, 500
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handler para dados inválidos"""
        return {"error": "Unprocessable Entity", "details": str(error)}, 422


def _register_commands(app):
    """Registra comandos CLI na aplicação."""
    
    @app.cli.command('init-db')
    def init_db_command():
        """Inicializa o banco de dados: cria tabelas e admin padrão."""
        click.echo('Inicializando o banco de dados...')
        try:
            db.create_all()
            click.echo('Tabelas criadas com sucesso.')
        except Exception as e:
            click.echo(f'Erro ao criar tabelas: {str(e)}')
            return # Aborta se a criação de tabelas falhar
            
        _create_default_admin_cli()
        # Adicionar aqui outros comandos de inicialização, se necessário
        # Ex: Criar estágios de pipeline padrão se movidos para comando
        # from app.models.pipeline import PipelineStage
        # PipelineStage.create_default_stages()
        click.echo('Banco de dados inicializado.')
    
    # Mover a função helper para dentro ou mantê-la acessível aqui
    # Não precisa ser registrada como comando CLI diretamente
    def _create_default_admin_cli():
        """Helper para criar usuário admin padrão via CLI."""
        from app.models import User # Import local dentro da função
        
        try:
            if not User.query.filter_by(role='admin').first():
                click.echo('Criando usuário admin padrão...')
                default_password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
                if default_password == 'admin123':
                    click.echo(click.style('AVISO: Usando senha padrão fraca para admin. Defina DEFAULT_ADMIN_PASSWORD no ambiente para produção.', fg='yellow'))
                    
                admin = User(
                    name='Administrador',
                    username='admin',
                    email=os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@example.com'),
                    password=default_password,
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                click.echo(click.style('Usuário admin criado com sucesso.', fg='green'))
            else:
                click.echo('Usuário admin já existe.')
        except Exception as e:
            db.session.rollback()
            click.echo(click.style(f'Erro ao criar usuário admin: {str(e)}', fg='red'))

    # Você pode adicionar mais comandos @app.cli.command aqui dentro
    # Exemplo:
    # @app.cli.command('outro-comando')
    # def outro_comando_func():
    #     click.echo('Executando outro comando...')
