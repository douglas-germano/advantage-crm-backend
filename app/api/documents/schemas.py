from marshmallow import Schema, fields, validate, validates, ValidationError

class DocumentSchema(Schema):
    """Schema para validação e serialização de documentos"""
    id = fields.Int(dump_only=True)
    
    filename = fields.Str(dump_only=True)
    original_filename = fields.Str(dump_only=True)
    file_path = fields.Str(dump_only=True)
    file_size = fields.Int(dump_only=True)
    file_type = fields.Str(dump_only=True)
    
    title = fields.Str(validate=validate.Length(max=255))
    description = fields.Str()
    
    entity_type = fields.Str(validate=validate.OneOf([
        'customer', 'lead', 'deal', 'task', 'communication', 'workflow', 'none'
    ]))
    entity_id = fields.Int()
    
    communication_id = fields.Int()
    
    uploaded_by = fields.Int(dump_only=True)
    uploader_name = fields.Str(dump_only=True)
    
    is_public = fields.Bool(default=False)
    access_code = fields.Str(validate=validate.Length(max=20))
    
    extension = fields.Str(dump_only=True)
    is_image = fields.Bool(dump_only=True)
    is_document = fields.Bool(dump_only=True)
    
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    
    @validates('entity_id')
    def validate_entity_id(self, value):
        """Valida que entity_id está presente apenas se entity_type não for 'none'"""
        entity_type = self.context.get('entity_type')
        if entity_type and entity_type != 'none' and (value is None or value <= 0):
            raise ValidationError("O ID da entidade é obrigatório quando um tipo de entidade é fornecido")
        return value
