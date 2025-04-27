from marshmallow import Schema, fields, validate

class LeadSchema(Schema):
    """Esquema para validação dos dados de Lead"""
    nome = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    telefone = fields.String(required=False, allow_none=True, validate=validate.Length(max=20))
    empresa = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    cargo = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    interesse = fields.String(required=False, allow_none=True, validate=validate.Length(max=100))
    origem = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    status = fields.String(required=False, allow_none=True, validate=validate.Length(max=50)) # Pode adicionar validate.OneOf se houver status fixos
    observacoes = fields.String(required=False, allow_none=True)
    # usuario_id é gerenciado pela rota 