from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime

class TaskSchema(Schema):
    """Schema para validação e serialização de tarefas"""
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str()
    
    start_date = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    due_date = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    completed_date = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    
    status = fields.Str(validate=validate.OneOf(['pending', 'in_progress', 'completed', 'canceled']))
    priority = fields.Str(validate=validate.OneOf(['low', 'medium', 'high']))
    task_type = fields.Str(validate=validate.OneOf(['call', 'meeting', 'email', 'follow_up', 'other']))
    
    entity_type = fields.Str(validate=validate.OneOf(['customer', 'lead', 'deal', 'none']))
    entity_id = fields.Int()
    
    assigned_to = fields.Int()
    assigned_user_name = fields.Str(dump_only=True)
    
    reminder_date = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    reminder_sent = fields.Bool(dump_only=True)
    
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    
    @validates('entity_id')
    def validate_entity_id(self, value):
        """Valida que entity_id está presente apenas se entity_type não for 'none'"""
        entity_type = self.context.get('entity_type')
        if entity_type and entity_type != 'none' and (value is None or value <= 0):
            raise ValidationError("O ID da entidade é obrigatório quando um tipo de entidade é fornecido")
        return value
    
    @validates('due_date')
    def validate_due_date(self, value):
        """Valida que a data de vencimento é posterior à data inicial"""
        start_date = self.context.get('start_date') or datetime.utcnow()
        if value and value < start_date:
            raise ValidationError("A data de vencimento deve ser posterior à data inicial")
        return value
