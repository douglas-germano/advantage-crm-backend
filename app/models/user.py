"""
Módulo que define o modelo de Usuário para o sistema CRM.

Este modelo gerencia autenticação, autorização e informações dos usuários.
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app import db


class User(db.Model):
    """
    Modelo de usuário para autenticação e autorização.
    
    Attributes:
        id (int): Identificador único do usuário
        name (str): Nome completo do usuário
        username (str): Nome de usuário único para login
        email (str): Email único do usuário
        password_hash (str): Hash da senha (não acessível diretamente)
        role (str): Função do usuário (admin, vendedor, suporte)
        created_at (DateTime): Data e hora de criação da conta
    """
    __tablename__ = 'users'
    
    # Colunas principais
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='vendedor')  # admin, vendedor, suporte
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constantes para roles disponíveis
    ROLE_ADMIN = 'admin'
    ROLE_VENDEDOR = 'vendedor'
    ROLE_SUPORTE = 'suporte'
    
    # Lista de roles válidas
    VALID_ROLES = [ROLE_ADMIN, ROLE_VENDEDOR, ROLE_SUPORTE]
    
    def __init__(self, name, username, email, password, role='vendedor'):
        """
        Inicializa um novo usuário.
        
        Args:
            name (str): Nome completo do usuário
            username (str): Nome de usuário único
            email (str): Email único
            password (str): Senha em texto plano (será hasheada)
            role (str, optional): Função do usuário. Padrão: 'vendedor'
        """
        self.name = name
        self.username = username
        self.email = email
        self.password = password  # Utilizará o setter para hashear
        
        # Valida o role antes de atribuir
        if role in self.VALID_ROLES:
            self.role = role
        else:
            self.role = self.ROLE_VENDEDOR
    
    @property
    def password(self):
        """
        Impede acesso direto à senha, propriedade somente para escrita.
        
        Raises:
            AttributeError: Sempre lança exceção ao tentar acessar
        """
        raise AttributeError('A senha não é um atributo legível')
        
    @password.setter
    def password(self, password):
        """
        Gera o hash da senha para armazenamento seguro.
        
        Args:
            password (str): Senha em texto plano
        """
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        """
        Verifica se a senha fornecida corresponde ao hash armazenado.
        
        Args:
            password (str): Senha em texto plano para verificação
            
        Returns:
            bool: True se a senha estiver correta, False caso contrário
        """
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self):
        """
        Gera um token JWT para o usuário com claims de identidade e função.
        
        Returns:
            str: Token JWT codificado
        """
        return create_access_token(
            identity=str(self.id), 
            additional_claims={'role': self.role}
        )
    
    def is_admin(self):
        """
        Verifica se o usuário tem função de administrador.
        
        Returns:
            bool: True se o usuário for admin, False caso contrário
        """
        return self.role == self.ROLE_ADMIN
    
    def to_dict(self):
        """
        Retorna uma representação em dicionário do usuário.
        Omite informações sensíveis como a senha.
        
        Returns:
            dict: Representação do usuário em formato de dicionário
        """
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        """
        Representação string do objeto para depuração.
        
        Returns:
            str: Representação do usuário
        """
        return f'<User {self.username}>'
