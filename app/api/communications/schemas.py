from marshmallow import Schema, fields, validate, validates, ValidationError

class CommunicationSchema(Schema):
    """Schema para validação e serialização de comunicações"""
    id = fields.Int(dump_only=True)
    
    comm_type = fields.Str(required=True, validate=validate.OneOf([
        'email', 'phone', 'meeting', 'video_call', 'whatsapp', 'sms', 'other'
    ]))
    
    subject = fields.Str(validate=validate.Length(max=200))
    content = fields.Str()
    outcome = fields.Str(validate=validate.OneOf([
        'positive', 'negative', 'neutral', 'follow_up_required', 'no_response', 'other'
    ]))
    
    date_time = fields.DateTime(format='%Y-%m-%d %H:%M:%S')
    duration_minutes = fields.Int(validate=validate.Range(min=1, max=1440))  # Máximo de 24 horas
    
    entity_type = fields.Str(validate=validate.OneOf(['customer', 'lead', 'deal', 'none']))
    entity_id = fields.Int()
    
    user_id = fields.Int()
    user_name = fields.Str(dump_only=True)
    
    attachments = fields.List(fields.Dict(), dump_only=True)
    
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    
    @validates('entity_id')
    def validate_entity_id(self, value):
        """Valida que entity_id está presente apenas se entity_type não for 'none'"""
        entity_type = self.context.get('entity_type')
        if entity_type and entity_type != 'none' and (value is None or value <= 0):
            raise ValidationError("O ID da entidade é obrigatório quando um tipo de entidade é fornecido")
        return value
