from datetime import datetime
from app import db

class Task(db.Model):
    # Modelo para representar tarefas e atividades dentro do CRM.
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True) # Identificador único
    title = db.Column(db.String(100), nullable=False) # Título da tarefa (obrigatório)
    description = db.Column(db.Text) # Descrição detalhada da tarefa
    
    # Datas importantes
    start_date = db.Column(db.DateTime, default=datetime.utcnow) # Data de início (padrão: agora)
    due_date = db.Column(db.DateTime) # Data de vencimento/prazo
    completed_date = db.Column(db.DateTime) # Data em que a tarefa foi concluída
    
    # Status, prioridade e tipo da tarefa
    status = db.Column(db.String(20), default='pending')  # Status atual: 'pending', 'in_progress', 'completed', 'canceled'
    priority = db.Column(db.String(10), default='medium')  # Prioridade: 'low', 'medium', 'high'
    task_type = db.Column(db.String(20))  # Tipo de tarefa: 'call', 'meeting', 'email', 'follow_up', etc.
    
    # Entidade à qual esta tarefa está associada (relação polimórfica).
    entity_type = db.Column(db.String(50))  # Tipo da entidade: 'customer', 'lead', 'deal'.
    entity_id = db.Column(db.Integer) # ID da entidade relacionada.
    
    # Usuário responsável pela execução da tarefa.
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    # Relacionamento para buscar o objeto User responsável.
    assigned_user = db.relationship('User', backref='tasks')
    
    # Configurações de lembrete
    reminder_date = db.Column(db.DateTime) # Data e hora para enviar um lembrete
    reminder_sent = db.Column(db.Boolean, default=False) # Indica se o lembrete já foi enviado
    
    # Timestamps de criação e atualização automática.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, title, description=None, start_date=None, due_date=None, 
                 status='pending', priority='medium', task_type=None, 
                 entity_type=None, entity_id=None, assigned_to=None, reminder_date=None):
        # Construtor da classe Task.
        self.title = title
        self.description = description
        self.start_date = start_date or datetime.utcnow() # Usa data/hora atual se não fornecida
        self.due_date = due_date
        self.status = status
        self.priority = priority
        self.task_type = task_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.assigned_to = assigned_to
        self.reminder_date = reminder_date
    
    def complete(self):
        # Marca a tarefa como concluída, definindo o status e a data de conclusão.
        self.status = 'completed'
        self.completed_date = datetime.utcnow()
    
    def reopen(self):
        # Reabre uma tarefa que estava concluída ou cancelada, definindo status como 'in_progress'.
        self.status = 'in_progress'
        self.completed_date = None # Remove a data de conclusão
    
    def cancel(self):
        # Marca a tarefa como cancelada.
        self.status = 'canceled'
    
    def to_dict(self):
        # Retorna uma representação em dicionário do objeto Task.
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_date': self.start_date.strftime('%Y-%m-%d %H:%M:%S') if self.start_date else None,
            'due_date': self.due_date.strftime('%Y-%m-%d %H:%M:%S') if self.due_date else None,
            'completed_date': self.completed_date.strftime('%Y-%m-%d %H:%M:%S') if self.completed_date else None,
            'status': self.status,
            'priority': self.priority,
            'task_type': self.task_type,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'assigned_to': self.assigned_to, # ID do usuário responsável
            'assigned_user_name': self.assigned_user.name if self.assigned_user else None, # Nome do usuário via relacionamento
            'reminder_date': self.reminder_date.strftime('%Y-%m-%d %H:%M:%S') if self.reminder_date else None,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        # Representação textual do objeto para debug.
        return f'<Task {self.id}: {self.title}>'
