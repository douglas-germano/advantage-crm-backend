from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import ValidationError

from app import db
from app.api.pipeline import bp
from app.models.pipeline import Pipeline, PipelineStage
from .schemas import PipelineStageSchema

# --- INÍCIO: Adicionar schemas para Pipeline ---
from marshmallow import Schema, fields, validate

class PipelineSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    is_default = fields.Bool(dump_only=True) # Controlado internamente
    criado_em = fields.DateTime(dump_only=True)
    atualizado_em = fields.DateTime(dump_only=True)

pipeline_schema = PipelineSchema()
pipelines_schema = PipelineSchema(many=True)
# --- FIM: Adicionar schemas para Pipeline ---

pipeline_stage_schema = PipelineStageSchema()
pipeline_stage_update_schema = PipelineStageSchema(partial=True)

# --- INÍCIO: Novas Rotas para Pipelines --- 
@bp.route('/', methods=['GET'])
@jwt_required()
def get_pipelines():
    """Get all pipelines."""
    try:
        pipelines = Pipeline.query.order_by(Pipeline.name).all()
        return jsonify(pipelines_schema.dump(pipelines)), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching pipelines: {str(e)}")
        return jsonify({'error': 'Error fetching pipelines', 'details': str(e)}), 500

@bp.route('/', methods=['POST'])
@jwt_required()
def create_pipeline():
    """Create a new pipeline with default stages."""
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        # Valida os dados do pipeline
        data = pipeline_schema.load(json_data)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    # Verificar se já existe um pipeline com este nome
    if Pipeline.query.filter_by(name=data['name']).first():
        return jsonify({'message': f'Pipeline com nome "{data["name"]}" já existe.'}), 409 # Conflict

    try:
        # Cria o pipeline
        new_pipeline = Pipeline(name=data['name'], description=data.get('description'))
        db.session.add(new_pipeline)
        db.session.flush() # Para obter o ID do novo pipeline

        # Cria os estágios padrão para este pipeline
        PipelineStage.create_default_stages(new_pipeline.id)
        
        db.session.commit() # Commita o pipeline e os estágios
        
        # Retorna o pipeline criado (sem os estágios por padrão)
        return jsonify(pipeline_schema.dump(new_pipeline)), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar pipeline: {str(e)}")
        return jsonify({'error': 'Erro ao criar pipeline', 'details': str(e)}), 500
# --- FIM: Novas Rotas para Pipelines ---

@bp.route('/<int:id>/stages', methods=['GET'])
@jwt_required()
def get_pipeline_stages(id):
    """Get all stages for a specific pipeline."""
    try:
        # Verify if pipeline exists
        pipeline = Pipeline.query.get(id)
        if not pipeline:
            return jsonify({'error': 'Pipeline not found'}), 404
            
        # Get all stages for this pipeline ordered by order
        stages = PipelineStage.query.filter_by(pipeline_id=id).order_by(PipelineStage.order).all()
        
        # Convert to dict
        result = []
        for stage in stages:
            result.append(stage.to_dict())
            
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error fetching pipeline stages: {str(e)}")
        return jsonify({'error': 'Error fetching pipeline stages', 'details': str(e)}), 500

