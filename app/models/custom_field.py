from datetime import datetime
from app import db
import json

class CustomField(db.Model):
    """Modelo para definir campos personalizados para clientes/leads"""
    __tablename__ = 'custom_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(20), nullable=False)  # text, number, date, select, checkbox
    required = db.Column(db.Boolean, default=False)
    options = db.Column(db.Text)  # Para campos do tipo select, armazenado como JSON
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, name, field_type, required=False, options=None, active=True):
        self.name = name
        self.field_type = field_type
        self.required = required
        self.options = json.dumps(options) if options else None
        self.active = active
    
    @property
    def options_list(self):
        """Retorna as opções como uma lista para campos do tipo select"""
        return json.loads(self.options) if self.options else []
    
    def to_dict(self):
        """Retorna uma representação em dicionário do campo personalizado"""
        return {
            'id': self.id,
            'name': self.name,
            'field_type': self.field_type,
            'required': self.required,
            'options': self.options_list if self.field_type == 'select' else None,
            'active': self.active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<CustomField {self.name}>'


class CustomFieldValue(db.Model):
    """Modelo para armazenar os valores dos campos personalizados para cada cliente"""
    __tablename__ = 'custom_field_values'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    custom_field_id = db.Column(db.Integer, db.ForeignKey('custom_fields.id'), nullable=False)
    value = db.Column(db.Text)
    
    # Relacionamentos
    custom_field = db.relationship('CustomField', backref='values')
    
    def __init__(self, customer_id, custom_field_id, value):
        self.customer_id = customer_id
        self.custom_field_id = custom_field_id
        self.value = value
    
    def to_dict(self):
        """Retorna uma representação em dicionário do valor do campo personalizado"""
        return {
            'field_id': self.custom_field_id,
            'field_name': self.custom_field.name if self.custom_field else None,
            'field_type': self.custom_field.field_type if self.custom_field else None,
            'value': self.value
        }
    
    def __repr__(self):
        return f'<CustomFieldValue {self.custom_field_id}={self.value}>'
