from datetime import datetime
from app import db

class Task(db.Model):
    """Modelo para tarefas e atividades no CRM"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Datas
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    
    # Status e prioridade
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, canceled
    priority = db.Column(db.String(10), default='medium')  # low, medium, high
    task_type = db.Column(db.String(20))  # call, meeting, email, follow_up, etc.
    
    # Entidade relacionada (polimórfica)
    entity_type = db.Column(db.String(50))  # customer, lead, deal
    entity_id = db.Column(db.Integer)
    
    # Usuário responsável
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_user = db.relationship('User', backref='tasks')
    
    # Lembretes
    reminder_date = db.Column(db.DateTime)
    reminder_sent = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, title, description=None, start_date=None, due_date=None, 
                 status='pending', priority='medium', task_type=None, 
                 entity_type=None, entity_id=None, assigned_to=None, reminder_date=None):
        self.title = title
        self.description = description
        self.start_date = start_date or datetime.utcnow()
        self.due_date = due_date
        self.status = status
        self.priority = priority
        self.task_type = task_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.assigned_to = assigned_to
        self.reminder_date = reminder_date
    
    def complete(self):
        """Marca a tarefa como concluída"""
        self.status = 'completed'
        self.completed_date = datetime.utcnow()
    
    def reopen(self):
        """Reabre a tarefa"""
        self.status = 'in_progress'
        self.completed_date = None
    
    def cancel(self):
        """Cancela a tarefa"""
        self.status = 'canceled'
    
    def to_dict(self):
        """Retorna uma representação em dicionário da tarefa"""
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
            'assigned_to': self.assigned_to,
            'assigned_user_name': self.assigned_user.name if self.assigned_user else None,
            'reminder_date': self.reminder_date.strftime('%Y-%m-%d %H:%M:%S') if self.reminder_date else None,
            'reminder_sent': self.reminder_sent,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'
