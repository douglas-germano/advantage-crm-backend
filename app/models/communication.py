from datetime import datetime
from app import db

class Communication(db.Model):
    # Modelo para registrar interações e comunicações com clientes, leads ou deals.
    __tablename__ = 'communications'
    
    id = db.Column(db.Integer, primary_key=True) # Identificador único
    
    # Tipo da comunicação (obrigatório). Ex: 'email', 'phone_call', 'meeting', 'note'.
    comm_type = db.Column(db.String(20), nullable=False)
    
    # Conteúdo e metadados da comunicação
    subject = db.Column(db.String(200)) # Assunto (relevante para emails, reuniões).
    content = db.Column(db.Text) # Corpo da mensagem, notas da reunião, resumo da ligação.
    outcome = db.Column(db.String(100))  # Resultado ou status da comunicação (ex: 'positive', 'negative', 'follow_up_required', 'no_answer').
    
    # Data e hora em que a comunicação ocorreu.
    date_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Duração em minutos (relevante para ligações, reuniões).
    duration_minutes = db.Column(db.Integer)
    
    # Entidade à qual esta comunicação está associada (relação polimórfica).
    entity_type = db.Column(db.String(50))  # Tipo da entidade: 'customer', 'lead', 'deal'.
    entity_id = db.Column(db.Integer) # ID da entidade relacionada.
    
    # Usuário do sistema que registrou ou realizou a comunicação.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # Relacionamento para buscar o objeto User.
    user = db.relationship('User', backref='communications')
    
    # Relacionamento com documentos anexados a esta comunicação.
    # 'cascade' garante que os anexos (registros na tabela Document) sejam excluídos se a comunicação for excluída.
    # 'foreign_keys' é necessário porque a tabela Document pode ter outras FKs.
    attachments = db.relationship('Document', backref='communication', 
                                  cascade='all, delete-orphan',
                                  foreign_keys='Document.communication_id')
    
    # Timestamps de criação e atualização automática.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, comm_type, subject=None, content=None, outcome=None, date_time=None,
                 duration_minutes=None, entity_type=None, entity_id=None, user_id=None):
        # Construtor da classe Communication.
        self.comm_type = comm_type
        self.subject = subject
        self.content = content
        self.outcome = outcome
        self.date_time = date_time or datetime.utcnow() # Usa a data/hora atual se não for fornecida.
        self.duration_minutes = duration_minutes
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.user_id = user_id
    
    def to_dict(self, include_attachments=True):
        # Retorna uma representação em dicionário do objeto Communication.
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
            'user_id': self.user_id, # ID do usuário
            'user_name': self.user.name if self.user else None, # Nome do usuário via relacionamento
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Inclui a lista de anexos (convertidos para dicionário) se solicitado.
        # Não inclui o conteúdo do anexo por padrão (include_content=False).
        if include_attachments:
            data['attachments'] = [attachment.to_dict(include_content=False) 
                                  for attachment in self.attachments]
        
        return data
    
    def __repr__(self):
        # Representação textual do objeto para debug.
        return f'<Communication {self.id}: {self.comm_type}>'
