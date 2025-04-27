from flask import request, jsonify, current_app, send_file
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import os
import uuid
from datetime import datetime
import mimetypes
from werkzeug.utils import secure_filename

from app import db
from app.models import Document, User
from . import documents_bp
from .schemas import DocumentSchema

document_schema = DocumentSchema()
documents_schema = DocumentSchema(many=True)

@documents_bp.route('/', methods=['GET'])
@jwt_required()
def get_documents():
    """Lista todos os documentos com filtros opcionais"""
    try:
        # Parâmetros de filtro
        entity_type = request.args.get('entity_type')
        entity_id = request.args.get('entity_id')
        communication_id = request.args.get('communication_id')
        is_public = request.args.get('is_public')
        file_type = request.args.get('file_type')
        uploaded_by = request.args.get('uploaded_by')
        search = request.args.get('search')
        
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        query = Document.query
        
        # Aplicar filtros
        if entity_type:
            query = query.filter(Document.entity_type == entity_type)
        if entity_id:
            query = query.filter(Document.entity_id == entity_id)
        if communication_id:
            query = query.filter(Document.communication_id == communication_id)
        if is_public is not None:
            is_public_bool = is_public.lower() == 'true'
            query = query.filter(Document.is_public == is_public_bool)
        if file_type:
            query = query.filter(Document.file_type.ilike(f'%{file_type}%'))
        if uploaded_by:
            query = query.filter(Document.uploaded_by == uploaded_by)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Document.title.ilike(search_term) | 
                Document.description.ilike(search_term) |
                Document.original_filename.ilike(search_term)
            )
        
        # Ordenação padrão: documentos mais recentes primeiro
        query = query.order_by(Document.created_at.desc())
        
        # Executar a consulta paginada
        paginated_docs = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Preparar a resposta
        return jsonify({
            'documents': [doc.to_dict(include_content=False) for doc in paginated_docs.items],
            'pagination': {
                'total_items': paginated_docs.total,
                'total_pages': paginated_docs.pages,
                'current_page': paginated_docs.page,
                'per_page': paginated_docs.per_page,
                'has_next': paginated_docs.has_next,
                'has_prev': paginated_docs.has_prev
            }
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao listar documentos: {str(e)}")
        return jsonify({'error': 'Erro ao listar documentos', 'details': str(e)}), 500

@documents_bp.route('/', methods=['POST'])
@jwt_required()
def upload_document():
    """Faz upload de um novo documento"""
    try:
        # Verificar se pelo menos um arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({'message': 'Nenhum arquivo enviado'}), 400
            
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'message': 'Arquivo inválido'}), 400
            
        # Obter dados do formulário
        data = request.form.to_dict()
        
        # Configurar contexto para validação
        document_schema.context = {
            'entity_type': data.get('entity_type')
        }
        
        # Validar dados com o schema
        validated_data = document_schema.load(data, partial=True)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Obter o usuário atual
        current_user_id = get_jwt_identity()
        
        # Gerar nome de arquivo único
        original_filename = secure_filename(file.filename)
        extension = os.path.splitext(original_filename)[1]
        unique_id = str(uuid.uuid4())
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{unique_id}{extension}"
        
        # Verificar se deve usar Supabase Storage
        use_supabase = data.get('use_supabase', 'false').lower() == 'true'
        
        # Definir diretório de uploads local
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'documents')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Caminho completo do arquivo local (sempre salvar local primeiro)
        file_path = os.path.join(upload_dir, filename)
        
        # Salvar o arquivo localmente
        file.save(file_path)
        
        # Determinar o tipo MIME se não for fornecido pelo cliente
        file_type = file.content_type
        if not file_type:
            file_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        
        # Obter tamanho do arquivo
        file_size = os.path.getsize(file_path)
        
        # Criar documento no banco de dados
        document = Document(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            title=validated_data.get('title') or original_filename,
            description=validated_data.get('description'),
            entity_type=validated_data.get('entity_type'),
            entity_id=validated_data.get('entity_id'),
            communication_id=validated_data.get('communication_id'),
            uploaded_by=current_user_id,
            is_public=validated_data.get('is_public', False),
            access_code=validated_data.get('access_code'),
            use_supabase=use_supabase
        )
        
        db.session.add(document)
        db.session.flush()  # Obter ID sem commit
        
        # Se for usar Supabase Storage, fazer upload do arquivo
        supabase_success = False
        if use_supabase:
            bucket_name = data.get('bucket_name', 'documents')
            supabase_success = document.upload_to_supabase(bucket_name)
            
            if not supabase_success:
                current_app.logger.warning(f"Falha ao fazer upload para o Supabase. Usando armazenamento local para o documento {document.id}")
                document.use_supabase = False
        
        db.session.commit()
        
        response_data = {
            'message': 'Documento enviado com sucesso',
            'document': document.to_dict(include_content=False)
        }
        
        if use_supabase:
            if supabase_success:
                response_data['storage'] = 'supabase'
                response_data['public_url'] = document.get_supabase_url()
            else:
                response_data['storage'] = 'local'
                response_data['warning'] = 'Falha ao fazer upload para o Supabase. Usando armazenamento local.'                
        
        return jsonify(response_data), 201
    except Exception as e:
        # Se ocorrer um erro, excluir o arquivo se ele foi criado
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        db.session.rollback()
        current_app.logger.error(f"Erro ao enviar documento: {str(e)}")
        return jsonify({'error': 'Erro ao enviar documento', 'details': str(e)}), 500

