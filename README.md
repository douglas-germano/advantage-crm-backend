# Advantage CRM - Backend

Backend da aplicação Advantage CRM, desenvolvido com Flask para gerenciamento de leads, clientes, negócios e relacionamentos comerciais.

## Tecnologias Utilizadas

- Python 3.9+
- Flask
- SQLAlchemy (ORM)
- Flask-JWT-Extended (Autenticação)
- Flask-Migrate (Migrações de banco de dados)
- Flask-CORS (Integração com frontend)
- Gunicorn (Servidor WSGI para produção)

## Estrutura do Projeto

```
backend/
├── app/                      # Pacote principal da aplicação
│   ├── api/                  # Endpoints da API REST
│   │   ├── auth/             # Autenticação de usuários
│   │   ├── leads/            # Gerenciamento de leads
│   │   ├── customers/        # Gerenciamento de clientes
│   │   ├── deals/            # Gerenciamento de negócios
│   │   └── ...
│   ├── models/               # Modelos de dados SQLAlchemy
│   └── utils/                # Utilitários e helpers
├── migrations/               # Migrações do banco de dados
├── config.py                 # Configurações da aplicação
├── gunicorn_config.py        # Configuração do Gunicorn para produção
├── requirements.txt          # Dependências do projeto
├── run.py                    # Ponto de entrada para desenvolvimento
└── wsgi.py                   # Ponto de entrada para produção (Gunicorn)
```

## Instalação e Configuração

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd backend
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente (opcional):
```bash
# No Linux/Mac
export FLASK_APP=run.py
export FLASK_ENV=development

# No Windows
set FLASK_APP=run.py
set FLASK_ENV=development
```

5. Execute as migrações do banco de dados:
```bash
flask db upgrade
```

6. Inicialize o banco de dados (se necessário):
```bash
flask init-db
```

7. Inicie o servidor de desenvolvimento:
```bash
flask run
# ou
python -m flask run
```

## Usando Gunicorn para Produção

Para ambientes de produção, é recomendado usar o Gunicorn como servidor WSGI ao invés do servidor de desenvolvimento embutido do Flask.

### Iniciar com configurações padrão:

```bash
gunicorn -w 4 -b 0.0.0.0:5001 wsgi:app
```

### Iniciar com arquivo de configuração:

```bash
gunicorn -c gunicorn_config.py wsgi:app
```

### Opções comuns do Gunicorn:

- `-w` ou `--workers`: Número de processos worker
- `-b` ou `--bind`: Endereço de IP e porta para bindar o servidor
- `-D` ou `--daemon`: Rodar em background como um daemon
- `--access-logfile`: Arquivo de log de acesso
- `--error-logfile`: Arquivo de log de erros
- `--log-level`: Nível de log (debug, info, warning, error, critical)

### Configurações em Produção

Em um ambiente de produção, é recomendado usar o Gunicorn atrás de um servidor web como Nginx ou Apache, que podem lidar melhor com conexões estáticas, SSL, e balanceamento de carga.

Exemplo básico de configuração Nginx:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## API Endpoints

A API está disponível em `http://localhost:5001/api/` com os seguintes endpoints principais:

- `/api/auth/login` - Autenticação de usuários
- `/api/leads/` - Gerenciamento de leads
- `/api/customers/` - Gerenciamento de clientes 
- `/api/deals/` - Gerenciamento de negócios

Consulte a documentação completa da API para mais detalhes sobre endpoints disponíveis. 