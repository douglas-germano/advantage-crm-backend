from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from . import bp  # Import the Blueprint defined in __init__.py
from app import db
from app.models.user import User
# Importa os schemas específicos de users
from .schemas import UserUpdateSchema, PasswordUpdateSchema, AdminUserCreateSchema

user_update_schema = UserUpdateSchema()
password_update_schema = PasswordUpdateSchema()
admin_user_create_schema = AdminUserCreateSchema()

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Obtém informações do usuário autenticado."""
    try:
        # Verificar o token e obter o ID do usuário
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Token validado com sucesso. Buscando dados do usuário: {current_user_id}")
        
        # Buscar o usuário atual
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
            
        return jsonify(user.to_dict())
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar dados do usuário atual: {str(e)}")
        return jsonify({'error': 'Erro ao buscar dados do usuário', 'details': str(e)}), 500

@bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Atualiza informações do usuário autenticado usando schema."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    try:
        # Valida os dados usando o schema de atualização
        data = user_update_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar duplicidade de username/email antes de atualizar
        if 'username' in data and data['username'] != user.username and User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Erro de validação', 'errors': {'username':['Nome de usuário já existe']}}), 400
        if 'email' in data and data['email'] != user.email and User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Erro de validação', 'errors': {'email':['E-mail já cadastrado']}}), 400

        # Atualizar os campos permitidos (name, username, email)
        for field, value in data.items():
            setattr(user, field, value)
                
        db.session.commit()
        return jsonify(user.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar dados do usuário {current_user_id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar dados do usuário', 'details': str(e)}), 500

@bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """Obtém todos os usuários (apenas para admins)."""
    try:
        # Verificar o token e obter o ID do usuário
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Token validado com sucesso. ID do usuário: {current_user_id}")
        
        # Buscar o usuário atual para verificar se é admin
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Acesso negado. Apenas administradores podem listar usuários.'}), 403
            
        # Buscar todos os usuários
        users = User.query.all()
        current_app.logger.info(f"Encontrados {len(users)} usuários")
        
        # Formatar a resposta
        result = {
            'users': [user.to_dict() for user in users]
        }
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Erro ao listar usuários: {str(e)}")
        return jsonify({'error': 'Erro ao listar usuários', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    """Obtém um usuário específico pelo ID."""
    try:
        # Verificar o token e obter o ID do usuário
        current_user_id = get_jwt_identity()
        
        # Buscar o usuário atual para verificar permissões
        current_user = User.query.get(current_user_id)
        if not current_user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
            
        # Se não for admin e estiver tentando acessar outro usuário
        if current_user.role != 'admin' and str(current_user_id) != str(id):
            return jsonify({'error': 'Acesso negado. Você só pode visualizar seu próprio perfil.'}), 403
            
        # Buscar o usuário solicitado
        user = User.query.get(id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
            
        return jsonify(user.to_dict())
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar usuário: {str(e)}")
        return jsonify({'error': 'Erro ao buscar usuário', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    """Atualiza um usuário existente (admin ou próprio usuário)."""
    current_user_id_str = get_jwt_identity()
    current_user = User.query.get(current_user_id_str)
    if not current_user:
        # Should not happen if token is valid, but good practice
        return jsonify({'error': 'Usuário autenticado não encontrado'}), 401 

    user_to_update = User.query.get(id)
    if not user_to_update:
        return jsonify({'error': 'Usuário a ser atualizado não encontrado'}), 404

    # Verifica permissão (admin pode editar qualquer um, usuário normal só a si mesmo)
    if not current_user.is_admin() and str(id) != current_user_id_str:
         return jsonify({'error': 'Acesso negado. Você só pode editar seu próprio perfil.'}), 403

    try:
        # Valida os dados recebidos
        data = user_update_schema.load(request.json or {})
        # Admin pode adicionalmente enviar 'role'
        if current_user.is_admin() and 'role' in request.json:
            role = request.json['role']
            if role not in User.VALID_ROLES:
                 raise ValidationError({'role': ['Função inválida.']})
            data['role'] = role # Adiciona role aos dados validados se admin e válido
            
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar duplicidade de username/email antes de atualizar
        if 'username' in data and data['username'] != user_to_update.username and User.query.filter(User.username == data['username'], User.id != id).first():
             return jsonify({'message': 'Erro de validação', 'errors': {'username':['Nome de usuário já existe']}}), 400
        if 'email' in data and data['email'] != user_to_update.email and User.query.filter(User.email == data['email'], User.id != id).first():
            return jsonify({'message': 'Erro de validação', 'errors': {'email':['E-mail já cadastrado']}}), 400

        # Atualizar os campos
        for field, value in data.items():
            setattr(user_to_update, field, value)
                
        db.session.commit()
        return jsonify(user_to_update.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar usuário {id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar usuário', 'details': str(e)}), 500

@bp.route('/<int:id>/password', methods=['PUT'])
@jwt_required()
def update_password(id):
    """Atualiza a senha de um usuário usando schema."""
    current_user_id_str = get_jwt_identity()
    current_user = User.query.get(current_user_id_str)
    user_to_update = User.query.get(id)

    if not user_to_update:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    is_self_update = (str(id) == current_user_id_str)

    # Verifica permissão (admin pode editar qualquer um, usuário normal só a si mesmo)
    if not current_user.is_admin() and not is_self_update:
        return jsonify({'error': 'Acesso negado. Você só pode alterar sua própria senha.'}), 403

    try:
        # Valida os dados recebidos
        data = password_update_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Se for o próprio usuário, verificar senha atual
        if is_self_update:
            current_password = data.get('current_password')
            if not current_password:
                 return jsonify({'message': 'Erro de validação', 'errors': {'current_password':['Senha atual é obrigatória.']}}), 400
            if not user_to_update.verify_password(current_password):
                return jsonify({'message': 'Senha atual incorreta'}), 401
                
        # Atualizar senha (o schema já validou a presença de new_password)
        user_to_update.password = data['new_password']
        db.session.commit()
        
        return jsonify({'message': 'Senha atualizada com sucesso'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar senha do usuário {id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar senha', 'details': str(e)}), 500

@bp.route('/', methods=['POST'])
@jwt_required()
def create_user():
    """Cria um novo usuário (admin only) usando schema."""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.is_admin():
        return jsonify({'error': 'Acesso negado. Apenas administradores podem criar usuários.'}), 403
            
    try:
        # Valida os dados usando o schema específico para criação por admin
        data = admin_user_create_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar se o nome de usuário ou e-mail já existem (redundante com auth/register, mas bom ter aqui)
        if User.query.filter_by(username=data['username']).first():
             return jsonify({'message': 'Erro de validação', 'errors': {'username':['Nome de usuário já existe']}}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Erro de validação', 'errors': {'email':['E-mail já cadastrado']}}), 400
            
        # Criar novo usuário
        user = User(
            name=data['name'],
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'vendedor') # Usa role validado ou default
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify(user.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar usuário via admin: {str(e)}")
        return jsonify({'error': 'Erro ao criar usuário', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    """Exclui um usuário (apenas para admins)."""
    try:
        # Verificar o token e obter o ID do usuário
        current_user_id = get_jwt_identity()
        
        # Verificar se é admin
        current_user = User.query.get(current_user_id)
        if not current_user or current_user.role != 'admin':
            return jsonify({'error': 'Acesso negado. Apenas administradores podem excluir usuários.'}), 403
            
        # Não permitir que um usuário se exclua
        if str(current_user_id) == str(id):
            return jsonify({'error': 'Você não pode excluir seu próprio usuário'}), 400
            
        # Buscar o usuário a ser excluído
        user = User.query.get(id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
            
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'Usuário excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao excluir usuário: {str(e)}")
        return jsonify({'error': 'Erro ao excluir usuário', 'details': str(e)}), 500 