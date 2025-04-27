from datetime import datetime
from app import db

class Communication(db.Model):
    """Modelo para registro de comunicações com clientes/leads"""
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Tipo de comunicação
    comm_type = db.Column(db.String(20), nullable=False)  # email, phone, meeting, etc.
    
    # Conteúdo e metadados
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    outcome = db.Column(db.String(100))  # resultado: positive, negative, follow_up_required, etc.
    
    # Data e hora
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Duração (para ligações, reuniões, etc.)
    duration_minutes = db.Column(db.Integer)
    
    # Entidade relacionada (polimórfica)
    entity_type = db.Column(db.String(50))  # customer, lead, deal
    entity_id = db.Column(db.Integer)
    
    # Usuário que realizou a comunicação
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref='communications')
    
    # Relacionamento com arquivos anexados
    attachments = db.relationship('Document', backref='communication', 
                                  cascade='all, delete-orphan',
                                  foreign_keys='Document.communication_id')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, comm_type, subject=None, content=None, outcome=None, date_time=None,
                 duration_minutes=None, entity_type=None, entity_id=None, user_id=None):
        self.comm_type = comm_type
        self.subject = subject
        self.content = content
        self.outcome = outcome
        self.date_time = date_time or datetime.utcnow()
        self.duration_minutes = duration_minutes
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.user_id = user_id
    
    def to_dict(self, include_attachments=True):
        """Retorna uma representação em dicionário da comunicação"""
        data = {
            'id': self.id,
            'comm_type': self.comm_type,
            'subject': self.subject,
            'content': self.content,
            'outcome': self.outcome,
            'date_time': self.date_time.strftime('%Y-%m-%d %H:%M:%S') if self.date_time else None,
            'duration_minutes': self.duration_minutes,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if include_attachments:
            data['attachments'] = [attachment.to_dict(include_content=False) 
                                  for attachment in self.attachments]
        
        return data
    
    def __repr__(self):
        return f'<Communication {self.id}: {self.comm_type}>'
