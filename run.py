"""
Arquivo principal de execução da aplicação Flask CRM.

Este arquivo é responsável por criar a instância da aplicação e iniciar
o servidor web de desenvolvimento.
Tarefas de inicialização (como criação de DB) devem ser feitas via Flask CLI.
"""

from app import create_app
import os
import logging

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar a aplicação Flask
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """
    Configura o contexto do shell Flask para facilitar o desenvolvimento.
    """
    # Mantém importações locais para evitar dependências circulares
    from app import db
    from app.models import User, Customer, CustomField, CustomFieldValue, Lead
    from app.models.pipeline import PipelineStage
    from app.models.deal import Deal
    
    # Novos modelos
    from app.models import Task, Communication, Workflow, WorkflowAction, Document
    
    return {
        'db': db, 
        'User': User, 
        'Customer': Customer, 
        'CustomField': CustomField,
        'CustomFieldValue': CustomFieldValue,
        'Lead': Lead,
        'PipelineStage': PipelineStage,
        'Deal': Deal,
        # Novos modelos
        'Task': Task,
        'Communication': Communication,
        'Workflow': Workflow,
        'WorkflowAction': WorkflowAction,
        'Document': Document
    }


if __name__ == '__main__':
    # Obter configuração da porta do servidor (padrão: 5001)
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Determinar modo de depuração
    debug_mode = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    
    # Log de informações de inicialização
    logger.info(f"Iniciando servidor Flask em {host}:{port} (Debug: {debug_mode})")
    logger.info("Para inicializar o banco de dados, execute: flask init-db")
    
    # Iniciar o servidor Flask
    app.run(host=host, port=port, debug=debug_mode)