@documents_bp.route('/<int:document_id>', methods=['GET'])
@jwt_required(optional=True)
def get_document(document_id):
    """Obtém os detalhes de um documento específico"""
    try:
        document = Document.query.get(document_id)
        if not document:
            return jsonify({'message': 'Documento não encontrado'}), 404
            
        # Verificar permissões para documentos não públicos
        if not document.is_public:
            current_user_id = get_jwt_identity()
            
            # Se não está autenticado e o documento não é público
            if not current_user_id:
                # Verificar se foi fornecido um código de acesso válido
                access_code = request.args.get('access_code')
                if not access_code or access_code != document.access_code:
                    return jsonify({'message': 'Acesso negado. Este documento não é público.'}), 403
        
        # Opcionalmente incluir conteúdo para arquivos de texto pequenos
        include_content = request.args.get('include_content', 'false').lower() == 'true'
        max_size = 1024 * 100  # Limitar a 100KB para incluir conteúdo
        
        if include_content and document.file_size > max_size:
            include_content = False
        
        return jsonify({
            'document': document.to_dict(include_content=include_content)
        }), 200
    except Exception as e:
        current_app.logger.error(f"Erro ao buscar documento {document_id}: {str(e)}")
        return jsonify({'error': 'Erro ao buscar documento', 'details': str(e)}), 500

