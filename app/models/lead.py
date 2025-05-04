"""
Módulo que define o modelo de Lead para o sistema CRM.

Um Lead representa um potencial cliente que demonstrou interesse inicial
mas ainda não foi totalmente qualificado ou convertido em um negócio (Deal).
O modelo armazena informações de contato, origem, interesse, status e histórico.
"""
from datetime import datetime
from app import db
from flask import current_app


class Lead(db.Model):
    # Modelo para armazenar e gerenciar informações de leads de venda.
    # Um lead é um contato inicial que pode se tornar um cliente ou negócio.
    
    # Attributes:
    #     id (int): Identificador único do lead.
    #     nome (str): Nome completo do contato do lead.
    #     email (str): Email principal do contato.
    #     telefone (str): Número de telefone do contato.
    #     empresa (str): Nome da empresa associada ao lead.
    #     cargo (str): Cargo ou função do contato na empresa.
    #     interesse (str): Produto, serviço ou área de interesse do lead.
    #     origem (str): Canal pelo qual o lead foi adquirido (ex: 'Website', 'Indicação', 'Evento').
    #     status (str): Status atual do lead no processo de qualificação (ex: 'Novo', 'Contato Feito', 'Qualificado', 'Perdido').
    #     observacoes (Text): Notas e informações adicionais sobre o lead.
    #     criado_em (DateTime): Data e hora de criação do registro do lead.
    #     atualizado_em (DateTime): Data e hora da última atualização do registro.
    #     usuario_id (int): ID do usuário do sistema responsável pelo acompanhamento do lead.
    #     usuario (relationship): Relação com o modelo User para obter detalhes do usuário responsável.

    __tablename__ = 'leads'

    # Colunas principais da tabela 'leads'
    id = db.Column(db.Integer, primary_key=True) # Chave primária
    nome = db.Column(db.String(100), nullable=False) # Nome do lead (obrigatório)
    email = db.Column(db.String(100), nullable=False, index=True) # Email do lead (obrigatório, indexado)
    telefone = db.Column(db.String(20)) # Telefone de contato
    empresa = db.Column(db.String(100)) # Nome da empresa
    cargo = db.Column(db.String(100)) # Cargo do contato na empresa
    interesse = db.Column(db.String(100)) # Área/produto de interesse
    origem = db.Column(db.String(50)) # Fonte/Canal de origem do lead
    status = db.Column(db.String(50), default='novo', index=True) # Status atual do lead (padrão: 'novo', indexado)
    observacoes = db.Column(db.Text) # Campo para notas e observações adicionais
    
    # Colunas de auditoria (timestamps automáticos)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com o usuário responsável
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True) # Chave estrangeira para a tabela users (indexada)
    # Define a relação com o modelo User, permitindo acessar `lead.usuario`
    # `backref='leads'` cria o atributo `user.leads` no modelo User
    usuario = db.relationship('User', backref='leads')

    def to_dict(self):
        # Converte o objeto Lead em um dicionário serializável para APIs JSON.
        # Inclui informações do usuário responsável, se disponível.
        # 
        # Returns:
        #     dict: Representação do lead em formato de dicionário.
        # 
        # Raises:
        #     Exception: Captura e loga erros que possam ocorrer durante a conversão,
        #                retornando um dicionário parcial em caso de falha.
        try:
            # Processa o relacionamento com usuário de forma segura, tratando exceções.
            usuario_dict = None
            if self.usuario:
                try:
                    # Tenta chamar o método to_dict() do usuário relacionado.
                    usuario_dict = self.usuario.to_dict()
                except Exception as e:
                    # Loga o erro se a conversão do usuário falhar.
                    current_app.logger.error(f"Erro ao converter usuário {self.usuario_id} para dicionário no Lead {self.id}: {str(e)}")
                    # Cria um dicionário básico com o ID do usuário como fallback.
                    usuario_dict = {'id': self.usuario.id, 'name': getattr(self.usuario, 'name', 'N/A')} if hasattr(self.usuario, 'id') else None
            
            # Constrói o dicionário final do lead.
            # Usa `or ''` para garantir strings vazias em vez de None para campos opcionais.
            # Formata datas para o padrão ISO 8601.
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
                'usuario': usuario_dict # Inclui o dicionário do usuário (pode ser None)
            }
        except Exception as e:
            # Loga erro geral na conversão do Lead.
            current_app.logger.error(f"Erro geral no to_dict do Lead {self.id}: {str(e)}")
            # Retorna um dicionário mínimo indicando o erro.
            return {
                'id': self.id,
                'nome': self.nome,
                'email': self.email,
                'error': 'Erro ao converter todos os campos do lead'
            }

    @staticmethod
    def from_dict(data):
        # Cria uma nova instância de Lead (sem salvar no DB) a partir de um dicionário.
        # Útil para processar dados recebidos de uma API ou formulário.
        # 
        # Args:
        #     data (dict): Dicionário contendo os dados do lead.
        #     
        # Returns:
        #     Lead: Uma nova instância de Lead populada com os dados, ou None se `data` for inválido.
        if not data or not isinstance(data, dict):
            current_app.logger.warning("Tentativa de criar Lead a partir de dados inválidos.")
            return None
            
        lead = Lead()
        
        # Mapeia campos comuns do dicionário para os atributos do objeto.
        # Itera sobre uma lista de nomes de campos esperados.
        for field in ['nome', 'email', 'telefone', 'empresa', 'cargo', 'interesse', 
                      'origem', 'observacoes']:
            if field in data:
                setattr(lead, field, data.get(field)) # Usa setattr para atribuição dinâmica
                
        # Define o status, usando 'novo' como padrão se não fornecido.
        lead.status = data.get('status', 'novo')
        
        # Atribui o usuario_id, tratando possíveis erros de tipo.
        user_id = data.get('usuario_id')
        if user_id is not None:
            try:
                lead.usuario_id = int(user_id) # Tenta converter para inteiro
            except (ValueError, TypeError):
                # Se não for um inteiro válido, loga um aviso e deixa como None (ou mantém o valor original se apropriado)
                current_app.logger.warning(f"Valor inválido para usuario_id recebido: {user_id}")
                lead.usuario_id = None # Ou decidir como tratar IDs inválidos
                
        # Nota: Este método não adiciona nem salva o lead no banco de dados.
        # Isso deve ser feito separadamente (ex: db.session.add(lead); db.session.commit()).
        return lead
    
    def __repr__(self):
        # Retorna uma representação textual do objeto Lead, útil para logs e depuração.
        return f'<Lead {self.id}: {self.nome} ({self.email})>'
