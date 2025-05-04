from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app import db
from app.api.deals import bp
from app.models.deal import Deal
from app.models.pipeline import PipelineStage
from .schemas import DealSchema

deal_schema = DealSchema()
deal_update_schema = DealSchema(partial=True)

@bp.route('/', methods=['GET'])
@jwt_required()
def get_deals():
    """Get all deals."""
    try:
        # Verify token and get user ID
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Token validated successfully. User ID: {current_user_id}")
        
        # Pagination parameters with extra validation
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 10, type=int), 100)
            current_app.logger.info(f"Pagination parameters: page={page}, per_page={per_page}")
        except Exception as e:
            current_app.logger.error(f"Error processing pagination parameters: {str(e)}")
            page = 1
            per_page = 10
        
        # Basic query for diagnostics
        try:
            query = Deal.query
            
            # Process filters
            current_app.logger.info(f"Request args: {request.args}")
            
            # Filter by pipeline stage
            if request.args.get('pipeline_stage_id'):
                try:
                    stage_id = int(request.args.get('pipeline_stage_id'))
                    query = query.filter(Deal.pipeline_stage_id == stage_id)
                    current_app.logger.info(f"Filtering by pipeline stage: {stage_id}")
                except ValueError:
                    current_app.logger.error("Invalid pipeline_stage_id format")
            
            # Filter by title (partial search)
            if request.args.get('title'):
                title_query = f"%{request.args.get('title')}%"
                query = query.filter(Deal.title.ilike(title_query))
                current_app.logger.info(f"Filtering by title: {title_query}")
            
            # Filter by status (exact match)
            if request.args.get('status'):
                query = query.filter(Deal.status == request.args.get('status'))
                current_app.logger.info(f"Filtering by status: {request.args.get('status')}")
            
            # Order by creation date, from most recent to oldest
            query = query.order_by(Deal.criado_em.desc())
            
            # Simple test with a limit before paginating
            deals_count = query.count()
            current_app.logger.info(f"Total deals found after applying filters: {deals_count}")
            
            # Paginate the results
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            deals = pagination.items
            current_app.logger.info(f"Pagination successful. {len(deals)} deals on page {page}")
            
            # Build response carefully
            deal_list = []
            for deal in deals:
                try:
                    deal_dict = deal.to_dict()
                    deal_list.append(deal_dict)
                except Exception as e:
                    current_app.logger.error(f"Error processing deal {deal.id}: {str(e)}")
            
            result = {
                'items': deal_list,
                'total': pagination.total,
                'pages': pagination.pages,
                'page': page,
                'per_page': per_page
            }
            
            current_app.logger.info("Response prepared successfully")
            return jsonify(result)
            
        except Exception as e:
            current_app.logger.error(f"Error querying the database: {str(e)}")
            return jsonify({'error': 'Error querying deals from the database', 'details': str(e)}), 500
            
    except Exception as e:
        current_app.logger.error(f"Global error when listing deals: {str(e)}")
        return jsonify({'error': 'Error listing deals', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_deal(id):
    """Get a specific deal by ID."""
    try:
        deal = Deal.query.get(id)
        if not deal:
            return jsonify({'error': 'Deal not found'}), 404
            
        return jsonify(deal.to_dict())
    except Exception as e:
        current_app.logger.error(f"Error fetching deal: {str(e)}")
        return jsonify({'error': 'Error fetching deal', 'details': str(e)}), 500

@bp.route('/', methods=['POST'])
@jwt_required()
def create_deal():
    """Create a new deal using schema validation."""
    try:
        # Valida os dados usando o schema
        data = deal_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verifica se o pipeline stage existe (após validação do tipo)
        pipeline_stage = PipelineStage.query.get(data['pipeline_stage_id'])
        if not pipeline_stage:
            # Retorna erro específico se o stage não for encontrado
            return jsonify({'message': 'Pipeline stage inválido', 'errors': {'pipeline_stage_id': ['Estágio do pipeline não encontrado.']}}), 400
        
        # Cria o deal usando os dados validados
        # O método from_dict pode precisar de ajuste se não esperar objetos Date diretamente
        # Mas como DealSchema já converte para Date, vamos tentar direto
        deal = Deal(**data) # Passa dados validados diretamente para o construtor
        
        # Define o usuário que criou o deal
        current_user_id = get_jwt_identity()
        deal.usuario_id = current_user_id
            
        db.session.add(deal)
        db.session.commit()
        
        return jsonify(deal.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar deal: {str(e)}")
        return jsonify({'error': 'Erro ao criar deal', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_deal(id):
    """Update an existing deal using schema validation."""
    deal = Deal.query.get(id)
    if not deal:
        return jsonify({'error': 'Deal not found'}), 404
            
    try:
        # Valida os dados usando o schema de atualização (partial=True)
        data = deal_update_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verifica se o pipeline stage existe, se fornecido
        if 'pipeline_stage_id' in data:
            pipeline_stage = PipelineStage.query.get(data['pipeline_stage_id'])
            if not pipeline_stage:
                 return jsonify({'message': 'Pipeline stage inválido', 'errors': {'pipeline_stage_id': ['Estágio do pipeline não encontrado.']}}), 400
        
        # Atualiza os campos do deal com os dados validados
        for field, value in data.items():
            setattr(deal, field, value)
        
        # Não atualizamos usuario_id aqui, a menos que seja um requisito específico
        
        db.session.commit()
        
        return jsonify(deal.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating deal {id}: {str(e)}")
        return jsonify({'error': 'Error updating deal', 'details': str(e)}), 500

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_deal(id):
    """Delete a deal by ID."""
    try:
        deal = Deal.query.get(id)
        if not deal:
            return jsonify({'error': 'Deal not found'}), 404
            
        db.session.delete(deal)
        db.session.commit()
        
        return jsonify({'message': 'Deal deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting deal: {str(e)}")
        return jsonify({'error': 'Error deleting deal', 'details': str(e)}), 500

@bp.route('/<int:id>/move', methods=['PUT'])
@jwt_required()
def move_deal(id):
    """Move a deal to a different pipeline stage."""
    try:
        deal = Deal.query.get(id)
        if not deal:
            return jsonify({'error': 'Deal not found'}), 404
            
        data = request.get_json() or {}
        
        if not data or 'stageId' not in data:
            return jsonify({'error': 'Pipeline stage ID is required'}), 400
        
        # Verify if the pipeline stage exists
        new_stage_id = data['stageId']
        # Validação do tipo stageId
        if not isinstance(new_stage_id, int):
             return jsonify({'error': 'stageId must be an integer'}), 400
             
        pipeline_stage = PipelineStage.query.get(new_stage_id)
        if not pipeline_stage:
            return jsonify({'error': 'Invalid pipeline stage'}), 400
        
        # Update the deal with the new stage
        deal.pipeline_stage_id = new_stage_id
        db.session.commit()
        
        return jsonify(deal.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error moving deal: {str(e)}")
        return jsonify({'error': 'Error moving deal', 'details': str(e)}), 500

@bp.route('/<int:id>/stage', methods=['PUT'])
@jwt_required()
def update_deal_stage(id):
    """Update a deal's pipeline stage."""
    try:
        deal = Deal.query.get(id)
        if not deal:
            return jsonify({'error': 'Deal not found'}), 404
        
        # Validate data
        data = request.json
        if not data or 'pipeline_stage_id' not in data:
            return jsonify({'error': 'Pipeline stage ID required'}), 400
        
        # Check if the stage exists
        pipeline_stage = PipelineStage.query.get(data['pipeline_stage_id'])
        if not pipeline_stage:
            return jsonify({'error': 'Invalid pipeline stage'}), 400
            
        # Update stage
        deal.pipeline_stage_id = data['pipeline_stage_id']
        
        db.session.commit()
        
        return jsonify(deal.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating deal stage: {str(e)}")
        return jsonify({'error': 'Error updating deal stage', 'details': str(e)}), 500 