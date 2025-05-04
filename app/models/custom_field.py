from datetime import datetime
from app import db
import json # Para serializar/desserializar a lista de opções

class CustomField(db.Model):
    # Modelo para definir a estrutura de campos personalizados que podem ser associados a entidades (como Clientes).
    __tablename__ = 'custom_fields'
    
    id = db.Column(db.Integer, primary_key=True) # Identificador único do campo
    name = db.Column(db.String(100), nullable=False, unique=True) # Nome/label do campo (obrigatório e único)
    field_type = db.Column(db.String(20), nullable=False)  # Tipo de dado do campo: 'text', 'number', 'date', 'select', 'checkbox', 'textarea'
    required = db.Column(db.Boolean, default=False) # Indica se o preenchimento deste campo é obrigatório
    # Opções para campos do tipo 'select', armazenadas como uma string JSON (ex: '["Opção 1", "Opção 2"]').
    options = db.Column(db.Text)
    # Indica se o campo está ativo e deve ser exibido/utilizado.
    active = db.Column(db.Boolean, default=True)
    # Data de criação do campo.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, name, field_type, required=False, options=None, active=True):
        # Construtor da classe CustomField.
        self.name = name
        self.field_type = field_type
        self.required = required
        # Serializa a lista/dicionário de opções para JSON se fornecida.
        self.options = json.dumps(options) if options and isinstance(options, (list, dict)) else None
        self.active = active
    
    @property
    def options_list(self):
        # Desserializa a string JSON de opções de volta para uma lista Python.
        # Retorna uma lista vazia se não houver opções ou ocorrer erro na desserialização.
        if self.options:
            try:
                return json.loads(self.options)
            except json.JSONDecodeError:
                return []
        return []
    
    def to_dict(self):
        # Retorna uma representação em dicionário do objeto CustomField.
        return {
            'id': self.id,
            'name': self.name,
            'field_type': self.field_type,
            'required': self.required,
            # Inclui a lista de opções apenas se o tipo for 'select'.
            'options': self.options_list if self.field_type == 'select' else None,
            'active': self.active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        # Representação textual do objeto para debug.
        return f'<CustomField {self.id}: {self.name} ({self.field_type})>'


class CustomFieldValue(db.Model):
    # Modelo para armazenar o valor específico de um CustomField para uma entidade (atualmente, Customer).
    # Cria a relação muitos-para-muitos entre Customers e CustomFields com dados adicionais (o valor).
    __tablename__ = 'custom_field_values'
    
    id = db.Column(db.Integer, primary_key=True) # Identificador único do valor
    # Chave estrangeira para o Cliente ao qual este valor pertence (obrigatório).
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    # Chave estrangeira para o CustomField que define este valor (obrigatório).
    custom_field_id = db.Column(db.Integer, db.ForeignKey('custom_fields.id'), nullable=False, index=True)
    # O valor do campo personalizado, armazenado como texto (a validação/conversão pode ocorrer na aplicação).
    value = db.Column(db.Text)
    
    # Relacionamento para buscar o objeto CustomField associado a este valor.
    # `backref='values'` permite acessar `custom_field.values`.
    custom_field = db.relationship('CustomField', backref='values')
    # O relacionamento com Customer é definido no modelo Customer (`customer.custom_fields`).
    
    def __init__(self, customer_id, custom_field_id, value):
        # Construtor da classe CustomFieldValue.
        self.customer_id = customer_id
        self.custom_field_id = custom_field_id
        # Converte o valor para string para garantir que possa ser armazenado no campo Text.
        self.value = str(value) if value is not None else None
    
    def to_dict(self):
        # Retorna uma representação em dicionário do objeto CustomFieldValue.
        # Inclui informações do CustomField relacionado para contexto.
        return {
            'field_id': self.custom_field_id,
            'field_name': self.custom_field.name if self.custom_field else None,
            'field_type': self.custom_field.field_type if self.custom_field else None,
            'value': self.value
        }
    
    def __repr__(self):
        # Representação textual do objeto para debug.
        field_name = self.custom_field.name if self.custom_field else self.custom_field_id
        return f'<CustomFieldValue Customer={self.customer_id} Field={field_name} Value="{self.value}">'
