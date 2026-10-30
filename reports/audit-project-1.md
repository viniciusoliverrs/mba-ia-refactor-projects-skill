```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1
Domain:        E-commerce API (produtos, usuários, pedidos, relatórios de vendas)
Architecture:  Monolítica — 4 arquivos, sem separação real de camadas (models.py concentra SQL + regra de negócio)
Source files:  4 files analyzed (~780 LOC)
DB tables:     produtos, usuarios, pedidos, itens_pedido (SQLite, arquivo loja.db)
Entry point:   app.py
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:7-8, controllers.py:285-289
Description: `SECRET_KEY` fixa em 'minha-chave-super-secreta-123' e `DEBUG = True` no código; o endpoint `/health` devolve
`secret_key`, `db_path`, `debug` e `ambiente` no JSON público.
Impact: Qualquer pessoa obtém a chave de assinatura da aplicação e detalhes internos; segredo versionado no Git.
Recommendation: Mover para `config/settings.py` lendo variáveis de ambiente (PB-01) e remover segredos da resposta do `/health`.

### [CRITICAL] SQL Injection / Query por Concatenação (AP-02)
File: models.py:28, models.py:47-50, models.py:58-61, models.py:68, models.py:92, models.py:109-111, models.py:126-129, models.py:140, models.py:148-151, models.py:155-166, models.py:174, models.py:188-192, models.py:206, models.py:220-224, models.py:279-281, models.py:289-297
Description: Todas as queries são montadas com `"..." + str(id)` / `"'" + nome + "'"`; o login monta `WHERE email = '...' AND senha = '...'`
(bypass trivial com `' OR '1'='1`); a busca monta `LIKE '%" + termo + "%'`.
Impact: Leitura, alteração e destruição arbitrária do banco por qualquer cliente; bypass de autenticação.
Recommendation: Usar placeholders `?` com tuplas de parâmetros em todos os models (PB-02).

### [CRITICAL] God Module / Violação Total de Camadas (AP-03)
File: models.py:1-314, controllers.py:1-292, app.py:47-78
Description: `models.py` mistura SQL, mapeamento, regra de negócio (cálculo de pedido, desconto progressivo, estoque) de 4 domínios;
`app.py` e `controllers.py:264-292` executam SQL direto (`reset_database`, `executar_query`, `health_check`); `database.py` mistura
conexão, schema DDL e seed.
Impact: Impossível testar em isolamento; qualquer mudança afeta todos os domínios.
Recommendation: Separar em `models/`, `controllers/` e `routes/` por domínio, `database/` para conexão/schema (PB-03).

### [CRITICAL] Senhas em Texto Puro e Expostas (AP-04)
File: database.py:75-79, models.py:83, models.py:99, models.py:109-111, models.py:122-131
Description: Senhas são gravadas em texto puro (seed `admin123`, `123456`; `criar_usuario` grava `senha` crua); `GET /usuarios` e
`GET /usuarios/<id>` devolvem o campo `senha`; o login compara a senha dentro da query SQL.
Impact: Vazamento direto das credenciais de todos os usuários; qualquer comprometimento do banco expõe as senhas.
Recommendation: Hash com salt (`werkzeug.security`), nunca serializar a senha, verificar no código (PB-04).

### [CRITICAL] Endpoints Administrativos Perigosos Sem Autenticação (AP-05)
File: app.py:47-57, app.py:59-78, app.py:88
Description: `POST /admin/reset-db` apaga todas as tabelas e `POST /admin/query` executa SQL arbitrário recebido do cliente, ambos
sem autenticação; servidor sobe com `debug=True` e `host=0.0.0.0` (console Werkzeug exposto).
Impact: Qualquer cliente de rede destrói ou exfiltra todos os dados; debugger remoto = execução de código.
Recommendation: Remover `/admin/query`, proteger `/admin/reset-db` por token de admin de configuração, `debug` via ambiente (PB-05).

### [HIGH] Regra de Negócio Misturada ao Acesso a Dados / Notificações no Controller (AP-06)
File: models.py:133-169, models.py:256-273, controllers.py:208-210, controllers.py:247-250
Description: Cálculo de total/estoque do pedido e política de desconto estão em `models.py`; controller dispara "e-mail/SMS/push"
com `print` dentro do fluxo do pedido.
Impact: Regras de negócio não testáveis sem banco; efeitos colaterais acoplados ao handler HTTP.
Recommendation: Controllers concentram regras (`calcular_desconto`), models só persistem; notificações em service dedicado (PB-06, PB-15, PB-16).

### [HIGH] Estado Global Mutável da Conexão (AP-07)
File: database.py:4-11
Description: `db_connection` global compartilhado, criado preguiçosamente com `check_same_thread=False`; `db_path` fixo no módulo.
Impact: Condições de corrida entre threads, impossibilidade de injetar banco de teste, conexão nunca fechada.
Recommendation: Conexão por requisição (`flask.g`) com `teardown_appcontext`, caminho vindo de config (PB-07).

### [HIGH] Falta de Transação e Atomicidade no Pedido (AP-08)
File: models.py:133-169, controllers.py:249-250
Description: `criar_pedido` valida estoque, insere pedido, itens e baixa estoque em passos separados sem `BEGIN/ROLLBACK` e com
check-then-act não atômico; cancelar pedido apenas imprime "Devolver estoque" sem devolver.
Impact: Estoque negativo/oversell sob concorrência, pedidos parciais em caso de erro, estoque nunca restituído.
Recommendation: Transação explícita com rollback e `UPDATE ... WHERE estoque >= ?` (PB-08).

### [MEDIUM] N+1 Queries (AP-10)
File: models.py:171-201, models.py:203-233, models.py:139-146, models.py:154-166
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam, para cada pedido, uma query de itens (`cursor2`) e, para cada
item, uma query de produto (`cursor3`); `criar_pedido` consulta o mesmo produto duas vezes por item.
Impact: Número de queries cresce com pedidos × itens; degradação de performance.
Recommendation: Um `JOIN` único com agrupamento em memória (PB-10).

### [MEDIUM] Tratamento de Erros Duplicado e Inseguro (AP-11)
File: controllers.py:5-292 (todos os handlers), app.py:77-78
Description: Cada handler repete `try/except Exception as e: return jsonify({"erro": str(e)}), 500`, devolvendo a mensagem interna ao cliente.
Impact: Vazamento de detalhes internos, 20+ blocos duplicados, sem log estruturado.
Recommendation: Exceções de domínio + `errorhandler` central (PB-11).

### [MEDIUM] Validação de Entrada Ausente ou Duplicada (AP-12)
File: controllers.py:24-62, controllers.py:64-96, controllers.py:118-121, controllers.py:169-171, controllers.py:195-203, controllers.py:239-240
Description: Validação de produto copiada em `criar_produto` e `atualizar_produto` (com regras divergentes: update não valida nome/categoria);
`float(preco_min)` sem tratamento; `login`/`atualizar_status_pedido` chamam `dados.get` sem checar `None`; itens do pedido não validados
(`produto_id`/`quantidade`); tipos de `preco`/`estoque` não verificados.
Impact: Respostas 500 por entrada malformada; regras inconsistentes entre operações.
Recommendation: Funções de validação únicas no controller, lançando `ValidationError` (PB-12).

### [MEDIUM] Duplicação de Código (AP-13)
File: models.py:10-21, models.py:31-40, models.py:79-86, models.py:95-102, models.py:177-199, models.py:210-231, models.py:304-312
Description: O mapeamento `row → dict` de produto/usuário/pedido é copiado 7 vezes; os loops de pedidos são idênticos.
Impact: Mudança de schema exige editar vários lugares; risco de divergência.
Recommendation: Helpers `_row_to_*` e query única reaproveitada (PB-13).

### [LOW] Magic Numbers e Listas Hardcoded (AP-15)
File: models.py:256-262, controllers.py:47-54, controllers.py:242
Description: Faixas de desconto (`10000/0.1`, `5000/0.05`, `1000/0.02`), limites de nome (`2`, `200`), categorias e status válidos inline.
Impact: Regras de negócio escondidas e difíceis de alterar.
Recommendation: Constantes nomeadas em `config/constants.py` (PB-15).

### [LOW] Logging Amador com print (AP-16)
File: controllers.py:8, controllers.py:11, controllers.py:57, controllers.py:61, controllers.py:106, controllers.py:161, controllers.py:179, controllers.py:182, controllers.py:208-210, controllers.py:219, controllers.py:248-250, app.py:56, app.py:83-86
Description: `print` usado para log, auditoria e para "simular" e-mail/SMS/push; inclui e-mails de usuários no stdout.
Impact: Sem níveis, sem destino configurável, polui stdout.
Recommendation: Módulo `logging` e `NotificationService` (PB-16).

### [LOW] Nomenclatura Ruim / Shadowing de Builtins (AP-17)
File: controllers.py:14, controllers.py:24-56, controllers.py:64, controllers.py:98, controllers.py:136, models.py:24, models.py:54, models.py:65, models.py:89
Description: Parâmetro/variável `id` sobrescreve o builtin; `cursor2/cursor3`, `dados`, `produto_existente` pouco descritivos.
Impact: Leitura confusa e risco de bugs sutis.
Recommendation: Renomear para `produto_id`, `usuario_id`, `pedido_id` internamente (rotas mantêm o contrato) (PB-17).

### [LOW] Imports Não Usados e Código Morto (AP-18)
File: models.py:2, database.py:2, app.py:4
Description: `import sqlite3` em `models.py` e `import os` em `database.py` nunca usados; `app.py` importa `get_db` só para SQL direto.
Impact: Ruído e acoplamento desnecessário.
Recommendation: Remover imports mortos (PB-18).

================================
Total: 16 findings
================================
Deprecated APIs: none detected (Flask 3.x / sqlite3 sem uso de APIs obsoletas; o ponto de modernização é a conexão global, já coberto em AP-07)

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y   (confirmado pelo usuário ao aprovar o plano de execução)
```

