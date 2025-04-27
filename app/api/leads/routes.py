"""
Endpoints da API para gerenciamento de leads no sistema CRM.

Este módulo implementa operações CRUD para leads, incluindo listagem paginada,
criação, edição, exclusão e endpoints para obter opções de status e origem.
"""
from flask import jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app import db
from app.api.leads import bp
from app.models import Lead, User
from .schemas import LeadSchema

lead_schema = LeadSchema()
lead_update_schema = LeadSchema(partial=True)


@bp.route('/', methods=['GET'])
@jwt_required()
def get_leads():
    """
    Obtém uma lista paginada de leads com suporte a filtros.
    
    Query parameters:
        page (int): Número da página (padrão: 1)
        per_page (int): Itens por página (padrão: 10, máximo: 100)
        nome (str): Filtra por nome (pesquisa parcial)
        email (str): Filtra por email (pesquisa parcial)
        empresa (str): Filtra por empresa (pesquisa parcial)
        status (str): Filtra por status (correspondência exata)
        origem (str): Filtra por origem (correspondência exata)
        
    Returns:
        JSON com leads paginados e metadados da paginação
    """
    try:
        # Obter identificação do usuário a partir do token JWT
        current_user_id = get_jwt_identity()
        current_app.logger.info(f"Token validado com sucesso. ID do usuário: {current_user_id}")
        
        # Configurar parâmetros de paginação com validação
        try:
            page = request.args.get('page', 1, type=int)
            # Limita o número máximo de itens por página para prevenir sobrecarga
            per_page = min(request.args.get('per_page', 10, type=int), 100)
            current_app.logger.info(f"Parâmetros de paginação: page={page}, per_page={per_page}")
        except Exception as e:
            current_app.logger.error(f"Erro ao processar parâmetros de paginação: {str(e)}")
            # Valores padrão caso ocorra erro na validação
            page = 1
            per_page = 10
        
        # Iniciar consulta base
        query = Lead.query
        
        # Aplicar filtros dinâmicos com base nos parâmetros da requisição
        current_app.logger.info(f"Request args: {request.args}")
        
        # Aplicar filtros de pesquisa parcial (usando LIKE)
        for filter_name, model_field in [
            ('nome', Lead.nome),
            ('email', Lead.email),
            ('empresa', Lead.empresa)
        ]:
            if request.args.get(filter_name):
                filter_value = f"%{request.args.get(filter_name)}%"
                query = query.filter(model_field.ilike(filter_value))
                current_app.logger.info(f"Filtrando por {filter_name}: {filter_value}")
        
        # Aplicar filtros de correspondência exata
        for filter_name, model_field in [
            ('status', Lead.status),
            ('origem', Lead.origem)
        ]:
            if request.args.get(filter_name):
                filter_value = request.args.get(filter_name)
                query = query.filter(model_field == filter_value)
                current_app.logger.info(f"Filtrando por {filter_name}: {filter_value}")
        
        # Ordenação padrão por data de criação (mais recentes primeiro)
        query = query.order_by(Lead.criado_em.desc())
        
        # Contagem total para diagnóstico e informações de paginação
        leads_count = query.count()
        current_app.logger.info(f"Total de leads encontrados após aplicar filtros: {leads_count}")
        
        # Aplicar paginação à consulta
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        leads = pagination.items
        current_app.logger.info(f"Paginação bem-sucedida. {len(leads)} leads na página {page}")
        
        # Construir resposta com manipulação segura de cada lead
        lead_list = []
        for lead in leads:
            try:
                # Estrutura simplificada e otimizada para listagem
                lead_dict = {
                    'id': lead.id,
                    'nome': lead.nome,
                    'email': lead.email,
                    'telefone': lead.telefone,
                    'empresa': lead.empresa,
                    'cargo': lead.cargo,
                    'status': lead.status,
                    'origem': lead.origem,
                    'criado_em': lead.criado_em.isoformat() if lead.criado_em else None
                }
                lead_list.append(lead_dict)
            except Exception as e:
                current_app.logger.error(f"Erro ao processar lead {lead.id}: {str(e)}")
        
        # Estrutura de resposta com metadados de paginação
        result = {
            'items': lead_list,
            'total': pagination.total,
            'pages': pagination.pages,
            'page': page,
            'per_page': per_page
        }
        
        current_app.logger.info("Resposta preparada com sucesso")
        return jsonify(result)
            
    except Exception as e:
        current_app.logger.error(f"Erro global ao listar leads: {str(e)}")
        return jsonify({
            'error': 'Erro ao listar leads', 
            'details': str(e)
        }), 500


