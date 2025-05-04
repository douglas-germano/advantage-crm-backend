from datetime import datetime
from app import db

# --- INÍCIO: Adicionar classe Pipeline ---
class Pipeline(db.Model):
    # Modelo para armazenar pipelines de vendas.
    __tablename__ = 'pipelines'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Nome do pipeline (obrigatório e único)
    description = db.Column(db.Text) # Descrição opcional do pipeline
    is_default = db.Column(db.Boolean, default=False, index=True) # Indica se este é o pipeline padrão
    
    # Relacionamento um-para-muitos com PipelineStage
    # 'backref' cria um atributo 'pipeline' em PipelineStage
    # 'lazy=dynamic' permite consultas adicionais nos estágios
    # 'cascade' garante que os estágios sejam excluídos se o pipeline for excluído
    stages = db.relationship('PipelineStage', backref='pipeline', lazy='dynamic', cascade='all, delete-orphan')
    
    # Timestamps de criação e atualização automática
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        # Converte o objeto Pipeline para um dicionário serializável.
        # Estágios não são incluídos por padrão para evitar consultas desnecessárias.
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
    # Modelo para armazenar os estágios de um pipeline de vendas.

    __tablename__ = 'pipeline_stages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False) # Nome do estágio (obrigatório)
    description = db.Column(db.Text) # Descrição opcional do estágio
    order = db.Column(db.Integer, nullable=False)  # Ordem de exibição do estágio no pipeline
    color = db.Column(db.String(20), default='#4CAF50')  # Cor para representação visual na UI (padrão: verde)
    
    # --- INÍCIO: Adicionar pipeline_id e relacionamento ---
    # Chave estrangeira referenciando o Pipeline ao qual este estágio pertence (obrigatório)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), nullable=False)
    # --- FIM: Adicionar pipeline_id e relacionamento ---

    # Indica se este é um estágio padrão do sistema (não pode ser excluído pela UI)
    is_system = db.Column(db.Boolean, default=False)
    
    # Timestamps de criação e atualização automática
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        # Converte o objeto PipelineStage para um dicionário serializável.
        try:
            return {
                'id': self.id,
                'name': self.name,
                'description': self.description or '', # Retorna string vazia se a descrição for None
                'order': self.order,
                'color': self.color,
                'pipeline_id': self.pipeline_id, # Inclui o ID do pipeline pai
                'is_system': self.is_system,
                'criado_em': self.criado_em.isoformat() if self.criado_em else None,
                'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
            }
        except Exception as e:
            # Loga o erro caso a conversão falhe
            from flask import current_app
            current_app.logger.error(f"Erro em PipelineStage.to_dict() para estágio {self.id}: {str(e)}")
            # Retorna um dicionário parcial com a indicação do erro
            return {
                'id': self.id,
                'name': self.name,
                'pipeline_id': self.pipeline_id,
                'error': 'Erro ao converter todos os campos'
            }

    @staticmethod
    def from_dict(data, pipeline_id=None):
        # Cria uma nova instância de PipelineStage a partir de um dicionário.
        # Não salva no banco de dados.
        stage = PipelineStage(
            name=data.get('name'),
            description=data.get('description'),
            order=data.get('order'),
            color=data.get('color', '#4CAF50'), # Usa cor padrão se não fornecida
            is_system=data.get('is_system', False) # Assume False se não fornecido
        )
        if pipeline_id: # Associa ao pipeline se o ID for fornecido
            stage.pipeline_id = pipeline_id
        return stage
        
    @staticmethod
    def create_default_stages(pipeline_id):
        # Cria os estágios padrão para um pipeline específico.
        # Esta função apenas adiciona os estágios à sessão; o commit deve ser feito externamente.
        
        # Define os estágios padrão
        default_stages = [
            {'name': 'Prospect', 'order': 1, 'color': '#9E9E9E', 'is_system': True},
            {'name': 'Qualification', 'order': 2, 'color': '#2196F3', 'is_system': True},
            {'name': 'Proposal', 'order': 3, 'color': '#FF9800', 'is_system': True},
            {'name': 'Negotiation', 'order': 4, 'color': '#F44336', 'is_system': True},
            {'name': 'Closed Won', 'order': 5, 'color': '#4CAF50', 'is_system': True},
            {'name': 'Closed Lost', 'order': 6, 'color': '#795548', 'is_system': True}
        ]
        
        # Itera sobre os dados e cria as instâncias PipelineStage
        for stage_data in default_stages:
            stage = PipelineStage(**stage_data)
            stage.pipeline_id = pipeline_id # Associa o estágio ao pipeline correto
            db.session.add(stage) # Adiciona à sessão do SQLAlchemy
        
        # O commit é intencionalmente omitido aqui para permitir que seja feito
        # como parte de uma transação maior (ex: ao criar o pipeline)
        # try:
        #     db.session.commit()
        # except Exception as e:
        #     db.session.rollback()
        #     from flask import current_app
        #     current_app.logger.error(f"Erro ao criar estágios padrão para pipeline {pipeline_id}: {str(e)}") 
    # --- FIM ALTERAÇÃO --- 