# Documentação da API do Backend - Advantage CRM

Este documento descreve os endpoints da API RESTful do backend do Advantage CRM.

**Prefixo Base:** Todas as rotas da API estão sob o prefixo `/api`.

**Autenticação:** A maioria das rotas requer autenticação via JWT (JSON Web Token). O token deve ser enviado no cabeçalho `Authorization` como `Bearer <token>`.

**Formatos:** As requisições e respostas utilizam o formato JSON.

---

## 1. Autenticação (`/api/auth`)

Gerencia o login e registro de usuários.

*   **`POST /api/auth/login`**
    *   **Descrição:** Autentica um usuário com `username` e `password`.
    *   **Request Body:** `{ "username": "...", "password": "..." }`
    *   **Response (200 OK):** `{ "message": "Login realizado com sucesso", "user": { ... }, "access_token": "..." }`
    *   **Response (400 Bad Request):** Erro de validação nos dados de entrada.
    *   **Response (401 Unauthorized):** Credenciais inválidas.

*   **`POST /api/auth/register`**
    *   **Descrição:** Registra um novo usuário no sistema.
    *   **Request Body:** `{ "name": "...", "username": "...", "email": "...", "password": "...", "role": "vendedor" (opcional) }`
    *   **Response (201 Created):** `{ "message": "Usuário registrado com sucesso!", "user": { ... }, "access_token": "..." }`
    *   **Response (400 Bad Request):** Erro de validação ou `username`/`email` já existentes.

---

## 2. Usuários (`/api/users`)

Gerencia os usuários do sistema. Requer autenticação.

*   **`GET /api/users/me`**
    *   **Descrição:** Obtém as informações do usuário autenticado atualmente.
    *   **Response (200 OK):** `{ "id": ..., "name": "...", "username": "...", "email": "...", "role": "...", "created_at": "..." }`

*   **`PUT /api/users/me`**
    *   **Descrição:** Atualiza as informações do usuário autenticado (nome, username, email).
    *   **Request Body:** `{ "name": "...", "username": "...", "email": "..." }` (campos opcionais)
    *   **Response (200 OK):** Objeto do usuário atualizado.
    *   **Response (400 Bad Request):** Erro de validação ou `username`/`email` já existente.

*   **`GET /api/users/`**
    *   **Descrição:** Lista todos os usuários do sistema. **(Requer Role Admin)**
    *   **Response (200 OK):** `{ "users": [ { ... }, { ... } ] }`
    *   **Response (403 Forbidden):** Se o usuário não for admin.

*   **`POST /api/users/`**
    *   **Descrição:** Cria um novo usuário. **(Requer Role Admin)**
    *   **Request Body:** `{ "name": "...", "username": "...", "email": "...", "password": "...", "role": "..." }`
    *   **Response (201 Created):** Objeto do usuário criado.
    *   **Response (400 Bad Request):** Erro de validação ou `username`/`email` já existente.
    *   **Response (403 Forbidden):** Se o usuário não for admin.

*   **`GET /api/users/<int:id>`**
    *   **Descrição:** Obtém os detalhes de um usuário específico pelo ID. (Admin pode ver qualquer um, usuário normal só a si mesmo).
    *   **Response (200 OK):** Objeto do usuário.
    *   **Response (403 Forbidden):** Se tentando acessar outro usuário sem ser admin.
    *   **Response (404 Not Found):** Usuário não encontrado.

*   **`PUT /api/users/<int:id>`**
    *   **Descrição:** Atualiza um usuário específico pelo ID. (Admin pode editar qualquer um, usuário normal só a si mesmo). Admin pode alterar o `role`.
    *   **Request Body:** `{ "name": "...", "username": "...", "email": "...", "role": "..." (opcional, admin only) }` (campos opcionais)
    *   **Response (200 OK):** Objeto do usuário atualizado.
    *   **Response (400 Bad Request):** Erro de validação ou `username`/`email` já existente.
    *   **Response (403 Forbidden):** Se tentando editar outro usuário sem ser admin.
    *   **Response (404 Not Found):** Usuário não encontrado.

*   **`PUT /api/users/<int:id>/password`**
    *   **Descrição:** Atualiza a senha de um usuário específico. (Admin pode alterar qualquer senha, usuário normal só a própria, requerendo `current_password`).
    *   **Request Body (Self Update):** `{ "current_password": "...", "new_password": "..." }`
    *   **Request Body (Admin Update):** `{ "new_password": "..." }`
    *   **Response (200 OK):** `{ "message": "Senha atualizada com sucesso" }`
    *   **Response (400 Bad Request):** Erro de validação.
    *   **Response (401 Unauthorized):** Senha atual incorreta (para self update).
    *   **Response (403 Forbidden):** Se tentando alterar senha de outro usuário sem ser admin.
    *   **Response (404 Not Found):** Usuário não encontrado.

