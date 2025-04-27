from marshmallow import Schema, fields, validate

class CustomFieldSchema(Schema):
    """Esquema para validação dos dados de campos personalizados"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    field_type = fields.String(required=True, validate=validate.OneOf(
        ['text', 'number', 'date', 'select', 'checkbox']
    ))
    required = fields.Boolean(required=False, default=False)
    options = fields.List(fields.String(), required=False) # Validação básica, conversão pode ser necessária
    active = fields.Boolean(required=False, default=True) 