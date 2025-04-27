from flask import request, jsonify, current_app
from marshmallow import ValidationError

from app import db
from app.models import User
from . import auth_bp 
from .schemas import LoginSchema, UserSchema



login_schema = LoginSchema()
user_schema = UserSchema()

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Autentica um usuário e retorna token JWT.
    
    Request body:
        JSON com username e password
        
    Returns:
        200: Login bem-sucedido com token JWT
        400: Dados de login inválidos
        401: Credenciais inválidas
        500: Erro interno do servidor
    """
    try:
        # Validar dados de entrada usando schema
        data = login_schema.load(request.json or {})
    except ValidationError as err:
        current_app.logger.warning(f"Erro de validação no login: {err.messages}")
        return jsonify({
            'message': 'Erro de validação', 
            'errors': err.messages
        }), 400
    
    try:
        # Buscar usuário pelo nome de usuário
        user = User.query.filter_by(username=data['username']).first()
        
        # Verificar se o usuário existe e se a senha está correta
        if user and user.verify_password(data['password']):
            # Gerar token JWT
            token = user.generate_token()
            
            current_app.logger.info(f"Login bem-sucedido para o usuário {user.username}")
            return jsonify({
                'message': 'Login realizado com sucesso',
                'user': user.to_dict(),
                'access_token': token
            }), 200
        
        # Credenciais inválidas
        current_app.logger.warning(f"Tentativa de login mal-sucedida para o usuário {data['username']}")
        return jsonify({'message': 'Credenciais inválidas'}), 401
        
    except Exception as e:
        current_app.logger.error(f"Erro no login: {str(e)}")
        return jsonify({
            'message': 'Erro durante o login',
            'error': str(e)
        }), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Cria um novo usuário no sistema.
    
    Request body:
        JSON com dados do usuário conforme UserSchema
        
    Returns:
        201: Usuário criado com sucesso com token JWT
        400: Erro de validação ou usuário/email já existente
        500: Erro interno do servidor
    """
    try:
        # Validar dados de entrada usando schema
        data = user_schema.load(request.json or {})
    except ValidationError as err:
        current_app.logger.warning(f"Erro de validação no registro: {err.messages}")
        return jsonify({
            'message': 'Erro de validação', 
            'errors': err.messages
        }), 400
    
    try:
        # Verificar se o nome de usuário já existe
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Nome de usuário já existe'}), 400
            
        # Verificar se o e-mail já existe
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'E-mail já cadastrado'}), 400
        
        # Criar novo usuário
        user = User(
            name=data['name'],
            username=data['username'],
            email=data['email'],
            password=data['password'],  # A senha será hasheada pelo setter
            role=data.get('role', 'vendedor')  # Padrão: vendedor
        )
        
        # Persistir no banco de dados
        db.session.add(user)
        db.session.commit()
        
        # Gerar token JWT (opcional retornar no registro, mas mantido por consistência)
        token = user.generate_token()
        
        current_app.logger.info(f"Usuário {user.username} registrado com sucesso")
        return jsonify({
            'message': 'Usuário registrado com sucesso',
            'user': user.to_dict(),
            'access_token': token # Pode ser útil para logar automaticamente após registro
        }), 201
        
    except Exception as e:
        # Rollback em caso de erro
        db.session.rollback()
        current_app.logger.error(f"Erro no registro de usuário: {str(e)}")
        return jsonify({
            'message': 'Erro ao registrar usuário',
            'error': str(e)
        }), 500 