*   **`DELETE /api/users/<int:id>`**
    *   **Descrição:** Exclui um usuário específico pelo ID. **(Requer Role Admin)**. Não permite auto-exclusão.
    *   **Response (200 OK):** `{ "message": "Usuário excluído com sucesso" }`
    *   **Response (400 Bad Request):** Tentativa de auto-exclusão.
    *   **Response (403 Forbidden):** Se o usuário não for admin.
    *   **Response (404 Not Found):** Usuário não encontrado.

---

## 3. Leads (`/api/leads`)

Gerencia os leads (potenciais clientes). Requer autenticação.

*   **`GET /api/leads/`**
    *   **Descrição:** Lista leads com paginação e filtros.
    *   **Query Params:** `page`, `per_page`, `nome`, `email`, `empresa`, `status`, `origem`.
    *   **Response (200 OK):** `{ "items": [ { ... } ], "total": ..., "pages": ..., "page": ..., "per_page": ... }`

*   **`POST /api/leads/`**
    *   **Descrição:** Cria um novo lead. `usuario_id` é atribuído ao usuário autenticado.
    *   **Request Body:** `{ "nome": "...", "email": "...", "telefone": "...", "empresa": "...", "cargo": "...", "interesse": "...", "origem": "...", "status": "...", "observacoes": "..." }` (campos obrigatórios: nome, email)
    *   **Response (201 Created):** Objeto do lead criado.

*   **`GET /api/leads/<int:id>`**
    *   **Descrição:** Obtém os detalhes de um lead específico.
    *   **Response (200 OK):** Objeto do lead.
    *   **Response (404 Not Found):** Lead não encontrado.

*   **`PUT /api/leads/<int:id>`**
    *   **Descrição:** Atualiza um lead existente.
    *   **Request Body:** Campos do lead a serem atualizados (parcial permitido).
    *   **Response (200 OK):** Objeto do lead atualizado.
    *   **Response (404 Not Found):** Lead não encontrado.

*   **`DELETE /api/leads/<int:id>`**
    *   **Descrição:** Exclui um lead específico.
    *   **Response (200 OK):** `{ "message": "Lead excluído com sucesso" }`
    *   **Response (404 Not Found):** Lead não encontrado.

*   **`GET /api/leads/status`**
    *   **Descrição:** Obtém a lista de opções de status válidas para leads.
    *   **Response (200 OK):** `[ {"value": "novo", "label": "Novo"}, ... ]`

*   **`GET /api/leads/origem`**
    *   **Descrição:** Obtém a lista de opções de origem válidas para leads.
    *   **Response (200 OK):** `[ {"value": "site", "label": "Site"}, ... ]`

---

## 4. Clientes (`/api/customers`)

Gerencia os clientes. Requer autenticação.

*   **`GET /api/customers/`**
    *   **Descrição:** Lista clientes com filtros opcionais.
    *   **Query Params:** `status`, `assigned_to`, `search` (busca em nome, email, empresa).
    *   **Response (200 OK):** `{ "customers": [ { ... } ] }`

*   **`POST /api/customers/`**
    *   **Descrição:** Cria um novo cliente. Pode incluir `custom_fields` no formato `{ field_id: value }`.
    *   **Request Body:** `{ "name": "...", "email": "...", ..., "custom_fields": { 1: "Valor A", 2: "Valor B" } }`
    *   **Response (201 Created):** `{ "message": "Cliente criado com sucesso", "customer": { ... } }`

*   **`GET /api/customers/<int:customer_id>`**
    *   **Descrição:** Obtém os detalhes de um cliente específico.
    *   **Response (200 OK):** `{ "customer": { ... } }` (inclui campos personalizados)
    *   **Response (404 Not Found):** Cliente não encontrado.

*   **`PUT /api/customers/<int:customer_id>`**
    *   **Descrição:** Atualiza um cliente existente. Pode incluir `custom_fields`.
    *   **Request Body:** Campos do cliente a serem atualizados (parcial permitido).
    *   **Response (200 OK):** `{ "message": "Cliente atualizado com sucesso", "customer": { ... } }`
    *   **Response (404 Not Found):** Cliente não encontrado.

