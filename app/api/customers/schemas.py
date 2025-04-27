from marshmallow import Schema, fields, validate

class CustomerSchema(Schema):
    """Esquema para validação dos dados do cliente"""
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True)
    company = fields.String(required=False, allow_none=True)
    address = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, validate=validate.OneOf(
        ['lead', 'oportunidade', 'cliente', 'inativo']
    ))
    assigned_to = fields.Integer(required=False, allow_none=True)
    # Inclui a validação para campos personalizados como um dicionário
    custom_fields = fields.Dict(keys=fields.Integer(), values=fields.String(), required=False) 