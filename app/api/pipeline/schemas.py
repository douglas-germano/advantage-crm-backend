from marshmallow import Schema, fields, validate

class PipelineStageSchema(Schema):
    """Esquema para validação dos dados de PipelineStage"""
    name = fields.String(required=True, validate=validate.Length(min=1, max=50))
    description = fields.String(required=False, allow_none=True)
    order = fields.Integer(required=True)
    color = fields.String(required=False, allow_none=True, validate=validate.Length(max=20)) # Ex: #RRGGBB
    is_system = fields.Boolean(required=False) # Geralmente não definido pelo usuário 