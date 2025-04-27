from flask import request, jsonify, current_app
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime

from app import db
from app.models import Task, User
from . import tasks_bp
from .schemas import TaskSchema

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    """Lista todas as tarefas com filtros opcionais"""
    try:
        # Parâmetros de filtro
        status = request.args.get('status')
        priority = request.args.get('priority')
        assigned_to = request.args.get('assigned_to')
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')
        task_type = request.args.get('task_type')
        search = request.args.get('search')
        
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Limita a 100 itens por página
        
        query = Task.query
        
        # Aplicar filtros
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if assigned_to:
            query = query.filter(Task.assigned_to == assigned_to)
        if entity_type:
            query = query.filter(Task.entity_type == entity_type)
        if entity_id:
            query = query.filter(Task.entity_id == entity_id)
        if task_type:
            query = query.filter(Task.task_type == task_type)
        if search:
            search_term = f"%{search}%"
            query = query.filter(Task.title.ilike(search_term) | Task.description.ilike(search_term))
            
        # Ordenação padrão: primeiro as tarefas pendentes ordenadas por prioridade e data
        query = query.order_by(
            db.case(
                (Task.status == 'pending', 1),
                (Task.status == 'in_progress', 2),
                (Task.status == 'completed', 3),
                (Task.status == 'canceled', 4),
                else_=5
            ),
            db.case(
                (Task.priority == 'high', 1),
                (Task.priority == 'medium', 2),
                (Task.priority == 'low', 3),
                else_=4
            ),
            Task.due_date.asc().nullslast()
        )
        
        # Executar a consulta paginada
        paginated_tasks = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Preparar a resposta
        return jsonify({
            'tasks': [task.to_dict() for task in paginated_tasks.items],
            'pagination': {
                'total_items': paginated_tasks.total,
                'total_pages': paginated_tasks.pages,
                'current_page': paginated_tasks.page,
                'per_page': paginated_tasks.per_page,
                'has_next': paginated_tasks.has_next,
                'has_prev': paginated_tasks.has_prev
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar tarefas: {str(e)}")
        return jsonify({'error': 'Erro ao listar tarefas', 'details': str(e)}), 500

@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    """Cria uma nova tarefa"""
    try:
        data = request.json or {}
        
        # Preencher o contexto para validação
        task_schema.context = {
            'entity_type': data.get('entity_type'),
            'start_date': datetime.strptime(data.get('start_date'), '%Y-%m-%d %H:%M:%S') if data.get('start_date') else None
        }
        
        # Validar dados com o schema
        validated_data = task_schema.load(data)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar se o usuário responsável existe
        if validated_data.get('assigned_to') and not User.query.get(validated_data['assigned_to']):
            return jsonify({'message': 'Usuário responsável não encontrado'}), 400
            
        # Criar a tarefa
        task = Task(
            title=validated_data['title'],
            description=validated_data.get('description'),
            start_date=validated_data.get('start_date'),
            due_date=validated_data.get('due_date'),
            status=validated_data.get('status', 'pending'),
            priority=validated_data.get('priority', 'medium'),
            task_type=validated_data.get('task_type'),
            entity_type=validated_data.get('entity_type'),
            entity_id=validated_data.get('entity_id'),
            assigned_to=validated_data.get('assigned_to'),
            reminder_date=validated_data.get('reminder_date')
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa criada com sucesso',
            'task': task.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar tarefa: {str(e)}")
        return jsonify({'error': 'Erro ao criar tarefa', 'details': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Obtém os detalhes de uma tarefa específica"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Tarefa não encontrada'}), 404
        return jsonify({'task': task.to_dict()}), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar tarefa {task_id}: {str(e)}")
        return jsonify({'error': 'Erro ao buscar tarefa', 'details': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Atualiza uma tarefa existente"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Tarefa não encontrada'}), 404
            
        data = request.json or {}
        
        # Preencher o contexto para validação
        task_schema.context = {
            'entity_type': data.get('entity_type', task.entity_type),
            'start_date': datetime.strptime(data.get('start_date', task.start_date.strftime('%Y-%m-%d %H:%M:%S')), 
                                         '%Y-%m-%d %H:%M:%S') if data.get('start_date') or task.start_date else None
        }
        
        # Validar dados parcialmente (permitir atualização parcial)
        validated_data = task_schema.load(data, partial=True)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar se o usuário responsável existe
        if validated_data.get('assigned_to') and not User.query.get(validated_data['assigned_to']):
            return jsonify({'message': 'Usuário responsável não encontrado'}), 400
            
        # Atualizar campos
        for field, value in validated_data.items():
            setattr(task, field, value)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa atualizada com sucesso',
            'task': task.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar tarefa {task_id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar tarefa', 'details': str(e)}), 500

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Remove uma tarefa"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Tarefa não encontrada'}), 404
            
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir exclusão apenas para admins ou o usuário responsável
        if user_role != 'admin' and task.assigned_to != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        db.session.delete(task)
        db.session.commit()
        
        return jsonify({'message': 'Tarefa removida com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao remover tarefa {task_id}: {str(e)}")
        return jsonify({'error': 'Erro ao remover tarefa', 'details': str(e)}), 500

@tasks_bp.route('/<int:task_id>/complete', methods=['POST'])
@jwt_required()
def complete_task(task_id):
    """Marca uma tarefa como concluída"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Tarefa não encontrada'}), 404
            
        # Verificar se a tarefa já está concluída
        if task.status == 'completed':
            return jsonify({'message': 'A tarefa já está concluída'}), 400
            
        # Marcar como concluída
        task.complete()
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa marcada como concluída',
            'task': task.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao concluir tarefa {task_id}: {str(e)}")
        return jsonify({'error': 'Erro ao concluir tarefa', 'details': str(e)}), 500

@tasks_bp.route('/<int:task_id>/reopen', methods=['POST'])
@jwt_required()
def reopen_task(task_id):
    """Reabre uma tarefa concluída ou cancelada"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'message': 'Tarefa não encontrada'}), 404
            
        # Verificar se a tarefa está em um estado que pode ser reaberto
        if task.status not in ['completed', 'canceled']:
            return jsonify({'message': 'Apenas tarefas concluídas ou canceladas podem ser reabertas'}), 400
            
        # Reabrir a tarefa
        task.reopen()
        db.session.commit()
        
        return jsonify({
            'message': 'Tarefa reaberta com sucesso',
            'task': task.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao reabrir tarefa {task_id}: {str(e)}")
        return jsonify({'error': 'Erro ao reabrir tarefa', 'details': str(e)}), 500
