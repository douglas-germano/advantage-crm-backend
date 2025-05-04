"""
Utilitário para interagir diretamente com a API do Supabase.
Este módulo fornece acesso a funcionalidades específicas do Supabase que vão além 
do que o SQLAlchemy oferece, como armazenamento (Storage), autenticação (Auth), etc.
Utiliza o padrão Singleton para garantir uma única instância do cliente Supabase.
"""

import os
from supabase import create_client, Client
from flask import current_app # Usado para logging dentro do contexto Flask
import logging

# Configura um logger específico para este módulo
logger = logging.getLogger(__name__)

class SupabaseManager:
    # Gerencia a conexão e interação com a API do Supabase usando o padrão Singleton.
    _instance = None # Armazena a única instância da classe
    _client = None # Armazena o cliente Supabase inicializado
    
    def __new__(cls):
        # Implementa o padrão Singleton.
        # Se a instância ainda não existe (_instance is None), cria uma nova.
        # Caso contrário, retorna a instância já existente.
        if cls._instance is None:
            cls._instance = super(SupabaseManager, cls).__new__(cls)
            # Inicializa o cliente Supabase na primeira vez que a instância é criada.
            cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        # Método privado para inicializar o cliente Supabase.
        # Lê as credenciais (URL e Key) das variáveis de ambiente.
        try:
            url = os.environ.get('SUPABASE_URL')
            key = os.environ.get('SUPABASE_KEY')
            
            # Verifica se as credenciais foram encontradas.
            if not url or not key:
                logger.warning(
                    "Credenciais do Supabase (SUPABASE_URL, SUPABASE_KEY) não encontradas no ambiente. "
                    "Funcionalidades do Supabase podem não funcionar."
                )
                self._client = None # Define o cliente como None se as credenciais estiverem ausentes
                return
                
            # Cria o cliente Supabase usando as credenciais.
            self._client = create_client(url, key)
            logger.info("Cliente Supabase inicializado com sucesso.")
        except Exception as e:
            # Captura e loga qualquer erro durante a inicialização.
            logger.error(f"Erro fatal ao inicializar o cliente Supabase: {str(e)}", exc_info=True)
            self._client = None # Define o cliente como None em caso de erro
    
    @property
    def client(self) -> Client | None:
        # Propriedade para acessar o cliente Supabase inicializado.
        # Garante que a inicialização seja tentada novamente se falhou anteriormente.
        # Retorna o objeto Client do Supabase ou None se a inicialização falhou.
        if self._client is None:
            logger.warning("Tentando acessar cliente Supabase não inicializado. Tentando inicializar novamente...")
            self._initialize_client()
        return self._client
    
    def get_storage(self, bucket_name='documents'):
        # Retorna um objeto para interagir com um bucket específico do Supabase Storage.
        # Args:
        #     bucket_name (str): Nome do bucket (padrão: 'documents').
        # Returns:
        #     Supabase StorageBucket object ou None se o cliente não estiver inicializado.
        if not self.client: # Usa a propriedade client para garantir a inicialização
            logger.error(f"Não foi possível obter o storage do Supabase: cliente não inicializado.")
            return None
        try:
            return self.client.storage.from_(bucket_name)
        except Exception as e:
            logger.error(f"Erro ao acessar o bucket '{bucket_name}' do Supabase Storage: {e}", exc_info=True)
            return None

    def upload_file(self, file_path, destination_path, bucket_name='documents', file_options=None):
        # Faz upload de um arquivo local para o Supabase Storage.
        # 
        # Args:
        #     file_path (str): Caminho completo do arquivo local a ser enviado.
        #     destination_path (str): Caminho/nome do arquivo como será salvo no bucket.
        #     bucket_name (str): Nome do bucket de destino (padrão: 'documents').
        #     file_options (dict, optional): Opções adicionais para o upload (ex: {'cacheControl': '3600', 'upsert': False}).
        # 
        # Returns:
        #     dict: Resposta da API do Supabase em caso de sucesso, ou None em caso de erro.
        storage = self.get_storage(bucket_name)
        if not storage:
            return None # Erro já logado em get_storage
            
        if not os.path.exists(file_path):
            logger.error(f"Arquivo local não encontrado para upload: {file_path}")
            return None

        try:
            with open(file_path, 'rb') as f:
                # O método upload espera o conteúdo do arquivo em bytes
                response = storage.upload(destination_path, f, file_options=file_options)
            logger.info(f"Upload para Supabase concluído: {destination_path} no bucket {bucket_name}")
            # A resposta da API geralmente contém informações úteis, mas pode variar.
            # Retornamos a resposta bruta para o chamador decidir como usar.
            return response
        except Exception as e:
            logger.error(f"Erro durante o upload do arquivo '{file_path}' para '{destination_path}' no Supabase: {str(e)}", exc_info=True)
            return None
    
    def download_file(self, file_path, bucket_name='documents') -> bytes | None:
        # Baixa um arquivo do Supabase Storage.
        # 
        # Args:
        #     file_path (str): Caminho/nome do arquivo no bucket.
        #     bucket_name (str): Nome do bucket (padrão: 'documents').
        # 
        # Returns:
        #     bytes: O conteúdo binário do arquivo baixado, ou None em caso de erro.
        storage = self.get_storage(bucket_name)
        if not storage:
            return None
            
        try:
            # O método download retorna o conteúdo do arquivo como bytes.
            content = storage.download(file_path)
            logger.info(f"Download do Supabase concluído: {file_path} do bucket {bucket_name}")
            return content
        except Exception as e:
            # A exceção pode ser específica do Supabase (ex: FileNotFoundError) ou geral.
            logger.error(f"Erro ao baixar o arquivo '{file_path}' do Supabase: {str(e)}", exc_info=True)
            return None
    
    def get_public_url(self, file_path, bucket_name='documents') -> str | None:
        # Obtém a URL pública de um arquivo no Supabase Storage.
        # Nota: O bucket deve estar configurado como público no Supabase para que esta URL funcione sem autenticação.
        # 
        # Args:
        #     file_path (str): Caminho/nome do arquivo no bucket.
        #     bucket_name (str): Nome do bucket (padrão: 'documents').
        # 
        # Returns:
        #     str: A URL pública completa do arquivo, ou None em caso de erro.
        storage = self.get_storage(bucket_name)
        if not storage:
            return None
            
        try:
            # Gera a URL pública baseada no caminho do arquivo.
            public_url = storage.get_public_url(file_path)
            logger.debug(f"URL pública obtida para {file_path}: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"Erro ao obter URL pública para '{file_path}': {str(e)}", exc_info=True)
            return None

# Função auxiliar para simplificar a obtenção da instância do cliente Supabase
def get_supabase_client() -> Client | None:
    # Retorna a instância do cliente Supabase gerenciada pelo Singleton.
    # Pode retornar None se a inicialização falhou.
    manager = SupabaseManager()
    return manager.client
