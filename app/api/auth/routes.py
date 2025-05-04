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
    # Endpoint para autenticar um usuário e retornar um token JWT.
    # 
    # Request body:
    #     JSON com "username" e "password".
    # 
    # Returns:
    #     200: Login bem-sucedido, retorna dados do usuário e 'access_token'.
    #     400: Erro se os dados enviados são inválidos (falta campos, formato incorreto).
    #     401: Erro se o usuário não existe ou a senha está incorreta.
    #     500: Erro interno do servidor.
    try:
        # Valida os dados recebidos no corpo da requisição JSON usando o LoginSchema.
        data = login_schema.load(request.json or {})
    except ValidationError as err:
        # Se a validação falhar, retorna erro 400 com os detalhes da validação.
        current_app.logger.warning(f"Erro de validação no login para dados: {request.json}. Erros: {err.messages}")
        return jsonify({
            'message': 'Erro de validação nos dados de login', 
            'errors': err.messages
        }), 400
    
    try:
        # Busca o usuário no banco de dados pelo username fornecido.
        user = User.query.filter_by(username=data['username']).first()
        
        # Verifica se o usuário foi encontrado e se a senha fornecida é válida.
        if user and user.verify_password(data['password']):
            # Se as credenciais são válidas, gera um token JWT para o usuário.
            token = user.generate_token()
            
            current_app.logger.info(f"Login bem-sucedido para o usuário {user.username} (ID: {user.id})")
            # Retorna sucesso (200) com mensagem, dados do usuário e o token.
            return jsonify({
                'message': 'Login realizado com sucesso',
                'user': user.to_dict(), # Converte o objeto User para dicionário
                'access_token': token
            }), 200
        else:
            # Se o usuário não existe ou a senha está incorreta, retorna erro 401 (Não autorizado).
            current_app.logger.warning(f"Tentativa de login mal-sucedida para o usuário {data.get('username', '[username não fornecido]')}")
            return jsonify({'message': 'Credenciais inválidas (usuário ou senha incorretos)'}), 401
        
    except Exception as e:
        # Captura qualquer outra exceção inesperada durante o processo.
        current_app.logger.error(f"Erro inesperado durante o login para {data.get('username')}: {str(e)}", exc_info=True)
        return jsonify({
            'message': 'Ocorreu um erro interno durante o login',
            'error': str(e)
        }), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    # Endpoint para registrar (criar) um novo usuário no sistema.
    # 
    # Request body:
    #     JSON com "name", "username", "email", "password" (e opcionalmente "role").
    # 
    # Returns:
    #     201: Usuário criado com sucesso, retorna dados do usuário e 'access_token'.
    #     400: Erro se os dados enviados são inválidos, ou se username/email já existem.
    #     500: Erro interno do servidor.
    try:
        # Valida os dados recebidos no corpo da requisição JSON usando o UserSchema.
        data = user_schema.load(request.json or {})
    except ValidationError as err:
        # Se a validação falhar, retorna erro 400 com os detalhes.
        current_app.logger.warning(f"Erro de validação no registro: {err.messages}. Dados: {request.json}")
        return jsonify({
            'message': 'Erro de validação nos dados de registro', 
            'errors': err.messages
        }), 400
    
    try:
        # Verifica se já existe um usuário com o mesmo username.
        if User.query.filter_by(username=data['username']).first():
            current_app.logger.info(f"Tentativa de registro falhou: username '{data['username']}' já existe.")
            return jsonify({'message': f"O nome de usuário '{data['username']}' já está em uso.", 'field': 'username'}), 400
            
        # Verifica se já existe um usuário com o mesmo email.
        if User.query.filter_by(email=data['email']).first():
            current_app.logger.info(f"Tentativa de registro falhou: email '{data['email']}' já existe.")
            return jsonify({'message': f"O e-mail '{data['email']}' já está cadastrado.", 'field': 'email'}), 400
        
        # Se username e email são únicos, cria uma nova instância de User.
        # A senha passada no construtor será automaticamente hasheada pelo setter no modelo User.
        user = User(
            name=data['name'],
            username=data['username'],
            email=data['email'],
            password=data['password'],
            # Usa o role fornecido ou o padrão 'vendedor' se não especificado.
            role=data.get('role', User.ROLE_VENDEDOR) 
        )
        
        # Adiciona o novo usuário à sessão do banco de dados.
        db.session.add(user)
        # Efetiva a transação, salvando o usuário no banco.
        db.session.commit()
        current_app.logger.info(f"Usuário '{user.username}' (ID: {user.id}) registrado com sucesso com role '{user.role}'.")
        
        # Gera um token JWT para o usuário recém-criado (opcional, mas pode ser útil).
        token = user.generate_token()
        
        # Retorna sucesso (201 Created) com mensagem, dados do usuário e o token.
        return jsonify({
            'message': 'Usuário registrado com sucesso!',
            'user': user.to_dict(),
            'access_token': token # Permite login automático após registro no frontend
        }), 201
        
    except Exception as e:
        # Em caso de qualquer erro durante a criação ou commit, desfaz a transação.
        db.session.rollback()
        current_app.logger.error(f"Erro inesperado durante o registro do usuário {data.get('username')}: {str(e)}", exc_info=True)
        return jsonify({
            'message': 'Ocorreu um erro interno ao registrar o usuário',
            'error': str(e)
        }), 500 