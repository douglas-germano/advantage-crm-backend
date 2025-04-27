"""
Módulo que define o modelo de Lead para o sistema CRM.

Um Lead representa um potencial cliente no funil de vendas.
O modelo armazena informações de contato, interesses, status e histórico.
"""
from datetime import datetime
from app import db
from flask import current_app


class Lead(db.Model):
    """
    Modelo para armazenar e gerenciar informações de leads de venda.
    
    Attributes:
        id (int): Identificador único do lead
        nome (str): Nome completo do contato
        email (str): Email principal do contato
        telefone (str): Número de telefone do contato
        empresa (str): Nome da empresa do contato
        cargo (str): Cargo ou função do contato na empresa
        interesse (str): Produto ou serviço de interesse
        origem (str): Canal de origem do lead (site, indicação, etc.)
        status (str): Status atual do lead no funil de vendas
        observacoes (Text): Notas adicionais sobre o lead
        criado_em (DateTime): Data e hora de criação do lead
        atualizado_em (DateTime): Data e hora da última atualização
        usuario_id (int): ID do usuário responsável pelo lead
        usuario (relationship): Relação com o usuário responsável
    """

    __tablename__ = 'leads'

    # Colunas principais
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    empresa = db.Column(db.String(100))
    cargo = db.Column(db.String(100))
    interesse = db.Column(db.String(100))
    origem = db.Column(db.String(50))
    status = db.Column(db.String(50), default='novo')
    observacoes = db.Column(db.Text)
    
    # Colunas de auditoria
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    usuario = db.relationship('User', backref='leads')

    def to_dict(self):
        """
        Converte o objeto Lead em um dicionário para serialização.
        
        Returns:
            dict: Representação do lead em formato de dicionário
        
        Raises:
            Exception: Captura e registra erros durante a conversão
        """
        try:
            # Processa o relacionamento com usuário de forma segura
            usuario_dict = None
            if self.usuario:
                try:
                    usuario_dict = self.usuario.to_dict()
                except Exception as e:
                    current_app.logger.error(f"Erro ao converter usuário para dicionário: {str(e)}")
                    # Cria um dicionário básico se to_dict() falhar
                    usuario_dict = {'id': self.usuario.id} if hasattr(self.usuario, 'id') else None
            
            # Constrói o dicionário com todos os campos
            return {
                'id': self.id,
                'nome': self.nome,
                'email': self.email,
                'telefone': self.telefone or '',
                'empresa': self.empresa or '',
                'cargo': self.cargo or '',
                'interesse': self.interesse or '',
                'origem': self.origem or '',
                'status': self.status or 'novo',
                'observacoes': self.observacoes or '',
                'criado_em': self.criado_em.isoformat() if self.criado_em else None,
                'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
                'usuario_id': self.usuario_id,
                'usuario': usuario_dict
            }
        except Exception as e:
            current_app.logger.error(f"Erro no to_dict do Lead {self.id}: {str(e)}")
            # Retorna um dicionário mínimo em caso de erro
            return {
                'id': self.id,
                'nome': self.nome,
                'email': self.email,
                'error': 'Erro ao converter todos os campos'
            }

    @staticmethod
    def from_dict(data):
        """
        Cria um novo objeto Lead a partir de um dicionário.
        
        Args:
            data (dict): Dicionário contendo dados do lead
            
        Returns:
            Lead: Nova instância de Lead ou None se falhar
        """
        if not data:
            return None
            
        lead = Lead()
        
        # Mapeia campos principais do dicionário para o objeto
        for field in ['nome', 'email', 'telefone', 'empresa', 'cargo', 'interesse', 
                      'origem', 'observacoes']:
            if field in data:
                setattr(lead, field, data.get(field))
                
        # Configuração especial para status, com valor padrão
        lead.status = data.get('status', 'novo')
        
        # Configuração do usuario_id com tratamento para diferentes tipos
        if 'usuario_id' in data:
            try:
                lead.usuario_id = int(data['usuario_id'])
            except (ValueError, TypeError):
                lead.usuario_id = data.get('usuario_id')
                
        return lead
