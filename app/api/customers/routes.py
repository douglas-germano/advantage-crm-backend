from flask import request, jsonify, current_app
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app import db
from app.models import Customer, CustomField, CustomFieldValue, User
from . import customers_bp
from .schemas import CustomerSchema

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

@customers_bp.route('/', methods=['GET'])
@jwt_required()
def get_customers():
    """Lista todos os clientes com filtros opcionais"""
    try:
        status = request.args.get('status')
        assigned_to = request.args.get('assigned_to')
        search = request.args.get('search')
        
        query = Customer.query
        
        if status:
            query = query.filter(Customer.status == status)
        if assigned_to:
            query = query.filter(Customer.assigned_to == assigned_to)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Customer.name.ilike(search_term) | 
                Customer.email.ilike(search_term) | 
                Customer.company.ilike(search_term)
            )
            
        customers = query.all()
        # Usar to_dict() aqui pois o schema é mais para validação de entrada
        return jsonify({'customers': [c.to_dict() for c in customers]}), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar clientes: {str(e)}")
        return jsonify({'error': 'Erro ao listar clientes', 'details': str(e)}), 500

@customers_bp.route('/', methods=['POST'])
@jwt_required()
def create_customer():
    """Cria um novo cliente"""
    try:
        data = customer_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        if data.get('assigned_to') and not User.query.get(data['assigned_to']):
            return jsonify({'message': 'Usuário responsável não encontrado'}), 400
            
        custom_fields_data = data.pop('custom_fields', {})
        
        customer = Customer(
            name=data['name'],
            email=data.get('email'),
            phone=data.get('phone'),
            company=data.get('company'),
            address=data.get('address'),
            status=data.get('status', 'lead'),
            assigned_to=data.get('assigned_to')
        )
        
        db.session.add(customer)
        db.session.flush() 
        
        for field_id, value in custom_fields_data.items():
            field = CustomField.query.get(int(field_id))
            if field:
                field_value = CustomFieldValue(
                    customer_id=customer.id,
                    custom_field_id=field.id,
                    value=value
                )
                db.session.add(field_value)
        
        db.session.commit()
        return jsonify({
            'message': 'Cliente criado com sucesso',
            'customer': customer.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar cliente: {str(e)}")
        return jsonify({'error': 'Erro ao criar cliente', 'details': str(e)}), 500

@customers_bp.route('/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    """Obtém os detalhes de um cliente"""
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'message': 'Cliente não encontrado'}), 404
        return jsonify({'customer': customer.to_dict()}), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar cliente {customer_id}: {str(e)}")
        return jsonify({'error': 'Erro ao buscar cliente', 'details': str(e)}), 500

@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    """Atualiza um cliente"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'message': 'Cliente não encontrado'}), 404

    try:
        data = customer_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        if data.get('assigned_to') and not User.query.get(data['assigned_to']):
            return jsonify({'message': 'Usuário responsável não encontrado'}), 400
            
        custom_fields_data = data.pop('custom_fields', {})
        
        # Atualiza campos usando .get com valor padrão sendo o valor atual
        customer.name = data.get('name', customer.name)
        customer.email = data.get('email', customer.email)
        customer.phone = data.get('phone', customer.phone)
        customer.company = data.get('company', customer.company)
        customer.address = data.get('address', customer.address)
        customer.status = data.get('status', customer.status)
        customer.assigned_to = data.get('assigned_to', customer.assigned_to)
        
        # Assume que o modelo Customer tem um método para lidar com isso
        # Se não tiver, a lógica de resources.py precisa ser adaptada aqui
        for field_id, value in custom_fields_data.items():
             # Implementar a lógica de atualização de campos personalizados aqui
             # Exemplo: customer.update_custom_field(field_id, value)
             # Por segurança, vamos apenas logar por enquanto
             current_app.logger.info(f"Atualizando campo {field_id} para {value} no cliente {customer_id}")
             # Adapte conforme a implementação do seu modelo Customer
             pass # Remova este pass e adicione a lógica real
        
        db.session.commit()
        return jsonify({
            'message': 'Cliente atualizado com sucesso',
            'customer': customer.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar cliente {customer_id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar cliente', 'details': str(e)}), 500

@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    """Remove um cliente"""
    customer = Customer.query.get(customer_id)
    if not customer:
        return jsonify({'message': 'Cliente não encontrado'}), 404
        
    try:
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id_str = get_jwt_identity()
        
        # Permite admin ou o usuário responsável pelo cliente
        if user_role != 'admin' and str(customer.assigned_to) != current_user_id_str:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Lógica para lidar com dependências (leads, deals, etc.) pode ser necessária aqui
        
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'message': 'Cliente removido com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao remover cliente {customer_id}: {str(e)}")
        return jsonify({'error': 'Erro ao remover cliente', 'details': str(e)}), 500 