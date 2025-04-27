from datetime import datetime
from app import db
import json

class Workflow(db.Model):
    """Modelo para fluxos de trabalho automatizados no CRM"""
    __tablename__ = 'workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Tipo de entidade que este workflow se aplica
    entity_type = db.Column(db.String(50), nullable=False)  # customer, lead, deal, task
    
    # Status do workflow
    is_active = db.Column(db.Boolean, default=True)
    
    # Trigger - evento que inicia o workflow
    trigger_type = db.Column(db.String(50), nullable=False)  # on_create, on_update, on_status_change, scheduled
    trigger_data = db.Column(db.Text)  # JSON com detalhes do gatilho (ex: campos específicos, status, etc.)
    
    # Ações a serem executadas
    actions = db.relationship('WorkflowAction', backref='workflow', 
                             cascade='all, delete-orphan',
                             order_by='WorkflowAction.sequence')
    
    # Usuário que criou o workflow
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    creator = db.relationship('User', backref='created_workflows')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, name, entity_type, trigger_type, description=None, 
                 trigger_data=None, is_active=True, created_by=None):
        self.name = name
        self.description = description
        self.entity_type = entity_type
        self.trigger_type = trigger_type
        self.trigger_data = json.dumps(trigger_data) if trigger_data else None
        self.is_active = is_active
        self.created_by = created_by
    
    def get_trigger_data(self):
        """Retorna os dados do gatilho como um dicionário"""
        return json.loads(self.trigger_data) if self.trigger_data else {}
    
    def to_dict(self, include_actions=True):
        """Retorna uma representação em dicionário do workflow"""
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'entity_type': self.entity_type,
            'is_active': self.is_active,
            'trigger_type': self.trigger_type,
            'trigger_data': self.get_trigger_data(),
            'created_by': self.created_by,
            'creator_name': self.creator.name if self.creator else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if include_actions:
            data['actions'] = [action.to_dict() for action in self.actions]
        
        return data
    
    def __repr__(self):
        return f'<Workflow {self.id}: {self.name}>'


class WorkflowAction(db.Model):
    """Modelo para ações a serem executadas em um workflow"""
    __tablename__ = 'workflow_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False)
    
    # Ordenação das ações
    sequence = db.Column(db.Integer, nullable=False)
    
    # Tipo de ação
    action_type = db.Column(db.String(50), nullable=False)  # update_field, create_task, send_email, etc.
    
    # Dados da ação
    action_data = db.Column(db.Text, nullable=False)  # JSON com detalhes da ação
    
    # Condição (opcional)
    condition = db.Column(db.Text)  # JSON com condição para executar a ação
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, workflow_id, action_type, action_data, sequence, condition=None):
        self.workflow_id = workflow_id
        self.action_type = action_type
        self.sequence = sequence
        self.action_data = json.dumps(action_data) if isinstance(action_data, dict) else action_data
        self.condition = json.dumps(condition) if isinstance(condition, dict) else condition
    
    def get_action_data(self):
        """Retorna os dados da ação como um dicionário"""
        return json.loads(self.action_data) if self.action_data else {}
    
    def get_condition(self):
        """Retorna a condição como um dicionário"""
        return json.loads(self.condition) if self.condition else {}
    
    def to_dict(self):
        """Retorna uma representação em dicionário da ação"""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'sequence': self.sequence,
            'action_type': self.action_type,
            'action_data': self.get_action_data(),
            'condition': self.get_condition(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<WorkflowAction {self.id}: {self.action_type} (seq: {self.sequence})>'
