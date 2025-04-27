from datetime import datetime
from app import db

# --- INÍCIO: Adicionar classe Pipeline ---
class Pipeline(db.Model):
    """Model for storing sales pipelines."""
    __tablename__ = 'pipelines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Nome do pipeline
    description = db.Column(db.Text) # Descrição opcional
    is_default = db.Column(db.Boolean, default=False, index=True) # Indica se é o pipeline padrão
    
    # Relacionamento com estágios
    stages = db.relationship('PipelineStage', backref='pipeline', lazy='dynamic', cascade='all, delete-orphan')
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_default': self.is_default,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
            # Não incluir 'stages' aqui por padrão para evitar carga excessiva
        }
# --- FIM: Adicionar classe Pipeline ---

class PipelineStage(db.Model):
    """Model for storing sales pipeline stages."""

    __tablename__ = 'pipeline_stages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)  # For ordering the stages
    color = db.Column(db.String(20), default='#4CAF50')  # For UI representation
    
    # --- INÍCIO: Adicionar pipeline_id e relacionamento ---
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), nullable=False)
    # --- FIM: Adicionar pipeline_id e relacionamento ---

    # Track if this is a system default stage that shouldn't be deleted
    is_system = db.Column(db.Boolean, default=False)
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Converts object to dictionary."""
        try:
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description or '',
                'order': self.order,
                'color': self.color,
                'pipeline_id': self.pipeline_id, # Incluir ID do pipeline
                'is_system': self.is_system,
                'criado_em': self.criado_em.isoformat() if self.criado_em else None,
                'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
            }
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error in PipelineStage.to_dict() for stage {self.id}: {str(e)}")
            return {
                'id': self.id,
                'name': self.name,
                'pipeline_id': self.pipeline_id,
                'error': 'Error converting all fields'
            }

    @staticmethod
    def from_dict(data, pipeline_id=None):
        """Creates or updates object from dictionary."""
        stage = PipelineStage(
            name=data.get('name'),
            description=data.get('description'),
            order=data.get('order'),
            color=data.get('color', '#4CAF50'),
            is_system=data.get('is_system', False)
        )
        if pipeline_id:
            stage.pipeline_id = pipeline_id
        return stage
        
    @staticmethod
    def create_default_stages(pipeline_id):
        """Creates default pipeline stages for a specific pipeline."""
        # Verifica se já existem stages PARA ESTE PIPELINE
        # if PipelineStage.query.filter_by(pipeline_id=pipeline_id).count() == 0:
        # Simplificação: assume que sempre criaremos ao criar o pipeline
        default_stages = [
            {'name': 'Prospect', 'order': 1, 'color': '#9E9E9E', 'is_system': True},
            {'name': 'Qualification', 'order': 2, 'color': '#2196F3', 'is_system': True},
            {'name': 'Proposal', 'order': 3, 'color': '#FF9800', 'is_system': True},
            {'name': 'Negotiation', 'order': 4, 'color': '#F44336', 'is_system': True},
            {'name': 'Closed Won', 'order': 5, 'color': '#4CAF50', 'is_system': True},
            {'name': 'Closed Lost', 'order': 6, 'color': '#795548', 'is_system': True}
        ]
        
        for stage_data in default_stages:
            stage = PipelineStage(**stage_data)
            stage.pipeline_id = pipeline_id # Associa ao pipeline
            db.session.add(stage)
        
        # Commit será feito fora desta função, geralmente após criar o Pipeline
        # try:
        #     db.session.commit()
        # except Exception as e:
        #     db.session.rollback()
        #     from flask import current_app
        #     current_app.logger.error(f"Error creating default pipeline stages for pipeline {pipeline_id}: {str(e)}") 
    # --- FIM ALTERAÇÃO --- 