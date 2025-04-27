from datetime import datetime
from app import db

class Deal(db.Model):
    """Model for storing sales deals information."""

    __tablename__ = 'deals'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Float, default=0.0)
    description = db.Column(db.Text)
    
    # Pipeline information
    pipeline_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stages.id'))
    pipeline_stage = db.relationship('PipelineStage', backref='deals')
    probability = db.Column(db.Integer, default=0)  # 0-100%
    expected_close_date = db.Column(db.Date)
    closed_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(50), default='open')  # open, won, lost
    
    # Relationships
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    lead = db.relationship('Lead', backref='deals')
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    usuario = db.relationship('User', backref='deals')
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Converts object to dictionary."""
        try:
            usuario_dict = None
            if self.usuario:
                try:
                    usuario_dict = self.usuario.to_dict()
                except Exception as e:
                    from flask import current_app
                    current_app.logger.error(f"Error converting user to dict: {str(e)}")
                    usuario_dict = {'id': self.usuario.id} if hasattr(self.usuario, 'id') else None
            
            lead_dict = None
            if self.lead:
                try:
                    # Only include essential lead information to avoid circular references
                    lead_dict = {
                        'id': self.lead.id,
                        'nome': self.lead.nome,
                        'email': self.lead.email
                    }
                except Exception as e:
                    from flask import current_app
                    current_app.logger.error(f"Error converting lead to dict: {str(e)}")
                    lead_dict = {'id': self.lead.id} if hasattr(self.lead, 'id') else None
            
            stage_dict = None
            if self.pipeline_stage:
                try:
                    stage_dict = self.pipeline_stage.to_dict()
                except Exception as e:
                    from flask import current_app
                    current_app.logger.error(f"Error converting pipeline stage to dict: {str(e)}")
                    stage_dict = {'id': self.pipeline_stage.id} if hasattr(self.pipeline_stage, 'id') else None
            
            return {
                'id': self.id,
                'title': self.title,
                'value': self.value,
                'description': self.description or '',
                'pipeline_stage_id': self.pipeline_stage_id,
                'pipeline_stage': stage_dict,
                'probability': self.probability,
                'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
                'closed_date': self.closed_date.isoformat() if self.closed_date else None,
                'status': self.status,
                'lead_id': self.lead_id,
                'lead': lead_dict,
                'usuario_id': self.usuario_id,
                'usuario': usuario_dict,
                'criado_em': self.criado_em.isoformat() if self.criado_em else None,
                'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
            }
        except Exception as e:
            from flask import current_app
            current_app.logger.error(f"Error in Deal.to_dict() for deal {self.id}: {str(e)}")
            return {
                'id': self.id,
                'title': self.title,
                'error': 'Error converting all fields'
            }

    @staticmethod
    def from_dict(data):
        """Creates or updates object from dictionary."""
        # Convert date strings to datetime objects if they exist
        expected_close_date = None
        if data.get('expected_close_date'):
            try:
                if isinstance(data['expected_close_date'], str):
                    expected_close_date = datetime.fromisoformat(data['expected_close_date'])
                else:
                    expected_close_date = data['expected_close_date']
            except (ValueError, TypeError):
                pass
                
        closed_date = None
        if data.get('closed_date'):
            try:
                if isinstance(data['closed_date'], str):
                    closed_date = datetime.fromisoformat(data['closed_date'])
                else:
                    closed_date = data['closed_date']
            except (ValueError, TypeError):
                pass
                
        return Deal(
            title=data.get('title'),
            value=data.get('value', 0.0),
            description=data.get('description'),
            pipeline_stage_id=data.get('pipeline_stage_id'),
            probability=data.get('probability', 0),
            expected_close_date=expected_close_date,
            closed_date=closed_date,
            status=data.get('status', 'open'),
            lead_id=data.get('lead_id'),
            usuario_id=data.get('usuario_id')
        ) 