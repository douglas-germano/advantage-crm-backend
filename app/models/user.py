"""
Módulo que define o modelo de Usuário para o sistema CRM.

Este modelo gerencia autenticação, autorização e informações dos usuários.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app import db


class User(db.Model):
    # Modelo de usuário para autenticação e autorização no sistema.
    
    # Attributes:
    #     id (int): Identificador único do usuário.
    #     name (str): Nome completo do usuário.
    #     username (str): Nome de usuário único para login.
    #     email (str): Email único do usuário.
    #     password_hash (str): Hash da senha (não acessível diretamente).
    #     role (str): Função/papel do usuário (ex: admin, vendedor, suporte).
    #     created_at (DateTime): Data e hora de criação da conta.
    __tablename__ = 'users'
    
    # Colunas principais da tabela 'users'
    id = db.Column(db.Integer, primary_key=True) # Chave primária
    name = db.Column(db.String(100), nullable=False) # Nome completo (obrigatório)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True) # Nome de usuário para login (único, obrigatório, indexado)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True) # Email (único, obrigatório, indexado)
    password_hash = db.Column(db.String(256), nullable=False) # Hash da senha armazenado de forma segura (obrigatório)
    role = db.Column(db.String(20), default='vendedor')  # Função do usuário (padrão: 'vendedor')
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Data de criação (padrão: agora)
    
    # Constantes para os papéis (roles) disponíveis no sistema
    ROLE_ADMIN = 'admin'
    ROLE_VENDEDOR = 'vendedor'
    ROLE_SUPORTE = 'suporte'
    
    # Lista de papéis válidos para validação
    VALID_ROLES = [ROLE_ADMIN, ROLE_VENDEDOR, ROLE_SUPORTE]
    
    def __init__(self, name, username, email, password, role='vendedor'):
        # Inicializa uma nova instância de Usuário.
        # 
        # Args:
        #     name (str): Nome completo do usuário.
        #     username (str): Nome de usuário único.
        #     email (str): Email único.
        #     password (str): Senha em texto plano (será automaticamente hasheada pelo setter).
        #     role (str, optional): Função do usuário. Padrão: 'vendedor'. Se inválido, usa 'vendedor'.
        self.name = name
        self.username = username
        self.email = email
        self.password = password  # Utiliza o setter @password.setter para hashear a senha
        
        # Valida o papel (role) fornecido antes de atribuir.
        if role in self.VALID_ROLES:
            self.role = role
        else:
            # Se o papel fornecido não for válido, atribui o papel padrão 'vendedor'.
            self.role = self.ROLE_VENDEDOR
    
    @property
    def password(self):
        # Impede o acesso direto ao hash da senha. Propriedade apenas para escrita.
        # 
        # Raises:
        #     AttributeError: Sempre lança esta exceção ao tentar ler `user.password`.
        raise AttributeError('A senha não é um atributo legível diretamente. Use verify_password().')
        
    @password.setter
    def password(self, password):
        # Define a senha do usuário, gerando e armazenando seu hash seguro.
        # Este método é chamado automaticamente ao atribuir um valor a `user.password`.
        # 
        # Args:
        #     password (str): A senha em texto plano a ser hasheada.
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        # Verifica se a senha fornecida (em texto plano) corresponde ao hash armazenado.
        # 
        # Args:
        #     password (str): A senha em texto plano para verificação.
        #     
        # Returns:
        #     bool: True se a senha corresponder ao hash, False caso contrário.
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self):
        # Gera um token de acesso JWT (JSON Web Token) para este usuário.
        # O token inclui o ID do usuário como identidade ('sub') e seu papel ('role') como claim adicional.
        # 
        # Returns:
        #     str: O token JWT codificado como string.
        return create_access_token(
            identity=str(self.id), # Identidade do token (subject/sub claim)
            additional_claims={'role': self.role} # Claims adicionais (papel do usuário)
        )
    
    def is_admin(self):
        # Verifica se o usuário possui o papel (role) de administrador.
        # 
        # Returns:
        #     bool: True se o usuário for administrador, False caso contrário.
        return self.role == self.ROLE_ADMIN
    
    def to_dict(self):
        # Retorna uma representação em dicionário do objeto User, segura para serialização.
        # O hash da senha é omitido por segurança.
        # 
        # Returns:
        #     dict: Um dicionário contendo os atributos públicos do usuário.
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') # Formata a data para string
        }
    
    def __repr__(self):
        # Retorna uma representação textual do objeto User, útil para logs e depuração.
        # 
        # Returns:
        #     str: String representando o usuário.
        return f'<User {self.username}>'