@bp.route('/default', methods=['GET'])
@jwt_required()
def get_default_pipeline():
    """Get the default pipeline."""
    try:
        # Get the default pipeline
        pipeline = Pipeline.query.filter_by(is_default=True).first()
        if not pipeline:
            return jsonify({'error': 'No default pipeline found'}), 404
            
        return jsonify(pipeline.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error fetching default pipeline: {str(e)}")
        return jsonify({'error': 'Error fetching default pipeline', 'details': str(e)}), 500

# --- COMENTAR ROTAS DE STAGES POR ENQUANTO ---
# @bp.route('/stages', methods=['GET'])
# @jwt_required()
# def get_pipeline_stages():
#     """Get all pipeline stages."""
#     try:
#         stages = PipelineStage.query.order_by(PipelineStage.order).all()
#         return jsonify([stage.to_dict() for stage in stages])
#     except Exception as e:
#         current_app.logger.error(f"Error fetching pipeline stages: {str(e)}")
#         return jsonify({'error': 'Error fetching pipeline stages', 'details': str(e)}), 500
#
# @bp.route('/stages/<int:stage_id>', methods=['GET'])
# @jwt_required()
# def get_pipeline_stage(stage_id):
#     """Get a specific pipeline stage by ID."""
#     try:
#         stage = PipelineStage.query.get(stage_id)
#         if not stage:
#             return jsonify({'error': 'Pipeline stage not found'}), 404
#         return jsonify(stage.to_dict())
#     except Exception as e:
#         current_app.logger.error(f"Error fetching pipeline stage: {str(e)}")
#         return jsonify({'error': 'Error fetching pipeline stage', 'details': str(e)}), 500
#
# @bp.route('/stages', methods=['POST'])
# @jwt_required()
# def create_pipeline_stage():
#     """Create a new pipeline stage with schema validation."""
#     jwt_data = get_jwt()
#     if jwt_data.get('role') != 'admin':
#         return jsonify({'message': 'Apenas administradores podem criar estágios de pipeline'}), 403
#
#     try:
#         # Valida os dados usando o schema
#         data = pipeline_stage_schema.load(request.json or {})
#     except ValidationError as err:
#         return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400
#
#     try:
#         # Cria o estágio usando dados validados
#         stage = PipelineStage(**data)
#         
#         # Garante que is_system não seja definido como True via API
#         stage.is_system = False 
#         
#         db.session.add(stage)
#         db.session.commit()
#         return jsonify(stage.to_dict()), 201
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"Erro ao criar estágio de pipeline: {str(e)}")
#         return jsonify({'error': 'Erro ao criar estágio de pipeline', 'details': str(e)}), 500
#
# @bp.route('/stages/<int:stage_id>', methods=['PUT'])
# @jwt_required()
# def update_pipeline_stage(stage_id):
#     """Update an existing pipeline stage with schema validation."""
#     jwt_data = get_jwt()
#     if jwt_data.get('role') != 'admin':
#         return jsonify({'message': 'Apenas administradores podem atualizar estágios de pipeline'}), 403
#
#     stage = PipelineStage.query.get(stage_id)
#     if not stage:
#         return jsonify({'error': 'Estágio do pipeline não encontrado'}), 404
#
#     # Não permitir edição de estágios do sistema
#     if stage.is_system:
#          return jsonify({'message': 'Não é possível editar estágios do sistema'}), 403
#
#     try:
#         # Valida os dados usando o schema de atualização (partial=True)
#         data = pipeline_stage_update_schema.load(request.json or {})
#     except ValidationError as err:
#         return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400
#
#     try:
#         # Atualiza os campos do estágio com os dados validados
#         for field, value in data.items():
#             # Evitar que is_system seja modificado via API
#             if field != 'is_system': 
#                 setattr(stage, field, value)
#         
#         db.session.commit()
#         return jsonify(stage.to_dict()), 200
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"Erro ao atualizar estágio de pipeline {stage_id}: {str(e)}")
#         return jsonify({'error': 'Erro ao atualizar estágio de pipeline', 'details': str(e)}), 500
#
# @bp.route('/stages/<int:stage_id>', methods=['DELETE'])
# @jwt_required()
# def delete_pipeline_stage(stage_id):
#     """Delete a pipeline stage."""
#     try:
#         stage = PipelineStage.query.get(stage_id)
#         if not stage:
#             return jsonify({'error': 'Pipeline stage not found'}), 404
#         
#         # Don't allow deleting system stages
#         if stage.is_system:
#             return jsonify({'error': 'Cannot delete a system stage'}), 403
#         
#         db.session.delete(stage)
#         db.session.commit()
#         
#         return jsonify({'message': 'Pipeline stage deleted successfully'})
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"Error deleting pipeline stage: {str(e)}")
#         return jsonify({'error': 'Error deleting pipeline stage', 'details': str(e)}), 500
#
# @bp.route('/stages/reorder', methods=['POST'])
# @jwt_required()
# def reorder_pipeline_stages():
#     """Reorder pipeline stages."""
#     try:
#         data = request.get_json() or {}
#         
#         if not data or 'stages' not in data:
#             return jsonify({'error': 'Invalid data - stages array required'}), 400
#         
#         stages = data['stages']
#         
#         # Validate the stage IDs
#         stage_ids = [stage.get('id') for stage in stages if 'id' in stage]
#         db_stages = PipelineStage.query.filter(PipelineStage.id.in_(stage_ids)).all()
#         
#         if len(db_stages) != len(stage_ids):
#             return jsonify({'error': 'One or more stage IDs are invalid'}), 400
#         
#         # Update the order
#         for stage_data in stages:
#             if 'id' in stage_data and 'order' in stage_data:
#                 stage = next((s for s in db_stages if s.id == stage_data['id']), None)
#                 if stage:
#                     stage.order = stage_data['order']
#         
#         db.session.commit()
#         
#         # Return the updated stages
#         all_stages = PipelineStage.query.order_by(PipelineStage.order).all()
#         return jsonify([stage.to_dict() for stage in all_stages])
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"Error reordering pipeline stages: {str(e)}")
#         return jsonify({'error': 'Error reordering pipeline stages', 'details': str(e)}), 500
#
# @bp.route('/stages/initialize', methods=['POST'])
# @jwt_required()
# def initialize_default_stages():
#     """Initialize the default pipeline stages if none exist."""
#     try:
#         # Check if any stages already exist
#         existing_stages = PipelineStage.query.count()
#         if existing_stages > 0:
#             return jsonify({'message': 'Pipeline stages already exist', 'count': existing_stages}), 200
#         
#         # Create default stages
#         PipelineStage.create_default_stages()
#         
#         # Return the newly created stages
#         stages = PipelineStage.query.order_by(PipelineStage.order).all()
#         return jsonify([stage.to_dict() for stage in stages]), 201
#     except Exception as e:
#         db.session.rollback()
#         current_app.logger.error(f"Error initializing default pipeline stages: {str(e)}")
#         return jsonify({'error': 'Error initializing default pipeline stages', 'details': str(e)}), 500
# --- FIM COMENTÁRIOS --- 