from flask import request, jsonify, current_app
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import json

from app import db
from app.models import Workflow, WorkflowAction, User
from . import workflows_bp
from .schemas import WorkflowSchema, WorkflowActionSchema

workflow_schema = WorkflowSchema()
workflows_schema = WorkflowSchema(many=True)
action_schema = WorkflowActionSchema()

@workflows_bp.route('/', methods=['GET'])
@jwt_required()
def get_workflows():
    """Lista todos os workflows com filtros opcionais"""
    try:
        # Parâmetros de filtro
        entity_type = request.args.get('entity_type')
        is_active = request.args.get('is_active')
        trigger_type = request.args.get('trigger_type')
        search = request.args.get('search')
        
        query = Workflow.query
        
        # Aplicar filtros
        if entity_type:
            query = query.filter(Workflow.entity_type == entity_type)
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            query = query.filter(Workflow.is_active == is_active_bool)
        if trigger_type:
            query = query.filter(Workflow.trigger_type == trigger_type)
        if search:
            search_term = f"%{search}%"
            query = query.filter(Workflow.name.ilike(search_term) | Workflow.description.ilike(search_term))
        
        # Ordenação padrão: workflows ativos primeiro, depois por nome
        query = query.order_by(Workflow.is_active.desc(), Workflow.name)
        
        workflows = query.all()
        
        # Preparar a resposta
        return jsonify({
            'workflows': [workflow.to_dict() for workflow in workflows]
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar workflows: {str(e)}")
        return jsonify({'error': 'Erro ao listar workflows', 'details': str(e)}), 500

@workflows_bp.route('/', methods=['POST'])
@jwt_required()
def create_workflow():
    """Cria um novo workflow de automação"""
    try:
        data = request.json or {}
        
        # Obter o ID do usuário atual
        current_user_id = get_jwt_identity()
        data['created_by'] = current_user_id
        
        # Configurar contexto para validação
        workflow_schema.context = {
            'trigger_type': data.get('trigger_type')
        }
        
        # Validar dados com o schema
        validated_data = workflow_schema.load(data)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Extrair dados das ações para processamento separado
        actions_data = validated_data.pop('actions', [])
        
        # Criar workflow
        workflow = Workflow(
            name=validated_data['name'],
            description=validated_data.get('description'),
            entity_type=validated_data['entity_type'],
            trigger_type=validated_data['trigger_type'],
            trigger_data=validated_data.get('trigger_data'),
            is_active=validated_data.get('is_active', True),
            created_by=validated_data['created_by']
        )
        
        db.session.add(workflow)
        db.session.flush()  # Obter ID sem commit
        
        # Adicionar ações
        for action_data in actions_data:
            action = WorkflowAction(
                workflow_id=workflow.id,
                sequence=action_data['sequence'],
                action_type=action_data['action_type'],
                action_data=action_data['action_data'],
                condition=action_data.get('condition')
            )
            db.session.add(action)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Workflow criado com sucesso',
            'workflow': workflow.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar workflow: {str(e)}")
        return jsonify({'error': 'Erro ao criar workflow', 'details': str(e)}), 500

@workflows_bp.route('/<int:workflow_id>', methods=['GET'])
@jwt_required()
def get_workflow(workflow_id):
    """Obtém os detalhes de um workflow específico"""
    try:
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            return jsonify({'message': 'Workflow não encontrado'}), 404
        return jsonify({'workflow': workflow.to_dict()}), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Erro ao buscar workflow', 'details': str(e)}), 500

@workflows_bp.route('/<int:workflow_id>', methods=['PUT'])
@jwt_required()
def update_workflow(workflow_id):
    """Atualiza um workflow existente"""
    try:
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            return jsonify({'message': 'Workflow não encontrado'}), 404
            
        data = request.json or {}
        
        # Configurar contexto para validação
        workflow_schema.context = {
            'trigger_type': data.get('trigger_type', workflow.trigger_type)
        }
        
        # Validar dados parcialmente
        validated_data = workflow_schema.load(data, partial=True)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir edição apenas para admins ou o criador do workflow
        if user_role != 'admin' and str(workflow.created_by) != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Extrair dados das ações para processamento separado
        actions_data = validated_data.pop('actions', None)
        
        # Atualizar campos básicos do workflow
        for field, value in validated_data.items():
            setattr(workflow, field, value)
        
        # Se novas ações foram fornecidas, atualizar
        if actions_data is not None:
            # Remover ações existentes
            for action in workflow.actions:
                db.session.delete(action)
            
            # Adicionar novas ações
            for action_data in actions_data:
                action = WorkflowAction(
                    workflow_id=workflow.id,
                    sequence=action_data['sequence'],
                    action_type=action_data['action_type'],
                    action_data=action_data['action_data'],
                    condition=action_data.get('condition')
                )
                db.session.add(action)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Workflow atualizado com sucesso',
            'workflow': workflow.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar workflow', 'details': str(e)}), 500

@workflows_bp.route('/<int:workflow_id>', methods=['DELETE'])
@jwt_required()
def delete_workflow(workflow_id):
    """Remove um workflow"""
    try:
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            return jsonify({'message': 'Workflow não encontrado'}), 404
            
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir exclusão apenas para admins ou o criador do workflow
        if user_role != 'admin' and str(workflow.created_by) != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Excluir o workflow (e suas ações via cascade)
        db.session.delete(workflow)
        db.session.commit()
        
        return jsonify({'message': 'Workflow removido com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao remover workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Erro ao remover workflow', 'details': str(e)}), 500

@workflows_bp.route('/<int:workflow_id>/toggle', methods=['POST'])
@jwt_required()
def toggle_workflow(workflow_id):
    """Ativa ou desativa um workflow"""
    try:
        workflow = Workflow.query.get(workflow_id)
        if not workflow:
            return jsonify({'message': 'Workflow não encontrado'}), 404
            
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir alteração apenas para admins ou o criador do workflow
        if user_role != 'admin' and str(workflow.created_by) != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Inverter o estado de ativação
        workflow.is_active = not workflow.is_active
        
        db.session.commit()
        
        status = 'ativado' if workflow.is_active else 'desativado'
        return jsonify({
            'message': f'Workflow {status} com sucesso',
            'workflow': workflow.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao alterar status do workflow {workflow_id}: {str(e)}")
        return jsonify({'error': 'Erro ao alterar status do workflow', 'details': str(e)}), 500