@documents_bp.route('/<int:document_id>/download', methods=['GET'])
@jwt_required(optional=True)
def download_document(document_id):
    """Baixa um documento"""
    try:
        document = Document.query.get(document_id)
        if not document:
            return jsonify({'message': 'Documento não encontrado'}), 404
        
        # Verificar permissões para documentos não públicos
        if not document.is_public:
            current_user_id = get_jwt_identity()
            
            # Se não está autenticado e o documento não é público
            if not current_user_id:
                # Verificar se foi fornecido um código de acesso válido
                access_code = request.args.get('access_code')
                if not access_code or access_code != document.access_code:
                    return jsonify({'message': 'Acesso negado. Este documento não é público.'}), 403
        
        # Se estiver usando Supabase e quiser redirecionar para URL pública
        redirect_to_supabase = request.args.get('redirect', 'false').lower() == 'true'
        if document.use_supabase and redirect_to_supabase:
            public_url = document.get_supabase_url()
            if public_url:
                return redirect(public_url)
        
        # Obter o conteúdo do arquivo
        content = document.get_content()
        if not content:
            # Se não foi possível obter o conteúdo, verificar se o arquivo existe localmente
            if not os.path.exists(document.file_path):
                return jsonify({'message': 'Arquivo não encontrado no servidor'}), 404
            else:
                # Se existe localmente, tentar enviar diretamente
                return send_file(
                    document.file_path,
                    mimetype=document.file_type,
                    as_attachment=True,
                    download_name=document.original_filename
                )
        
        # Criar um arquivo temporário para servir o conteúdo
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(content)
            temp_filename = temp.name
        
        # Enviar o arquivo temporário
        return send_file(
            temp_filename,
            mimetype=document.file_type,
            as_attachment=True,
            download_name=document.original_filename
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao baixar documento {document_id}: {str(e)}")
        return jsonify({'error': 'Erro ao baixar documento', 'details': str(e)}), 500

@documents_bp.route('/migrate-to-supabase', methods=['POST'])
@jwt_required()
def migrate_documents_to_supabase():
    """Migra documentos existentes do armazenamento local para o Supabase"""
    try:
        # Verificar permissões (apenas admin)
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        if user_role != 'admin':
            return jsonify({'message': 'Permissão negada. Apenas administradores podem executar essa operação.'}), 403
        
        # Obter parâmetros
        data = request.json or {}
        document_ids = data.get('document_ids', [])
        bucket_name = data.get('bucket_name', 'documents')
        delete_local = data.get('delete_local', False)
        
        # Se nenhum ID foi especificado, obter todos os documentos que não usam Supabase
        if not document_ids:
            query = Document.query.filter_by(use_supabase=False)
            # Limit opcional para evitar migração de muitos documentos de uma vez
            limit = data.get('limit')
            if limit:
                query = query.limit(int(limit))
            documents = query.all()
        else:
            # Buscar documentos específicos
            documents = Document.query.filter(Document.id.in_(document_ids)).all()
        
        if not documents:
            return jsonify({
                'message': 'Nenhum documento encontrado para migração',
                'migrated': 0,
                'failed': 0
            }), 200
        
        # Resultados da migração
        results = {
            'migrated': 0,
            'failed': 0,
            'details': []
        }
        
        # Migrar cada documento
        for document in documents:
            # Pular documentos que já usam Supabase
            if document.use_supabase:
                results['details'].append({
                    'id': document.id,
                    'status': 'skipped',
                    'message': 'Documento já está no Supabase'
                })
                continue
                
            # Verificar se o arquivo existe localmente
            if not os.path.exists(document.file_path):
                results['failed'] += 1
                results['details'].append({
                    'id': document.id,
                    'status': 'failed',
                    'message': 'Arquivo local não encontrado'
                })
                continue
                
            # Tentar fazer upload para o Supabase
            success = document.upload_to_supabase(bucket_name)
            
            if success:
                results['migrated'] += 1
                results['details'].append({
                    'id': document.id,
                    'status': 'success',
                    'message': 'Migrado com sucesso',
                    'storage_path': document.storage_path,
                    'public_url': document.get_supabase_url()
                })
                
                # Se solicitado, excluir o arquivo local após migração bem-sucedida
                if delete_local and os.path.exists(document.file_path):
                    try:
                        os.remove(document.file_path)
                    except Exception as e:
                        current_app.logger.warning(f"Erro ao excluir arquivo local {document.file_path}: {str(e)}")
            else:
                results['failed'] += 1
                results['details'].append({
                    'id': document.id,
                    'status': 'failed',
                    'message': 'Falha ao fazer upload para o Supabase'
                })
        
        # Salvar as alterações no banco de dados
        db.session.commit()
        
        return jsonify({
            'message': f'Migração concluída. {results["migrated"]} documentos migrados, {results["failed"]} falhas.',
            'results': results
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao migrar documentos para o Supabase: {str(e)}")
        return jsonify({'error': 'Erro ao migrar documentos', 'details': str(e)}), 500
@jwt_required()
def update_document(document_id):
    """Atualiza os metadados de um documento"""
    try:
        document = Document.query.get(document_id)
        if not document:
            return jsonify({'message': 'Documento não encontrado'}), 404
            
        data = request.json or {}
        
        # Configurar contexto para validação
        document_schema.context = {
            'entity_type': data.get('entity_type', document.entity_type)
        }
        
        # Validar dados parcialmente
        validated_data = document_schema.load(data, partial=True)
    except ValidationError as err:
        return jsonify({'message': 'Erro de validação', 'errors': err.messages}), 400

    try:
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir edição apenas para admins ou o usuário que fez upload
        if user_role != 'admin' and str(document.uploaded_by) != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Atualizar apenas os campos editáveis
        if 'title' in validated_data:
            document.title = validated_data['title']
        if 'description' in validated_data:
            document.description = validated_data['description']
        if 'entity_type' in validated_data:
            document.entity_type = validated_data['entity_type']
        if 'entity_id' in validated_data:
            document.entity_id = validated_data['entity_id']
        if 'is_public' in validated_data:
            document.is_public = validated_data['is_public']
        if 'access_code' in validated_data:
            document.access_code = validated_data['access_code']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Documento atualizado com sucesso',
            'document': document.to_dict(include_content=False)
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao atualizar documento {document_id}: {str(e)}")
        return jsonify({'error': 'Erro ao atualizar documento', 'details': str(e)}), 500

@documents_bp.route('/<int:document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(document_id):
    """Remove um documento"""
    try:
        document = Document.query.get(document_id)
        if not document:
            return jsonify({'message': 'Documento não encontrado'}), 404
            
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir exclusão apenas para admins ou o usuário que fez upload
        if user_role != 'admin' and str(document.uploaded_by) != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Salvar o caminho do arquivo para excluí-lo após commit
        file_path = document.file_path
        
        # Excluir o documento do banco de dados
        db.session.delete(document)
        db.session.commit()
        
        # Excluir o arquivo físico
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as file_err:
                current_app.logger.warning(f"Erro ao excluir arquivo {file_path}: {str(file_err)}")
        
        return jsonify({'message': 'Documento removido com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao remover documento {document_id}: {str(e)}")
        return jsonify({'error': 'Erro ao remover documento', 'details': str(e)}), 500

@documents_bp.route('/share/<int:document_id>', methods=['POST'])
@jwt_required()
def share_document(document_id):
    """Gera um código de acesso para compartilhar um documento"""
    try:
        document = Document.query.get(document_id)
        if not document:
            return jsonify({'message': 'Documento não encontrado'}), 404
            
        # Verificar permissões
        jwt_data = get_jwt()
        user_role = jwt_data.get('role', '')
        current_user_id = get_jwt_identity()
        
        # Permitir compartilhamento apenas para admins ou o usuário que fez upload
        if user_role != 'admin' and str(document.uploaded_by) != current_user_id:
            return jsonify({'message': 'Permissão negada'}), 403
            
        # Dados do compartilhamento (opcional)
        data = request.json or {}
        is_public = data.get('is_public', False)
        
        # Gerar código de acesso se não for público
        access_code = None
        if not is_public:
            # Usar o código existente ou gerar um novo
            access_code = document.access_code or str(uuid.uuid4())[:8].upper()
            document.access_code = access_code
        
        # Atualizar visibilidade
        document.is_public = is_public
        db.session.commit()
        
        # Construir URL de compartilhamento
        base_url = current_app.config.get('BASE_URL', request.host_url.rstrip('/'))
        share_url = f"{base_url}/api/documents/{document.id}/download"
        
        if access_code:
            share_url += f"?access_code={access_code}"
        
        return jsonify({
            'message': 'Documento configurado para compartilhamento',
            'document': document.to_dict(include_content=False),
            'is_public': is_public,
            'access_code': access_code,
            'share_url': share_url
        }), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao compartilhar documento {document_id}: {str(e)}")
        return jsonify({'error': 'Erro ao compartilhar documento', 'details': str(e)}), 500