*   **`DELETE /api/customers/<int:customer_id>`**
    *   **Descrição:** Exclui um cliente específico. (Requer role Admin ou ser o usuário responsável).
    *   **Response (200 OK):** `{ "message": "Cliente removido com sucesso" }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Cliente não encontrado.

---

## 5. Negócios (`/api/deals`)

Gerencia os negócios/oportunidades de venda. Requer autenticação.

*   **`GET /api/deals/`**
    *   **Descrição:** Lista negócios com paginação e filtros.
    *   **Query Params:** `page`, `per_page`, `pipeline_stage_id`, `title`, `status`.
    *   **Response (200 OK):** `{ "items": [ { ... } ], "pagination": { ... } }` (inclui detalhes do estágio, lead e usuário)

*   **`POST /api/deals/`**
    *   **Descrição:** Cria um novo negócio. `usuario_id` é atribuído ao usuário autenticado.
    *   **Request Body:** `{ "title": "...", "value": ..., "pipeline_stage_id": ..., ... }` (campos obrigatórios: title, pipeline_stage_id)
    *   **Response (201 Created):** Objeto do negócio criado.
    *   **Response (400 Bad Request):** Erro de validação ou `pipeline_stage_id` inválido.

*   **`GET /api/deals/<int:id>`**
    *   **Descrição:** Obtém os detalhes de um negócio específico.
    *   **Response (200 OK):** Objeto do negócio.
    *   **Response (404 Not Found):** Negócio não encontrado.

*   **`PUT /api/deals/<int:id>`**
    *   **Descrição:** Atualiza um negócio existente.
    *   **Request Body:** Campos do negócio a serem atualizados (parcial permitido).
    *   **Response (200 OK):** Objeto do negócio atualizado.
    *   **Response (400 Bad Request):** Erro de validação ou `pipeline_stage_id` inválido (se fornecido).
    *   **Response (404 Not Found):** Negócio não encontrado.

*   **`DELETE /api/deals/<int:id>`**
    *   **Descrição:** Exclui um negócio específico.
    *   **Response (200 OK):** `{ "message": "Deal deleted successfully" }`
    *   **Response (404 Not Found):** Negócio não encontrado.

*   **`PUT /api/deals/<int:id>/move`** (ou `/api/deals/<int:id>/stage`)
    *   **Descrição:** Move um negócio para um estágio diferente do pipeline.
    *   **Request Body:** `{ "stageId": <new_stage_id> }` ou `{ "pipeline_stage_id": <new_stage_id> }`
    *   **Response (200 OK):** Objeto do negócio atualizado com o novo estágio.
    *   **Response (400 Bad Request):** ID do estágio ausente ou inválido.
    *   **Response (404 Not Found):** Negócio ou Estágio não encontrado.

---

## 6. Pipelines (`/api/pipeline`)

Gerencia os pipelines de venda e seus estágios. Requer autenticação.

*   **`GET /api/pipeline/`**
    *   **Descrição:** Lista todos os pipelines definidos.
    *   **Response (200 OK):** `[ { "id": ..., "name": "...", ... }, ... ]`

*   **`POST /api/pipeline/`**
    *   **Descrição:** Cria um novo pipeline. Cria automaticamente os estágios padrão para ele.
    *   **Request Body:** `{ "name": "...", "description": "..." (opcional) }`
    *   **Response (201 Created):** Objeto do pipeline criado (sem os estágios).
    *   **Response (409 Conflict):** Pipeline com o mesmo nome já existe.

*   **`GET /api/pipeline/<int:id>/stages`**
    *   **Descrição:** Obtém todos os estágios de um pipeline específico, ordenados.
    *   **Response (200 OK):** `[ { "id": ..., "name": "...", "order": ..., ... }, ... ]`
    *   **Response (404 Not Found):** Pipeline não encontrado.

*   **`GET /api/pipeline/default`**
    *   **Descrição:** Obtém os detalhes do pipeline marcado como padrão.
    *   **Response (200 OK):** Objeto do pipeline padrão.
    *   **Response (404 Not Found):** Nenhum pipeline padrão encontrado.

*(Nota: Rotas para CRUD de Pipeline Stages individuais podem estar comentadas no código (`pipeline/routes.py`) e exigiriam privilégios de admin se ativadas).*

---

## 7. Campos Personalizados (`/api/custom-fields`)

Gerencia a definição dos campos personalizados. Requer autenticação.

*   **`GET /api/custom-fields/`**
    *   **Descrição:** Lista os campos personalizados definidos.
    *   **Query Params:** `show_all=true` (para incluir campos inativos). Padrão: mostra apenas ativos.
    *   **Response (200 OK):** `{ "custom_fields": [ { ... } ] }`

*   **`POST /api/custom-fields/`**
    *   **Descrição:** Cria um novo campo personalizado. **(Requer Role Admin)**
    *   **Request Body:** `{ "name": "...", "field_type": "...", "required": ..., "options": [...] (se tipo select), "active": ... }`
    *   **Response (201 Created):** `{ "message": "...", "custom_field": { ... } }`
    *   **Response (400 Bad Request):** Erro de validação ou nome já existente.
    *   **Response (403 Forbidden):** Se o usuário não for admin.

*   **`GET /api/custom-fields/<int:field_id>`**
    *   **Descrição:** Obtém os detalhes de um campo personalizado.
    *   **Response (200 OK):** `{ "custom_field": { ... } }`
    *   **Response (404 Not Found):** Campo não encontrado.

*   **`PUT /api/custom-fields/<int:field_id>`**
    *   **Descrição:** Atualiza um campo personalizado. **(Requer Role Admin)**
    *   **Request Body:** Campos a serem atualizados (parcial permitido).
    *   **Response (200 OK):** `{ "message": "...", "custom_field": { ... } }`
    *   **Response (400 Bad Request):** Erro de validação ou nome já existente.
    *   **Response (403 Forbidden):** Se o usuário não for admin.
    *   **Response (404 Not Found):** Campo não encontrado.

*   **`DELETE /api/custom-fields/<int:field_id>`**
    *   **Descrição:** Remove um campo personalizado se não estiver em uso, caso contrário, marca como inativo. **(Requer Role Admin)**
    *   **Response (200 OK):** Mensagem indicando remoção ou inativação.
    *   **Response (403 Forbidden):** Se o usuário não for admin.
    *   **Response (404 Not Found):** Campo não encontrado.

---

## 8. Tarefas (`/api/tasks`)

Gerencia tarefas e atividades. Requer autenticação.

*   **`GET /api/tasks/`**
    *   **Descrição:** Lista tarefas com paginação e filtros.
    *   **Query Params:** `page`, `per_page`, `status`, `priority`, `assigned_to`, `entity_type`, `entity_id`, `task_type`, `search` (busca em título, descrição).
    *   **Response (200 OK):** `{ "tasks": [ { ... } ], "pagination": { ... } }`

*   **`POST /api/tasks/`**
    *   **Descrição:** Cria uma nova tarefa.
    *   **Request Body:** `{ "title": "...", "description": "...", "due_date": "...", ... }`
    *   **Response (201 Created):** `{ "message": "Tarefa criada com sucesso", "task": { ... } }`

*   **`GET /api/tasks/<int:task_id>`**
    *   **Descrição:** Obtém os detalhes de uma tarefa específica.
    *   **Response (200 OK):** `{ "task": { ... } }`
    *   **Response (404 Not Found):** Tarefa não encontrada.

*   **`PUT /api/tasks/<int:task_id>`**
    *   **Descrição:** Atualiza uma tarefa existente.
    *   **Request Body:** Campos da tarefa a serem atualizados (parcial permitido).
    *   **Response (200 OK):** `{ "message": "Tarefa atualizada com sucesso", "task": { ... } }`
    *   **Response (404 Not Found):** Tarefa não encontrada.

*   **`DELETE /api/tasks/<int:task_id>`**
    *   **Descrição:** Exclui uma tarefa específica. (Requer role Admin ou ser o usuário responsável).
    *   **Response (200 OK):** `{ "message": "Tarefa removida com sucesso" }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Tarefa não encontrada.

