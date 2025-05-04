from datetime import datetime
from app import db
from sqlalchemy.orm import relationship
from .custom_field import CustomFieldValue

class Customer(db.Model):
    # Modelo de cliente (que pode ser um lead, oportunidade, etc.) para o CRM.
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True) # Identificador único
    name = db.Column(db.String(100), nullable=False) # Nome do cliente (obrigatório)
    email = db.Column(db.String(100)) # Endereço de email
    phone = db.Column(db.String(20)) # Número de telefone
    company = db.Column(db.String(100)) # Empresa do cliente
    address = db.Column(db.Text) # Endereço
    status = db.Column(db.String(20), default='lead')  # Status atual: lead, oportunidade, cliente, inativo, etc.
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id')) # ID do usuário responsável
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # Data e hora de criação
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # Data e hora da última atualização
    
    # Relacionamentos
    # Usuário responsável por este cliente
    assigned_user = db.relationship('User', backref='customers')
    # Valores dos campos personalizados associados a este cliente
    # cascade='all, delete-orphan' garante que os valores sejam excluídos junto com o cliente
    custom_fields = db.relationship('CustomFieldValue', backref='customer', cascade='all, delete-orphan')
    
    def __init__(self, name, email=None, phone=None, company=None, address=None, 
                 status='lead', assigned_to=None):
        # Construtor da classe Customer.
        self.name = name
        self.email = email
        self.phone = phone
        self.company = company
        self.address = address
        self.status = status
        self.assigned_to = assigned_to
    
    def add_custom_field(self, field_id, value):
        # Adiciona ou atualiza um valor de campo personalizado para este cliente.
        # Verifica se um valor para este field_id já existe.
        existing = [f for f in self.custom_fields if f.custom_field_id == field_id]
        
        if existing:
            # Atualiza o valor se já existir.
            existing[0].value = value
        else:
            # Cria um novo CustomFieldValue se não existir.
            field_value = CustomFieldValue(
                customer_id=self.id, # Associa ao ID deste cliente
                custom_field_id=field_id,
                value=value
            )
            self.custom_fields.append(field_value) # Adiciona à lista de campos personalizados do cliente
    
    def get_custom_field_value(self, field_id):
        # Obtém o valor de um campo personalizado específico pelo seu ID.
        field = [f for f in self.custom_fields if f.custom_field_id == field_id]
        # Retorna o valor ou None se não encontrado.
        return field[0].value if field else None
    
    def get_custom_fields(self):
        # Retorna todos os campos personalizados associados a este cliente como um dicionário.
        # A chave é o nome do campo personalizado e o valor é o seu valor.
        return {f.custom_field.name: f.value for f in self.custom_fields if f.custom_field}
    
    def to_dict(self, include_custom_fields=True):
        # Retorna uma representação em dicionário do objeto Customer.
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'address': self.address,
            'status': self.status,
            'assigned_to': self.assigned_to, # ID do usuário responsável
            'assigned_user_name': self.assigned_user.name if self.assigned_user else None, # Nome do usuário responsável
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Inclui os campos personalizados no dicionário se solicitado.
        if include_custom_fields:
            data['custom_fields'] = self.get_custom_fields()
        
        return data
    
    def __repr__(self):
        # Representação textual do objeto para debug.
        return f'<Customer {self.name}>'
