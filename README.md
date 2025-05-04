# Advantage CRM - Backend

Backend da aplicação Advantage CRM, desenvolvido utilizando Flask. Este sistema fornece a API RESTful para gerenciar leads, clientes, negócios, tarefas, comunicações e outras funcionalidades essenciais de um CRM.

## Funcionalidades Principais

*   Autenticação de usuários baseada em JWT (JSON Web Tokens).
*   Gerenciamento de Usuários com diferentes papéis (admin, vendedor, etc.).
*   CRUD completo para Leads, Clientes (Customers), Negócios (Deals).
*   Gerenciamento de Pipelines de Venda e seus Estágios.
*   Criação e acompanhamento de Tarefas (Tasks).
*   Registro de Comunicações (emails, ligações, reuniões).
*   Suporte a Campos Personalizados (Custom Fields) para Clientes.
*   Gerenciamento de Documentos com opção de upload para Supabase Storage.
*   Sistema básico de Workflows (gatilhos e ações).
*   Endpoint de Health Check.

## Tecnologias Utilizadas

*   **Linguagem:** Python 3.9+
*   **Framework:** Flask
*   **ORM:** SQLAlchemy
*   **Banco de Dados:** PostgreSQL (via Supabase ou localmente)
*   **Migrações:** Flask-Migrate (baseado no Alembic)
*   **Autenticação:** Flask-JWT-Extended
*   **Validação:** Marshmallow
*   **Servidor WSGI (Produção):** Gunicorn
*   **CORS:** Flask-CORS
*   **Variáveis de Ambiente:** python-dotenv
*   **Integração Cloud (Opcional):** Supabase (Banco de Dados e Storage)

## Estrutura do Projeto

```
backend/
├── app/                      # Pacote principal da aplicação Flask
│   ├── api/                  # Módulos da API REST (Blueprints)
│   │   ├── auth/             #   - Autenticação (login, registro)
│   │   ├── communications/   #   - Comunicações
│   │   ├── custom_fields/    #   - Campos Personalizados
│   │   ├── customers/        #   - Clientes
│   │   ├── deals/            #   - Negócios
│   │   ├── documents/        #   - Documentos
│   │   ├── leads/            #   - Leads
│   │   ├── pipeline/         #   - Pipelines e Estágios
│   │   ├── tasks/            #   - Tarefas
│   │   ├── users/            #   - Usuários
│   │   └── workflows/        #   - Workflows
│   │   └── __init__.py       #   - Registro dos blueprints da API
│   ├── models/               # Modelos de dados SQLAlchemy (definição das tabelas)
│   │   ├── __init__.py
│   │   ├── communication.py
│   │   ├── custom_field.py
│   │   ├── customer.py
│   │   ├── deal.py
│   │   ├── document.py
│   │   ├── lead.py
│   │   ├── pipeline.py
│   │   ├── task.py
│   │   ├── user.py
│   │   └── workflow.py
│   ├── utils/                # Utilitários e helpers (ex: cliente Supabase)
│   │   ├── __init__.py
│   │   └── supabase_client.py
│   └── __init__.py           # Factory da aplicação Flask (create_app)
├── migrations/               # Arquivos de migração gerados pelo Flask-Migrate
├── uploads/                  # Diretório padrão para uploads locais (se não usar Supabase)
├── .env.example              # Arquivo de exemplo para variáveis de ambiente
├── .flaskenv                 # Configurações para o comando `flask` (FLASK_APP, FLASK_ENV)
├── .gitignore                # Arquivos e diretórios ignorados pelo Git
├── config.py                 # Classes de configuração (Development, Production, Testing)
├── gunicorn_config.py        # Configuração do Gunicorn para produção
├── requirements.txt          # Dependências Python do projeto
├── run.py                    # Ponto de entrada para execução em desenvolvimento (`flask run`)
├── wsgi.py                   # Ponto de entrada para servidores WSGI como Gunicorn
└── README.md                 # Este arquivo
```

## Configuração do Ambiente de Desenvolvimento

Siga estes passos para configurar e rodar o backend localmente:

1.  **Clone o Repositório:**
    ```bash
    git clone <url-do-seu-repositorio>
    cd backend
    ```

2.  **Crie e Ative um Ambiente Virtual:**
    ```bash
    python -m venv venv
    # Linux/macOS
    source venv/bin/activate
    # Windows (cmd/powershell)
    .\venv\Scripts\activate
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    *   Copie o arquivo de exemplo:
        ```bash
        cp .env.example .env
        ```
    *   Edite o arquivo `.env` recém-criado e preencha as variáveis necessárias. Consulte a seção [Variáveis de Ambiente](#variáveis-de-ambiente) abaixo para detalhes. **É crucial definir `SECRET_KEY`, `JWT_SECRET_KEY` e as URLs do banco de dados/Supabase.**

5.  **Configure o Arquivo `.flaskenv`:**
    *   Certifique-se que o arquivo `.flaskenv` existe com o seguinte conteúdo (ele informa ao comando `flask` como carregar a aplicação):
        ```
        FLASK_APP=run.py
        FLASK_ENV=development
        ```
    *   `FLASK_ENV=development` habilita o modo debug e recarregamento automático. **Não use em produção.**

6.  **Configure o Banco de Dados:**
    *   **Aplique as Migrações:** Este comando cria ou atualiza as tabelas no banco de dados definido na sua configuração (`DATABASE_URL` ou `SUPABASE_DATABASE_URL`).
        ```bash
        flask db upgrade
        ```
    *   **(Opcional) Inicialize Dados Padrão:** Este comando (definido em `app/__init__.py`) pode ser usado para criar dados iniciais, como o usuário administrador padrão.
        ```bash
        flask init-db
        ```
        Verifique o output para a senha padrão do admin ou configure `DEFAULT_ADMIN_PASSWORD` no `.env`.

## Executando a Aplicação

### Modo de Desenvolvimento

Com o ambiente virtual ativado e as configurações feitas, inicie o servidor de desenvolvimento Flask:

```bash
flask run
```

A aplicação estará disponível, por padrão, em `http://localhost:5001` (ou na porta definida pela variável de ambiente `PORT`).