@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_lead(id):
    """
    Obtém um lead específico pelo ID.
    
    Args:
        id (int): ID do lead a ser obtido
        
    Returns:
        JSON com os dados do lead ou mensagem de erro
    """
    try:
        # Busca o lead pelo ID
        lead = Lead.query.get(id)
        if not lead:
            return jsonify({'error': 'Lead não encontrado'}), 404
            
        # Retorna a representação completa do lead
        return jsonify(lead.to_dict())
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar lead: {str(e)}")
        return jsonify({'error': 'Erro ao buscar lead', 'details': str(e)}), 500


@bp.route('/', methods=['POST'])
@jwt_required()
def create_lead():
    """Cria um novo lead com validação de schema."""
    try:
        # Valida os dados usando o schema
        data = lead_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Cria o lead usando os dados validados
        lead = Lead(**data)
        
        # Associa ao usuário atual
        current_user_id = get_jwt_identity()
        lead.usuario_id = current_user_id
            
        db.session.add(lead)
        db.session.commit()
        
        return jsonify(lead.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar lead: {str(e)}")
        return jsonify({'error': 'Erro ao criar lead', 'details': str(e)}), 500


@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_lead(id):
    """Atualiza um lead existente com validação de schema."""
    lead = Lead.query.get(id)
    if not lead:
        return jsonify({'error': 'Lead não encontrado'}), 404
            
    try:
        # Valida os dados usando o schema de atualização (partial=True)
        data = lead_update_schema.load(request.json or {})
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Atualiza os campos do lead com os dados validados
        for field, value in data.items():
            setattr(lead, field, value)
        
        db.session.commit()
        return jsonify(lead.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar lead {id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar lead', 'details': str(e)}), 500


@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_lead(id):
    """
    Exclui um lead pelo ID.
    
    Args:
        id (int): ID do lead a ser excluído
        
    Returns:
        Mensagem de sucesso ou erro
    """
    try:
        # Buscar lead pelo ID
        lead = Lead.query.get(id)
        if not lead:
            return jsonify({'error': 'Lead não encontrado'}), 404
            
        # Excluir lead
        db.session.delete(lead)
        db.session.commit()
        
        return jsonify({'message': 'Lead excluído com sucesso'})
    except Exception as e:
        # Rollback em caso de erro
        db.session.rollback()
        current_app.logger.error(f"Erro ao excluir lead: {str(e)}")
        return jsonify({'error': 'Erro ao excluir lead', 'details': str(e)}), 500


@bp.route('/status', methods=['GET'])
@jwt_required()
def get_lead_status_options():
    """
    Obtém as opções de status disponíveis para leads.
    
    Returns:
        JSON com lista de opções de status (value/label)
    """
    status_options = [
        {'value': 'novo', 'label': 'Novo'},
        {'value': 'contatado', 'label': 'Contatado'},
        {'value': 'qualificado', 'label': 'Qualificado'},
        {'value': 'negociacao', 'label': 'Em Negociação'},
        {'value': 'ganho', 'label': 'Ganho'},
        {'value': 'perdido', 'label': 'Perdido'}
    ]
    
    return jsonify(status_options)


@bp.route('/origem', methods=['GET'])
@jwt_required()
def get_lead_origem_options():
    """
    Obtém as opções de origem disponíveis para leads.
    
    Returns:
        JSON com lista de opções de origem (value/label)
    """
    origem_options = [
        {'value': 'site', 'label': 'Site'},
        {'value': 'indicacao', 'label': 'Indicação'},
        {'value': 'email_marketing', 'label': 'Email Marketing'},
        {'value': 'redes_sociais', 'label': 'Redes Sociais'},
        {'value': 'evento', 'label': 'Evento'},
        {'value': 'outros', 'label': 'Outros'}
    ]
    
    return jsonify(origem_options)
