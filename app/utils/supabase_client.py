"""
Utilitário para interagir diretamente com a API do Supabase.
Este módulo fornece acesso a funcionalidades específicas do Supabase que vão além 
do que o SQLAlchemy oferece, como armazenamento, autenticação, etc.
"""

import os
from supabase import create_client, Client
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class SupabaseManager:
    """Gerencia a interação com a API do Supabase"""
    _instance = None
    _client = None
    
    def __new__(cls):
        """Implementação de Singleton para garantir apenas uma instância"""
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        """Inicializa o cliente Supabase com as credenciais do .env"""
        try:
            url = os.environ.get('SUPABASE_URL')
            key = os.environ.get('SUPABASE_KEY')
            
            if not url or not key:
                logger.warning(
                    "Credenciais do Supabase não encontradas. "
                    "Defina SUPABASE_URL e SUPABASE_KEY no arquivo .env"
                )
                self._client = None
                return
                
            self._client = create_client(url, key)
            logger.info("Cliente Supabase inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar o cliente Supabase: {str(e)}")
            self._client = None
    
    @property
    def client(self) -> Client:
        """Retorna o cliente Supabase"""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def get_storage(self, bucket_name='documents'):
        """Acessa o bucket de armazenamento do Supabase"""
        if not self._client:
            return None
        return self._client.storage.from_(bucket_name)
    
    def upload_file(self, file_path, destination_path, bucket_name='documents'):
        """
        Faz upload de um arquivo para o armazenamento do Supabase
        
        Args:
            file_path: Caminho local do arquivo
            destination_path: Caminho de destino no bucket
            bucket_name: Nome do bucket (padrão: documents)
            
        Returns:
            dict: resposta do Supabase ou None em caso de erro
        """
        try:
            storage = self.get_storage(bucket_name)
            if not storage:
                return None
                
            with open(file_path, 'rb') as f:
                file_content = f.read()
                
            return storage.upload(destination_path, file_content)
        except Exception as e:
            logger.error(f"Erro ao fazer upload do arquivo para o Supabase: {str(e)}")
            return None
    
    def download_file(self, file_path, bucket_name='documents'):
        """
        Baixa um arquivo do armazenamento do Supabase
        
        Args:
            file_path: Caminho do arquivo no bucket
            bucket_name: Nome do bucket (padrão: documents)
            
        Returns:
            bytes: conteúdo do arquivo ou None em caso de erro
        """
        try:
            storage = self.get_storage(bucket_name)
            if not storage:
                return None
                
            return storage.download(file_path)
        except Exception as e:
            logger.error(f"Erro ao baixar arquivo do Supabase: {str(e)}")
            return None
    
    def get_public_url(self, file_path, bucket_name='documents'):
        """
        Obtém a URL pública de um arquivo no armazenamento do Supabase
        
        Args:
            file_path: Caminho do arquivo no bucket
            bucket_name: Nome do bucket (padrão: documents)
            
        Returns:
            str: URL pública do arquivo ou None em caso de erro
        """
        try:
            storage = self.get_storage(bucket_name)
            if not storage:
                return None
                
            return storage.get_public_url(file_path)
        except Exception as e:
            logger.error(f"Erro ao obter URL pública do arquivo: {str(e)}")
            return None

# Função auxiliar para obter uma instância do gerenciador
def get_supabase_client():
    """Retorna uma instância do cliente Supabase"""
    return SupabaseManager().client
