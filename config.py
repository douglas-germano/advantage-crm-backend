"""
Arquivo de configuração da aplicação Flask.
Define diferentes configurações para desenvolvimento, teste e produção.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Define o diretório base da aplicação
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Configuração base que contém as configurações comuns a todos os ambientes.
    """
    # Chave secreta para assinatura de tokens e sessões
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # Chave secreta específica para tokens JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    # Tempo de expiração dos tokens JWT (1 hora)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    # Desativa o rastreamento de modificações do SQLAlchemy para melhor performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Configurações padrão de debug e teste
    DEBUG = False
    TESTING = False
    
    # URL base para geração de links
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5001')
    
    # Diretório de uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(basedir, 'uploads'))
    
    # Tamanho máximo de upload (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Configurações de Pool para PostgreSQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,               # Tamanho inicial do pool
        'max_overflow': 10,           # Conexões extras permitidas
        'pool_timeout': 30,           # Tempo de espera para obter uma conexão
        'pool_recycle': 1800,         # Recicla conexões a cada 30 minutos
        'pool_pre_ping': True         # Verifica se as conexões estão válidas
    }

class DevelopmentConfig(Config):
    """
    Configuração específica para ambiente de desenvolvimento.
    Usa SQLite localmente para desenvolvimento, enquanto as questões de compatibilidade com Postgres são resolvidas.
    """
    DEBUG = True
    # Usar SQLite para desenvolvimento local
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'crm_dev.db')

class TestingConfig(Config):
    """
    Configuração específica para ambiente de testes.
    Usa um banco de dados SQLite separado para testes.
    """
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'crm_test.db')

class ProductionConfig(Config):
    """
    Configuração específica para ambiente de produção.
    Usa a URL do banco de dados Supabase definida nas variáveis de ambiente.
    """
    db_url = os.environ.get('SUPABASE_DATABASE_URL') or os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    SQLALCHEMY_DATABASE_URI = db_url
    
    # Configurações adicionais para PostgreSQL/Supabase
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,  # Recicla conexões a cada 30 minutos
        'pool_pre_ping': True  # Verifica se as conexões estão válidas antes de usá-las
    }

# Mapeamento de ambientes para suas respectivas configurações
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """
    Retorna a configuração apropriada com base no ambiente atual.
    Por padrão, retorna a configuração de desenvolvimento.
    """
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name[env]