*   **`POST /api/tasks/<int:task_id>/complete`**
    *   **Descrição:** Marca uma tarefa como concluída.
    *   **Response (200 OK):** `{ "message": "Tarefa marcada como concluída", "task": { ... } }`
    *   **Response (400 Bad Request):** Tarefa já concluída.
    *   **Response (404 Not Found):** Tarefa não encontrada.

*   **`POST /api/tasks/<int:task_id>/reopen`**
    *   **Descrição:** Reabre uma tarefa concluída ou cancelada.
    *   **Response (200 OK):** `{ "message": "Tarefa reaberta com sucesso", "task": { ... } }`
    *   **Response (400 Bad Request):** Tarefa não está em estado que permite reabertura.
    *   **Response (404 Not Found):** Tarefa não encontrada.

---

## 9. Comunicações (`/api/communications`)

Gerencia registros de interações (emails, ligações, etc.). Requer autenticação.

*   **`GET /api/communications/`**
    *   **Descrição:** Lista comunicações com paginação e filtros.
    *   **Query Params:** `page`, `per_page`, `comm_type`, `entity_type`, `entity_id`, `user_id`, `outcome`, `search` (busca em assunto, conteúdo), `start_date`, `end_date`.
    *   **Response (200 OK):** `{ "communications": [ { ... } ], "pagination": { ... } }`

