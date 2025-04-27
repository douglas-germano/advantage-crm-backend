from flask import request, jsonify, current_app
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
import os

from app import db
from app.models import Communication, User, Document
from . import communications_bp
from .schemas import CommunicationSchema

communication_schema = CommunicationSchema()
communications_schema = CommunicationSchema(many=True)

@communications_bp.route('/', methods=['GET'])
@jwt_required()
def get_communications():
    """Lista todas as comunicações com filtros opcionais"""
    try:
        # Parâmetros de filtro
        comm_type = request.args.get('comm_type')
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')
        user_id = request.args.get('user_id')
        outcome = request.args.get('outcome')
        search = request.args.get('search')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = Communication.query
        
        # Aplicar filtros
        if comm_type:
            query = query.filter(Communication.comm_type == comm_type)
        if entity_type:
            query = query.filter(Communication.entity_type == entity_type)
        if entity_id:
            query = query.filter(Communication.entity_id == entity_id)
        if user_id:
            query = query.filter(Communication.user_id == user_id)
        if outcome:
            query = query.filter(Communication.outcome == outcome)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Communication.subject.ilike(search_term) | 
                Communication.content.ilike(search_term)
            )
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Communication.date_time >= start_date_obj)
            except ValueError:
                current_app.logger.warning(f"Formato de data inicial inválido: {start_date}")
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                # Adicionar 1 dia para incluir todo o último dia
                end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
                query = query.filter(Communication.date_time <= end_date_obj)
            except ValueError:
                current_app.logger.warning(f"Formato de data final inválido: {end_date}")
        
        # Ordenação padrão: comunicações mais recentes primeiro
        query = query.order_by(Communication.date_time.desc())
        
        # Executar a consulta paginada
        paginated_comms = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Preparar a resposta
        return jsonify({
            'communications': [comm.to_dict() for comm in paginated_comms.items],
            'pagination': {
                'total_items': paginated_comms.total,
                'total_pages': paginated_comms.pages,
                'current_page': paginated_comms.page,
                'per_page': paginated_comms.per_page,
                'has_next': paginated_comms.has_next,
                'has_prev': paginated_comms.has_prev
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar comunicações: {str(e)}")
        return jsonify({'error': 'Erro ao listar comunicações', 'details': str(e)}), 500

@communications_bp.route('/', methods=['POST'])
@jwt_required()
def create_communication():
    """Registra uma nova comunicação"""
    try:
        # Tratar dados JSON e formulário com arquivos
        data = request.form.to_dict() if request.form else request.json or {}
        
        # Configurar contexto para validação
        communication_schema.context = {
            'entity_type': data.get('entity_type')
        }
        
        # Validar dados com o schema
        validated_data = communication_schema.load(data)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar se o usuário existe
        if not User.query.get(validated_data.get('user_id')):
            return jsonify({'message': 'Usuário não encontrado'}), 400
            
        # Criar a comunicação
        communication = Communication(
            comm_type=validated_data['comm_type'],
            subject=validated_data.get('subject'),
            content=validated_data.get('content'),
            outcome=validated_data.get('outcome'),
            date_time=validated_data.get('date_time') or datetime.utcnow(),
            duration_minutes=validated_data.get('duration_minutes'),
            entity_type=validated_data.get('entity_type'),
            entity_id=validated_data.get('entity_id'),
            user_id=validated_data.get('user_id') or get_jwt_identity()
        )
        
        db.session.add(communication)
        db.session.flush()  # Obter ID sem commit
        
        # Processar arquivos enviados
        files = request.files.getlist("files") if request.files else []
        uploaded_files = []
        
        for file in files:
            if file and file.filename:
                # Gerar nome único para o arquivo
                ext = os.path.splitext(file.filename)[1]
                unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{communication.id}_{len(uploaded_files)}{ext}"
                
                # Definir o diretório de uploads
                upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'communications')
                
                # Criar o diretório se não existir
                os.makedirs(upload_dir, exist_ok=True)
                
                # Caminho completo do arquivo
                file_path = os.path.join(upload_dir, unique_filename)
                
                # Salvar o arquivo
                file.save(file_path)
                
                # Criar registro do documento
                document = Document(
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    file_type=file.content_type,
                    entity_type='communication',
                    entity_id=communication.id,
                    communication_id=communication.id,
                    uploaded_by=communication.user_id
                )
                
                db.session.add(document)
                uploaded_files.append(document)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Comunicação registrada com sucesso',
            'communication': communication.to_dict(),
            'attachments': [doc.to_dict(include_content=False) for doc in uploaded_files]
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao registrar comunicação: {str(e)}")
        return jsonify({'error': 'Erro ao registrar comunicação', 'details': str(e)}), 500

@communications_bp.route('/<int:comm_id>', methods=['GET'])
@jwt_required()
def get_communication(comm_id):
    """Obtém os detalhes de uma comunicação específica"""
    try:
        communication = Communication.query.get(comm_id)
        if not communication:
            return jsonify({'message': 'Comunicação não encontrada'}), 404
        return jsonify({'communication': communication.to_dict()}), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar comunicação {comm_id}: {str(e)}")
        return jsonify({'error': 'Erro ao buscar comunicação', 'details': str(e)}), 500

@communications_bp.route('/<int:comm_id>', methods=['PUT'])
@jwt_required()
def update_communication(comm_id):
    """Atualiza uma comunicação existente"""
    try:
        communication = Communication.query.get(comm_id)
        if not communication:
            return jsonify({'message': 'Comunicação não encontrada'}), 404
            
        data = request.json or {}
        
        # Configurar contexto para validação
        communication_schema.context = {
            'entity_type': data.get('entity_type', communication.entity_type)
        }
        
        # Validar dados parcialmente
        validated_data = communication_schema.load(data, partial=True)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir edição apenas para admins ou o usuário que registrou
        if user_role != 'admin' and str(communication.user_id) != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Atualizar campos
        for field, value in validated_data.items():
            setattr(communication, field, value)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Comunicação atualizada com sucesso',
            'communication': communication.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar comunicação {comm_id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar comunicação', 'details': str(e)}), 500

@communications_bp.route('/<int:comm_id>', methods=['DELETE'])
@jwt_required()
def delete_communication(comm_id):
    """Remove uma comunicação"""
    try:
        communication = Communication.query.get(comm_id)
        if not communication:
            return jsonify({'message': 'Comunicação não encontrada'}), 404
            
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir exclusão apenas para admins ou o usuário que registrou
        if user_role != 'admin' and str(communication.user_id) != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Salvar lista de documentos para excluir os arquivos físicos após commit
        documents_to_delete = [doc.file_path for doc in communication.attachments]
        
        # Excluir a comunicação (e seus anexos via cascade)
        db.session.delete(communication)
        db.session.commit()
        
        # Excluir arquivos físicos
        for file_path in documents_to_delete:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as file_err:
                current_app.logger.warning(f"Erro ao excluir arquivo {file_path}: {str(file_err)}")
        
        return jsonify({'message': 'Comunicação removida com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao remover comunicação {comm_id}: {str(e)}")
        return jsonify({'error': 'Erro ao remover comunicação', 'details': str(e)}), 500
