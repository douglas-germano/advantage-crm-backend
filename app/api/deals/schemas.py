from marshmallow import Schema, fields, validate

class DealSchema(Schema):
    """Esquema para validação dos dados de Deal"""
    title = fields.String(required=True, validate=validate.Length(min=1, max=100))
    value = fields.Float(required=False, allow_none=True, validate=validate.Range(min=0))
    description = fields.String(required=False, allow_none=True)
    pipeline_stage_id = fields.Integer(required=True) # Obrigatório na criação e ao mover
    probability = fields.Integer(required=False, allow_none=True, validate=validate.Range(min=0, max=100))
    expected_close_date = fields.Date(required=False, allow_none=True) # Aceita YYYY-MM-DD
    closed_date = fields.Date(required=False, allow_none=True) # Aceita YYYY-MM-DD
    status = fields.String(required=False, validate=validate.OneOf(['open', 'won', 'lost']))
    lead_id = fields.Integer(required=False, allow_none=True)
    # usuario_id não é incluído aqui, gerenciado pela rota 