*   **`POST /api/communications/`**
    *   **Descrição:** Registra uma nova comunicação. Pode incluir upload de arquivos anexos via `multipart/form-data` (campo `files`). `user_id` padrão é o usuário autenticado.
    *   **Request Body (JSON ou Form Data):** `{ "comm_type": "...", "subject": "...", "content": "...", ... }`
    *   **Response (201 Created):** `{ "message": "...", "communication": { ... }, "attachments": [ { ... } ] }`

*   **`GET /api/communications/<int:comm_id>`**
    *   **Descrição:** Obtém os detalhes de uma comunicação específica.
    *   **Response (200 OK):** `{ "communication": { ... } }` (inclui lista de anexos)
    *   **Response (404 Not Found):** Comunicação não encontrada.

*   **`PUT /api/communications/<int:comm_id>`**
    *   **Descrição:** Atualiza uma comunicação existente. (Requer role Admin ou ser o usuário que registrou).
    *   **Request Body:** Campos da comunicação a serem atualizados (parcial permitido).
    *   **Response (200 OK):** `{ "message": "...", "communication": { ... } }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Comunicação não encontrada.

*   **`DELETE /api/communications/<int:comm_id>`**
    *   **Descrição:** Exclui uma comunicação e seus anexos (arquivos físicos incluídos). (Requer role Admin ou ser o usuário que registrou).
    *   **Response (200 OK):** `{ "message": "Comunicação removida com sucesso" }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Comunicação não encontrada.

---

## 10. Workflows (`/api/workflows`)

Gerencia os fluxos de trabalho de automação. Requer autenticação.

*   **`GET /api/workflows/`**
    *   **Descrição:** Lista workflows com filtros opcionais.
    *   **Query Params:** `entity_type`, `is_active`, `trigger_type`, `search` (busca em nome, descrição).
    *   **Response (200 OK):** `{ "workflows": [ { ... } ] }` (inclui ações)

*   **`POST /api/workflows/`**
    *   **Descrição:** Cria um novo workflow com suas ações. `created_by` é atribuído ao usuário autenticado.
    *   **Request Body:** `{ "name": "...", "entity_type": "...", "trigger_type": "...", "trigger_data": { ... }, "actions": [ { "sequence": ..., "action_type": "...", "action_data": { ... }, "condition": { ... } } ], ... }`
    *   **Response (201 Created):** `{ "message": "...", "workflow": { ... } }`

*   **`GET /api/workflows/<int:workflow_id>`**
    *   **Descrição:** Obtém os detalhes de um workflow específico, incluindo suas ações.
    *   **Response (200 OK):** `{ "workflow": { ... } }`
    *   **Response (404 Not Found):** Workflow não encontrado.

*   **`PUT /api/workflows/<int:workflow_id>`**
    *   **Descrição:** Atualiza um workflow existente, incluindo suas ações (se fornecido, substitui todas as ações existentes). (Requer role Admin ou ser o criador).
    *   **Request Body:** Campos do workflow a serem atualizados (parcial permitido). `actions` é opcional.
    *   **Response (200 OK):** `{ "message": "...", "workflow": { ... } }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Workflow não encontrado.

*   **`DELETE /api/workflows/<int:workflow_id>`**
    *   **Descrição:** Exclui um workflow e suas ações. (Requer role Admin ou ser o criador).
    *   **Response (200 OK):** `{ "message": "Workflow removido com sucesso" }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Workflow não encontrado.

