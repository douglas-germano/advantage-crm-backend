from datetime import datetime
from app import db

class Deal(db.Model):
    # Modelo para armazenar informações sobre negócios (oportunidades de venda).
    # Representa um lead qualificado que está progredindo no funil de vendas.

    __tablename__ = 'deals'

    id = db.Column(db.Integer, primary_key=True) # Identificador único do negócio
    title = db.Column(db.String(100), nullable=False) # Título ou nome do negócio (obrigatório)
    value = db.Column(db.Float, default=0.0) # Valor monetário estimado ou real do negócio
    description = db.Column(db.Text) # Descrição detalhada do negócio
    
    # Informações do Pipeline de Vendas
    # Chave estrangeira para o estágio atual do pipeline
    pipeline_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stages.id'), index=True)
    # Relacionamento para buscar o objeto PipelineStage associado
    pipeline_stage = db.relationship('PipelineStage', backref='deals')
    # Probabilidade de fechamento (0-100%)
    probability = db.Column(db.Integer, default=0)
    # Data esperada para o fechamento do negócio
    expected_close_date = db.Column(db.Date)
    # Data em que o negócio foi efetivamente fechado (ganho ou perdido)
    closed_date = db.Column(db.Date)
    
    # Status do negócio
    # 'open': Em andamento, 'won': Ganho, 'lost': Perdido
    status = db.Column(db.String(50), default='open', index=True)
    
    # Relacionamentos com outras entidades
    # Chave estrangeira para o Lead que originou este negócio (opcional)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    # Relacionamento para buscar o objeto Lead associado
    lead = db.relationship('Lead', backref='deals')
    
    # Chave estrangeira para o usuário responsável pelo negócio
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    # Relacionamento para buscar o objeto User responsável
    usuario = db.relationship('User', backref='deals')
    
    # Timestamps de criação e atualização automática
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        # Converte o objeto Deal em um dicionário serializável para APIs JSON.
        # Inclui informações resumidas das entidades relacionadas (usuário, lead, estágio).
        # Trata erros durante a conversão de relacionamentos.
        try:
            # Converte o usuário relacionado de forma segura
            usuario_dict = None
            if self.usuario:
                try:
                    usuario_dict = self.usuario.to_dict()
                except Exception as e:
                    from flask import current_app
                    current_app.logger.error(f"Erro ao converter usuário {self.usuario_id} para dict no Deal {self.id}: {str(e)}")
                    usuario_dict = {'id': self.usuario.id, 'name': getattr(self.usuario, 'name', 'N/A')} if hasattr(self.usuario, 'id') else None
            
            # Converte o lead relacionado de forma segura (apenas campos essenciais)
            lead_dict = None
            if self.lead:
                try:
                    # Inclui apenas informações básicas do lead para evitar carga excessiva ou referências circulares.
                    lead_dict = {
                        'id': self.lead.id,
                        'nome': self.lead.nome,
                        'email': self.lead.email
                    }
                except Exception as e:
                    from flask import current_app
                    current_app.logger.error(f"Erro ao converter lead {self.lead_id} para dict no Deal {self.id}: {str(e)}")
                    lead_dict = {'id': self.lead.id} if hasattr(self.lead, 'id') else None
            
            # Converte o estágio do pipeline relacionado de forma segura
            stage_dict = None
            if self.pipeline_stage:
                try:
                    stage_dict = self.pipeline_stage.to_dict()
                except Exception as e:
                    from flask import current_app
                    current_app.logger.error(f"Erro ao converter estágio {self.pipeline_stage_id} para dict no Deal {self.id}: {str(e)}")
                    stage_dict = {'id': self.pipeline_stage.id, 'name': getattr(self.pipeline_stage, 'name', 'N/A')} if hasattr(self.pipeline_stage, 'id') else None
            
            # Constrói o dicionário final do Deal
            return {
                'id': self.id,
                'title': self.title,
                'value': self.value,
                'description': self.description or '',
                'pipeline_stage_id': self.pipeline_stage_id,
                'pipeline_stage': stage_dict, # Dicionário do estágio
                'probability': self.probability,
                'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
                'closed_date': self.closed_date.isoformat() if self.closed_date else None,
                'status': self.status,
                'lead_id': self.lead_id,
                'lead': lead_dict, # Dicionário resumido do lead
                'usuario_id': self.usuario_id,
                'usuario': usuario_dict, # Dicionário do usuário
                'criado_em': self.criado_em.isoformat() if self.criado_em else None,
                'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
            }
        except Exception as e:
            # Loga erro geral na conversão do Deal
            from flask import current_app
            current_app.logger.error(f"Erro geral no Deal.to_dict() para deal {self.id}: {str(e)}")
            # Retorna um dicionário mínimo indicando o erro
            return {
                'id': self.id,
                'title': self.title,
                'error': 'Erro ao converter todos os campos do deal'
            }

    @staticmethod
    def from_dict(data):
        # Cria uma nova instância de Deal (sem salvar no DB) a partir de um dicionário.
        # Trata a conversão de strings de data para objetos Date.
        if not data or not isinstance(data, dict):
            from flask import current_app
            current_app.logger.warning("Tentativa de criar Deal a partir de dados inválidos.")
            return None
            
        # Converte strings ISO de data (YYYY-MM-DD) para objetos Date.
        expected_close_date = None
        expected_close_str = data.get('expected_close_date')
        if expected_close_str and isinstance(expected_close_str, str):
            try:
                 # Tenta converter apenas a parte da data (ignora hora se houver)
                expected_close_date = datetime.fromisoformat(expected_close_str.split('T')[0]).date()
            except (ValueError, TypeError) as e:
                from flask import current_app
                current_app.logger.warning(f"Formato inválido para expected_close_date: {expected_close_str}, erro: {e}")
                pass # Mantém None se a conversão falhar
                
        closed_date = None
        closed_date_str = data.get('closed_date')
        if closed_date_str and isinstance(closed_date_str, str):
            try:
                closed_date = datetime.fromisoformat(closed_date_str.split('T')[0]).date()
            except (ValueError, TypeError) as e:
                from flask import current_app
                current_app.logger.warning(f"Formato inválido para closed_date: {closed_date_str}, erro: {e}")
                pass # Mantém None se a conversão falhar
                
        # Cria a instância do Deal com os dados processados.
        # Usa .get() com valores padrão para campos opcionais.
        # Garante que usuario_id, lead_id e pipeline_stage_id sejam inteiros ou None.
        try:
            pipeline_stage_id = data.get('pipeline_stage_id')
            lead_id = data.get('lead_id')
            usuario_id = data.get('usuario_id')

            deal = Deal(
                title=data.get('title'),
                value=float(data.get('value', 0.0)) if data.get('value') is not None else 0.0,
                description=data.get('description'),
                pipeline_stage_id=int(pipeline_stage_id) if pipeline_stage_id is not None else None,
                probability=int(data.get('probability', 0)) if data.get('probability') is not None else 0,
                expected_close_date=expected_close_date,
                closed_date=closed_date,
                status=data.get('status', 'open'),
                lead_id=int(lead_id) if lead_id is not None else None,
                usuario_id=int(usuario_id) if usuario_id is not None else None
            )
            return deal
        except (ValueError, TypeError) as e:
             from flask import current_app
             current_app.logger.error(f"Erro ao criar Deal a partir do dicionário: {e}. Dados: {data}")
             return None
             
    def __repr__(self):
        # Retorna uma representação textual do objeto Deal para debug.
        return f'<Deal {self.id}: {self.title} (Stage: {self.pipeline_stage_id}, Status: {self.status})>' 