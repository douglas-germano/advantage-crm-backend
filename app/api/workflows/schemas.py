from marshmallow import Schema, fields, validate, validates, ValidationError

class WorkflowActionSchema(Schema):
    """Schema para validação e serialização de ações de workflow"""
    id = fields.Int(dump_only=True)
    workflow_id = fields.Int(dump_only=True)
    sequence = fields.Int(required=True, validate=validate.Range(min=1))
    
    action_type = fields.Str(required=True, validate=validate.OneOf([
        'update_field', 'create_task', 'send_email', 'assign_user', 
        'change_status', 'create_notification', 'webhook'
    ]))
    
    action_data = fields.Dict(required=True)
    condition = fields.Dict()
    
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    
    @validates('action_data')
    def validate_action_data(self, value):
        """Valida que action_data contém os campos necessários para o tipo de ação"""
        action_type = self.context.get('action_type')
        
        if not action_type:
            return value
            
        # Validar campos obrigatórios com base no tipo de ação
        if action_type == 'update_field':
            if 'field' not in value or 'value' not in value:
                raise ValidationError("Os campos 'field' e 'value' são obrigatórios para ações do tipo 'update_field'")
                
        elif action_type == 'create_task':
            if 'title' not in value:
                raise ValidationError("O campo 'title' é obrigatório para ações do tipo 'create_task'")
                
        elif action_type == 'send_email':
            if 'template' not in value or 'subject' not in value:
                raise ValidationError("Os campos 'template' e 'subject' são obrigatórios para ações do tipo 'send_email'")
                
        elif action_type == 'assign_user':
            if 'user_id' not in value and 'role' not in value:
                raise ValidationError("Um dos campos 'user_id' ou 'role' é obrigatório para ações do tipo 'assign_user'")
                
        elif action_type == 'webhook':
            if 'url' not in value:
                raise ValidationError("O campo 'url' é obrigatório para ações do tipo 'webhook'")
                
        return value


class WorkflowSchema(Schema):
    """Schema para validação e serialização de workflows"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    description = fields.Str()
    
    entity_type = fields.Str(required=True, validate=validate.OneOf([
        'customer', 'lead', 'deal', 'task'
    ]))
    
    is_active = fields.Bool(default=True)
    
    trigger_type = fields.Str(required=True, validate=validate.OneOf([
        'on_create', 'on_update', 'on_status_change', 'scheduled'
    ]))
    
    trigger_data = fields.Dict()
    
    actions = fields.List(fields.Nested(WorkflowActionSchema))
    
    created_by = fields.Int()
    creator_name = fields.Str(dump_only=True)
    
    created_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    updated_at = fields.DateTime(format='%Y-%m-%d %H:%M:%S', dump_only=True)
    
    @validates('trigger_data')
    def validate_trigger_data(self, value):
        """Valida que trigger_data contém os campos necessários para o tipo de gatilho"""
        trigger_type = self.context.get('trigger_type')
        
        if not trigger_type or not value:
            return value
            
        # Validar campos obrigatórios com base no tipo de gatilho
        if trigger_type == 'on_status_change':
            if 'from_status' not in value and 'to_status' not in value:
                raise ValidationError("Pelo menos um dos campos 'from_status' ou 'to_status' é obrigatório para gatilhos do tipo 'on_status_change'")
                
        elif trigger_type == 'scheduled':
            if 'frequency' not in value:
                raise ValidationError("O campo 'frequency' é obrigatório para gatilhos do tipo 'scheduled'")
                
        return value
