from datetime import datetime
from app import db
from sqlalchemy.orm import relationship
from .custom_field import CustomFieldValue

class Customer(db.Model):
    """Modelo de cliente/lead para o CRM"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    company = db.Column(db.String(100))
    address = db.Column(db.Text)
    status = db.Column(db.String(20), default='lead')  # lead, oportunidade, cliente, inativo
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    assigned_user = db.relationship('User', backref='customers')
    custom_fields = db.relationship('CustomFieldValue', backref='customer', cascade='all, delete-orphan')
    
    def __init__(self, name, email=None, phone=None, company=None, address=None, 
                 status='lead', assigned_to=None):
        self.name = name
        self.email = email
        self.phone = phone
        self.company = company
        self.address = address
        self.status = status
        self.assigned_to = assigned_to
    
    def add_custom_field(self, field_id, value):
        """Adiciona ou atualiza um valor de campo personalizado"""
        # Verifica se o campo já existe
        existing = [f for f in self.custom_fields if f.custom_field_id == field_id]
        
        if existing:
            # Atualiza o valor existente
            existing[0].value = value
        else:
            # Cria um novo valor
            field_value = CustomFieldValue(
                customer_id=self.id,
                custom_field_id=field_id,
                value=value
            )
            self.custom_fields.append(field_value)
    
    def get_custom_field_value(self, field_id):
        """Obtém o valor de um campo personalizado"""
        field = [f for f in self.custom_fields if f.custom_field_id == field_id]
        return field[0].value if field else None
    
    def get_custom_fields(self):
        """Retorna todos os campos personalizados como um dicionário"""
        return {f.custom_field.name: f.value for f in self.custom_fields if f.custom_field}
    
    def to_dict(self, include_custom_fields=True):
        """Retorna uma representação em dicionário do cliente"""
        data = {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'company': self.company,
            'address': self.address,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'assigned_user_name': self.assigned_user.name if self.assigned_user else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if include_custom_fields:
            data['custom_fields'] = self.get_custom_fields()
        
        return data
    
    def __repr__(self):
        return f'<Customer {self.name}>'
