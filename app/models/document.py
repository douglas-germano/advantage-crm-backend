from datetime import datetime
import os
from app import db
from app.utils.supabase_client import SupabaseManager
import base64
import uuid

class Document(db.Model):
    """Modelo para documentos e arquivos anexados no CRM"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Tamanho em bytes
    file_type = db.Column(db.String(100))  # MIME type
    
    # Metadados
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    
    # Entidade relacionada (polimórfica)
    entity_type = db.Column(db.String(50))  # customer, lead, deal, task
    entity_id = db.Column(db.Integer)
    
    # Relacionamento com comunicação (se aplicável)
    communication_id = db.Column(db.Integer, db.ForeignKey('communications.id'))
    
    # Usuário que fez o upload
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploader = db.relationship('User', backref='uploaded_documents')
    
    # Metadados de acesso
    is_public = db.Column(db.Boolean, default=False)  # Se pode ser acessado sem autenticação
    access_code = db.Column(db.String(20))  # Para compartilhamento com acesso limitado
    
    # Campos para Supabase Storage
    storage_bucket = db.Column(db.String(100))  # Nome do bucket no Supabase
    storage_path = db.Column(db.String(500))    # Caminho do arquivo no Supabase
    use_supabase = db.Column(db.Boolean, default=False)  # Se está usando Supabase Storage
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, filename, original_filename, file_path, file_size=None, file_type=None,
                 title=None, description=None, entity_type=None, entity_id=None,
                 communication_id=None, uploaded_by=None, is_public=False, access_code=None,
                 use_supabase=False, storage_bucket=None, storage_path=None):
        self.filename = filename
        self.original_filename = original_filename
        self.file_path = file_path
        self.file_size = file_size
        self.file_type = file_type
        self.title = title or original_filename
        self.description = description
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.communication_id = communication_id
        self.uploaded_by = uploaded_by
        self.is_public = is_public
        self.access_code = access_code
        self.use_supabase = use_supabase
        self.storage_bucket = storage_bucket
        self.storage_path = storage_path
    
    @property
    def extension(self):
        """Retorna a extensão do arquivo"""
        _, ext = os.path.splitext(self.original_filename)
        return ext.lower() if ext else ''
    
    @property
    def is_image(self):
        """Verifica se o arquivo é uma imagem"""
        image_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return self.extension in image_types
    
    @property
    def is_document(self):
        """Verifica se o arquivo é um documento office/pdf"""
        doc_types = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
        return self.extension in doc_types
    
    def upload_to_supabase(self, bucket_name='documents'):
        """Faz upload do arquivo para o armazenamento do Supabase"""
        if not os.path.exists(self.file_path):
            return False
            
        try:
            # Gerar um caminho único para o arquivo no Supabase
            uid = str(uuid.uuid4())
            storage_path = f"{self.entity_type}/{self.entity_id or 'general'}/{uid}{self.extension}"
            
            # Obter o cliente Supabase
            supabase_manager = SupabaseManager()
            
            # Fazer upload do arquivo
            result = supabase_manager.upload_file(self.file_path, storage_path, bucket_name)
            
            if result:
                # Atualizar os campos do documento
                self.use_supabase = True
                self.storage_bucket = bucket_name
                self.storage_path = storage_path
                return True
            return False
        except Exception as e:
            return False
    
    def get_supabase_url(self):
        """Obtém a URL pública do arquivo no Supabase"""
        if not self.use_supabase or not self.storage_bucket or not self.storage_path:
            return None
            
        try:
            supabase_manager = SupabaseManager()
            return supabase_manager.get_public_url(self.storage_path, self.storage_bucket)
        except Exception:
            return None
    
    def get_content(self):
        """Obtém o conteúdo do arquivo"""
        # Se o arquivo estiver no Supabase
        if self.use_supabase and self.storage_bucket and self.storage_path:
            try:
                supabase_manager = SupabaseManager()
                content = supabase_manager.download_file(self.storage_path, self.storage_bucket)
                if content:
                    return content
            except Exception:
                pass
        
        # Se não estiver no Supabase ou falhar ao obter, tenta localmente
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'rb') as f:
                    return f.read()
            except Exception:
                pass
                
        return None
    
    def to_dict(self, include_content=False):
        """Retorna uma representação em dicionário do documento"""
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'extension': self.extension,
            'title': self.title,
            'description': self.description,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'communication_id': self.communication_id,
            'uploaded_by': self.uploaded_by,
            'uploader_name': self.uploader.name if self.uploader else None,
            'is_public': self.is_public,
            'is_image': self.is_image,
            'is_document': self.is_document,
            'use_supabase': self.use_supabase,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Adicionar URL pública se estiver no Supabase
        if self.use_supabase:
            data['public_url'] = self.get_supabase_url()
        
        # Opcionalmente, incluir o conteúdo do arquivo (para documentos pequenos)
        if include_content and self.file_size and self.file_size < 1024 * 1024:  # < 1MB
            content = self.get_content()
            if content:
                data['content'] = base64.b64encode(content).decode('utf-8')
            else:
                data['error'] = "Não foi possível ler o conteúdo do arquivo"
        
        return data
    
    def __repr__(self):
        return f'<Document {self.id}: {self.original_filename}>'