### Modo de Produção (Gunicorn)

Para produção, utilize o Gunicorn. Certifique-se que `FLASK_ENV` **não** esteja definido como `development`.

*   **Comando Básico:** (Ajuste workers e porta conforme necessário)
    ```bash
    gunicorn --workers 4 --bind 0.0.0.0:5001 wsgi:app
    ```
*   **Usando Arquivo de Configuração:** (Recomendado)
    ```bash
    gunicorn -c gunicorn_config.py wsgi:app
    ```
    O arquivo `gunicorn_config.py` permite configurações mais detalhadas (logging, timeouts, etc.).

**Importante:** Em produção, rode o Gunicorn por trás de um proxy reverso como Nginx ou Apache para melhor performance, segurança (SSL) e gerenciamento de conexões.

## Migrações de Banco de Dados (Flask-Migrate/Alembic)

Quando você modificar os modelos em `app/models/`, precisará gerar e aplicar migrações:

1.  **Gerar a Migração:** Detecta as mudanças nos modelos e cria um script de migração.
    ```bash
    flask db migrate -m "Descrição da sua mudança nos modelos"
    ```
2.  **Aplicar a Migração:** Executa o script de migração no banco de dados.
    ```bash
    flask db upgrade
    ```
3.  **Reverter (se necessário):** Desfaz a última migração.
    ```bash
    flask db downgrade
    ```

## Endpoints da API

A API RESTful está disponível sob o prefixo `/api`. Os principais grupos de endpoints incluem:

*   `/api/auth/`: Login (`/login`) e Registro (`/register`).
*   `/api/users/`: Gerenciamento de usuários (CRUD, obter usuário logado `/me`).
*   `/api/leads/`: CRUD para Leads.
*   `/api/customers/`: CRUD para Clientes.
*   `/api/deals/`: CRUD para Negócios.
*   `/api/pipeline/`: Gerenciamento de Pipelines e Estágios.
*   `/api/tasks/`: CRUD para Tarefas.
*   `/api/communications/`: CRUD para Comunicações.
*   `/api/custom-fields/`: CRUD para definição de Campos Personalizados.
*   `/api/documents/`: Upload e gerenciamento de documentos.
*   `/api/workflows/`: CRUD para Workflows.
*   `/api/health`: Endpoint de verificação de saúde da API.

Consulte o código nos respectivos diretórios em `app/api/` para detalhes sobre rotas específicas, métodos HTTP e parâmetros esperados.

## Variáveis de Ambiente (`.env`)

As seguintes variáveis de ambiente são usadas para configurar a aplicação. Crie um arquivo `.env` na raiz do diretório `backend/` com base no `.env.example`.

*   **`FLASK_ENV`**: (Definido em `.flaskenv` geralmente) Ambiente de execução (`development`, `production`, `testing`).
*   **`SECRET_KEY`**: Chave secreta forte e única para segurança do Flask (sessões, cookies, etc.). **Obrigatório.**
*   **`JWT_SECRET_KEY`**: Chave secreta forte e única para assinar os tokens JWT. **Obrigatório.**
*   **`DATABASE_URL`**: URL de conexão completa para o banco de dados PostgreSQL (usada em produção se `SUPABASE_DATABASE_URL` não estiver definida). Formato: `postgresql+psycopg://user:password@host:port/dbname`. **Obrigatório para produção sem Supabase.**
*   **`SUPABASE_URL`**: URL do seu projeto Supabase (para API e Storage). *Opcional, necessário se usar Supabase.*
*   **`SUPABASE_KEY`**: Chave `anon` ou `service_role` do seu projeto Supabase. *Opcional, necessário se usar Supabase.*
*   **`SUPABASE_DATABASE_URL`**: URL de conexão direta ao banco de dados Supabase (geralmente encontrada nas configurações do Supabase). Substitui `DATABASE_URL` se definida. *Opcional, recomendado se usar DB Supabase.*
*   **`DEFAULT_ADMIN_EMAIL`**: Email padrão para o usuário admin criado pelo `flask init-db`. (Padrão: `admin@example.com`)
*   **`DEFAULT_ADMIN_PASSWORD`**: Senha padrão para o usuário admin criado pelo `flask init-db`. (Padrão: `admin123` - **altamente recomendado alterar!**)
*   **`UPLOAD_FOLDER`**: Caminho do diretório para uploads locais (se não usar Supabase Storage). (Padrão: `backend/uploads`)
*   **`BASE_URL`**: URL base da aplicação (usada para gerar links, etc.). (Padrão: `http://localhost:5001`)
*   **`PORT`**: Porta para o servidor de desenvolvimento Flask. (Padrão: `5001`)
*   **`HOST`**: Host para o servidor de desenvolvimento Flask. (Padrão: `0.0.0.0`)

Certifique-se de manter seu arquivo `.env` seguro e fora do controle de versão (ele já está no `.gitignore`). 