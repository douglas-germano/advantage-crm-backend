import json
from flask import request, jsonify, current_app
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt

from app import db
from app.models import CustomField, CustomFieldValue
# Import blueprint from the module's __init__.py
from . import custom_fields_bp
from .schemas import CustomFieldSchema

# custom_fields_bp = Blueprint('custom_fields', __name__, url_prefix='/custom-fields') # Removed: Defined in __init__.py

custom_field_schema = CustomFieldSchema()
custom_fields_schema = CustomFieldSchema(many=True) # Para listas

@custom_fields_bp.route('/', methods=['GET'])
@jwt_required()
def get_custom_fields():
    """Lista todos os campos personalizados"""
    try:
        show_all = request.args.get('show_all', 'false').lower() == 'true'
        if show_all:
            custom_fields = CustomField.query.all()
        else:
            custom_fields = CustomField.query.filter_by(active=True).all()
        return jsonify({'custom_fields': [cf.to_dict() for cf in custom_fields]}), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar campos personalizados: {str(e)}")
        return jsonify({'error': 'Erro ao listar campos personalizados', 'details': str(e)}), 500

@custom_fields_bp.route('/', methods=['POST'])
@jwt_required()
def create_custom_field():
    """Cria um novo campo personalizado"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != 'admin':
        return jsonify({'message': 'Apenas administradores podem criar campos personalizados'}), 403

    try:
        data = custom_field_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        if CustomField.query.filter_by(name=data['name']).first():
            return jsonify({'message': 'Já existe um campo com este nome'}), 400
        
        options_json = None
        if 'options' in data and data.get('field_type') == 'select':
            options_json = json.dumps(data.get('options'))
            
        custom_field = CustomField(
            name=data['name'],
            field_type=data['field_type'],
            required=data.get('required', False),
            options=options_json, # Salva como JSON string
            active=data.get('active', True)
        )
        
        db.session.add(custom_field)
        db.session.commit()
        return jsonify({
            'message': 'Campo personalizado criado com sucesso',
            'custom_field': custom_field.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar campo personalizado: {str(e)}")
        return jsonify({'error': 'Erro ao criar campo personalizado', 'details': str(e)}), 500

@custom_fields_bp.route('/<int:field_id>', methods=['GET'])
@jwt_required()
def get_custom_field(field_id):
    """Obtém os detalhes de um campo personalizado"""
    try:
        custom_field = CustomField.query.get(field_id)
        if not custom_field:
            return jsonify({'message': 'Campo personalizado não encontrado'}), 404
        return jsonify({'custom_field': custom_field.to_dict()}), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar campo personalizado {field_id}: {str(e)}")
        return jsonify({'error': 'Erro ao buscar campo personalizado', 'details': str(e)}), 500

@custom_fields_bp.route('/<int:field_id>', methods=['PUT'])
@jwt_required()
def update_custom_field(field_id):
    """Atualiza um campo personalizado"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != 'admin':
        return jsonify({'message': 'Apenas administradores podem atualizar campos personalizados'}), 403

    custom_field = CustomField.query.get(field_id)
    if not custom_field:
        return jsonify({'message': 'Campo personalizado não encontrado'}), 404

    try:
        data = custom_field_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        existing = CustomField.query.filter(CustomField.name == data['name'], CustomField.id != field_id).first()
        if existing:
            return jsonify({'message': 'Já existe outro campo com este nome'}), 400
        
        custom_field.name = data.get('name', custom_field.name)
        custom_field.field_type = data.get('field_type', custom_field.field_type)
        custom_field.required = data.get('required', custom_field.required)
        
        if 'options' in data and data.get('field_type') == 'select':
            custom_field.options = json.dumps(data['options'])
        elif data.get('field_type') != 'select': # Clear options if not select type
             custom_field.options = None
             
        custom_field.active = data.get('active', custom_field.active)
        
        db.session.commit()
        return jsonify({
            'message': 'Campo personalizado atualizado com sucesso',
            'custom_field': custom_field.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar campo personalizado {field_id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar campo personalizado', 'details': str(e)}), 500

@custom_fields_bp.route('/<int:field_id>', methods=['DELETE'])
@jwt_required()
def delete_custom_field(field_id):
    """Remove um campo personalizado ou marca como inativo se estiver em uso"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != 'admin':
        return jsonify({'message': 'Apenas administradores podem remover campos personalizados'}), 403

    custom_field = CustomField.query.get(field_id)
    if not custom_field:
        return jsonify({'message': 'Campo personalizado não encontrado'}), 404

    try:
        # Verifica se o campo está sendo usado
        values_exist = CustomFieldValue.query.filter_by(custom_field_id=field_id).first()
        
        if values_exist:
            custom_field.active = False
            db.session.commit()
            return jsonify({'message': 'Campo personalizado marcado como inativo pois está em uso'}), 200
        else:
            db.session.delete(custom_field)
            db.session.commit()
            return jsonify({'message': 'Campo personalizado removido com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao remover campo personalizado {field_id}: {str(e)}")
        return jsonify({'error': 'Erro ao remover campo personalizado', 'details': str(e)}), 500 