*   **`POST /api/workflows/<int:workflow_id>/toggle`**
    *   **Descrição:** Ativa ou desativa um workflow. (Requer role Admin ou ser o criador).
    *   **Response (200 OK):** `{ "message": "Workflow ativado/desativado...", "workflow": { ... } }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Workflow não encontrado.

---

## 11. Documentos (`/api/documents`)

Gerencia o upload, download e metadados de documentos. Requer autenticação (exceto download público/com código).

*   **`GET /api/documents/`**
    *   **Descrição:** Lista documentos com paginação e filtros.
    *   **Query Params:** `page`, `per_page`, `entity_type`, `entity_id`, `communication_id`, `is_public`, `file_type`, `uploaded_by`, `search` (busca em título, descrição, nome original).
    *   **Response (200 OK):** `{ "documents": [ { ... } ], "pagination": { ... } }` (sem conteúdo do arquivo)

*   **`POST /api/documents/`**
    *   **Descrição:** Faz upload de um novo documento. Usa `multipart/form-data`. Campo do arquivo: `file`. Outros metadados via campos de formulário.
    *   **Form Data:** `file` (arquivo), `title`, `description`, `entity_type`, `entity_id`, `communication_id`, `is_public`, `access_code`, `use_supabase` (true/false), `bucket_name` (opcional).
    *   **Response (201 Created):** `{ "message": "...", "document": { ... }, "storage": "...", "public_url": "..." (se Supabase) }`

*   **`GET /api/documents/<int:document_id>`**
    *   **Descrição:** Obtém os metadados de um documento. Acesso permitido para documentos públicos ou com `access_code` válido na query param (se não autenticado).
    *   **Query Params:** `access_code` (opcional), `include_content=true` (opcional, para arquivos pequenos).
    *   **Response (200 OK):** `{ "document": { ... } }`
    *   **Response (403 Forbidden):** Acesso negado (se privado e sem token/código válido).
    *   **Response (404 Not Found):** Documento não encontrado.

*   **`GET /api/documents/<int:document_id>/download`**
    *   **Descrição:** Baixa o conteúdo do arquivo. Acesso permitido para documentos públicos ou com `access_code` válido na query param (se não autenticado). Pode redirecionar para URL do Supabase.
    *   **Query Params:** `access_code` (opcional), `redirect=true` (opcional, para redirecionar se Supabase).
    *   **Response (200 OK):** Conteúdo do arquivo (`Content-Type` e `Content-Disposition` definidos).
    *   **Response (302 Found):** Redireciona para a URL pública do Supabase (se `redirect=true`).
    *   **Response (403 Forbidden):** Acesso negado.
    *   **Response (404 Not Found):** Documento não encontrado.

*   **`PUT /api/documents/<int:document_id>`**
    *   **Descrição:** Atualiza os metadados de um documento. (Requer role Admin ou ser o uploader).
    *   **Request Body:** `{ "title": "...", "description": "...", "entity_type": "...", "entity_id": ..., "is_public": ..., "access_code": "..." }` (campos opcionais)
    *   **Response (200 OK):** `{ "message": "...", "document": { ... } }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Documento não encontrado.

*   **`DELETE /api/documents/<int:document_id>`**
    *   **Descrição:** Exclui um documento (registro no DB e arquivo físico/Supabase). (Requer role Admin ou ser o uploader).
    *   **Response (200 OK):** `{ "message": "Documento removido com sucesso" }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Documento não encontrado.

*   **`POST /api/documents/share/<int:document_id>`**
    *   **Descrição:** Configura o compartilhamento de um documento (público ou com código de acesso). (Requer role Admin ou ser o uploader).
    *   **Request Body:** `{ "is_public": true/false }` (opcional, default: false).
    *   **Response (200 OK):** `{ "message": "...", "document": { ... }, "is_public": ..., "access_code": "...", "share_url": "..." }`
    *   **Response (403 Forbidden):** Permissão negada.
    *   **Response (404 Not Found):** Documento não encontrado.

*   **`POST /api/documents/migrate-to-supabase`**
    *   **Descrição:** Migra documentos do armazenamento local para o Supabase Storage. **(Requer Role Admin)**.
    *   **Request Body:** `{ "document_ids": [...], "bucket_name": "...", "delete_local": true/false, "limit": ... }` (todos opcionais; sem `document_ids` tenta migrar todos os não migrados, respeitando `limit`).
    *   **Response (200 OK):** `{ "message": "...", "results": { "migrated": ..., "failed": ..., "details": [ ... ] } }`
    *   **Response (403 Forbidden):** Se o usuário não for admin.

---

## 12. Health Check (`/api/health`)

Verifica a saúde da aplicação. Não requer autenticação.

*   **`GET /api/health`**
    *   **Descrição:** Retorna o status da API.
    *   **Response (200 OK):** `{ "status": "ok", "version": "1.0.0" }`

--- 