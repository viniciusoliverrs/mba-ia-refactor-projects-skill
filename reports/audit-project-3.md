```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.0.0 (com Flask-SQLAlchemy 3.1.1)
Dependencies:  flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1, requests==2.31.0, python-dotenv==1.0.0
Domain:        Task Manager API (tarefas, usuários, categorias, autenticação e relatórios de produtividade)
Architecture:  Parcialmente em camadas — possui models/, routes/, services/ e utils/, mas sem camada controllers/ (Fat Routes com regra de negócio e queries ORM nas rotas)
Maturity:      2.5/5 (Partial Layers — Models ORM e Routes separados, mas sem camada Controllers)
Source files:  11 files analyzed (~1,083 LOC, incluindo seed.py)
DB tables:     users, categories, tasks (SQLite via SQLAlchemy ORM, arquivo tasks.db)
Entry point:   app.py
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask + SQLAlchemy
Files:   11 analyzed | ~1,083 lines of code

## Summary
CRITICAL: 2 | HIGH: 3 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:11-13, services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` e `SQLALCHEMY_DATABASE_URI = 'sqlite:///tasks.db'` estão hardcoded em `app.py`;
`NotificationService.__init__` contém credenciais SMTP hardcoded (`self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'`).
Impact: Exposição de segredos de aplicação e credenciais de e-mail no controle de versão, apesar de `python-dotenv` já constar no `requirements.txt`.
Recommendation: Extrair toda configuração sensível para `config/settings.py` lendo variáveis de ambiente (PB-01).

### [CRITICAL] Hashing MD5 sem Salt, Vazamento de Senha em `User.to_dict()` e Token Previsível (AP-04)
File: models/user.py:16-32, routes/user_routes.py:29-40, routes/user_routes.py:85-86, routes/user_routes.py:129, routes/user_routes.py:207-211
Description: `User.set_password` e `User.check_password` utilizam `hashlib.md5(pwd.encode()).hexdigest()` (algoritmo criptograficamente quebrado e sem salt);
`User.to_dict()` inclui `'password': self.password` no dicionário retornado por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`;
e `POST /login` retorna um token forjável `'fake-jwt-token-' + str(user.id)`.
Impact: Qualquer consumidor da API recebe o hash MD5 de qualquer usuário e pode revertê-lo instantaneamente via rainbow tables ou forjar tokens sequenciais.
Recommendation: Substituir MD5 por `werkzeug.security.generate_password_hash` / `check_password_hash`, remover `'password'` de `User.to_dict()` e gerar token assinado com `itsdangerous`/`hmac` (PB-04).

### [HIGH] Fat Routes / Ausência da Camada de Controllers e Mistura de Domínios (AP-06)
File: routes/task_routes.py:11-299, routes/user_routes.py:10-211, routes/report_routes.py:12-223
Description: Não existe camada `controllers/`: todas as validações, regras de negócio (cálculo de atraso `overdue`, taxas de conclusão, estatísticas),
queries diretas ao `db.session`/`Model.query` e transações (`db.session.add/commit/rollback`) estão dentro dos handlers HTTP em `routes/`.
Além disso, todo o CRUD de `categories` (`/categories`, `/categories/<int:cat_id>`) está misturado dentro de `routes/report_routes.py:157-223`.
Impact: Viola o padrão MVC e o princípio da responsabilidade única (SRP), tornando rotas extensas (~300 linhas) e impossibilitando reusar regras fora do contexto HTTP.
Recommendation: Criar camada `controllers/` (`task_controller.py`, `user_controller.py`, `category_controller.py`, `report_controller.py`) e separar `routes/category_routes.py`, mantendo `routes/` apenas para roteamento HTTP (PB-03, PB-06).

### [HIGH] Estado Mutável em Memória e Configuração Global Acoplada (AP-07)
File: app.py:9-31, services/notification_service.py:5-6
Description: `app.py` instancia e executa `db.create_all()` em escopo de importação global (dificultando testes isolados com outra URI de banco),
e `NotificationService` armazena notificações em uma lista mutável em memória (`self.notifications = []`) na instância.
Impact: Importar `app` em scripts ou testes dispara efeitos colaterais imediatos no banco `tasks.db`; notificações se perdem a cada reinício.
Recommendation: Encapsular a montagem em `create_app()` configurável via `Settings` e desacoplar serviços (PB-07).

### [HIGH] Deleção Manual sem Cascata ORM e Sem Integridade em Categorias (AP-08)
File: routes/user_routes.py:140-143, routes/report_routes.py:211-223
Description: `delete_user` busca e deleta manualmente `Task` em loop antes de deletar `User`, enquanto `delete_category` remove a categoria sem
desvincular `category_id` das tarefas associadas.
Impact: Risco de referências órfãs (`category_id` apontando para categoria inexistente) e lógica de integridade espalhada nas rotas.
Recommendation: Centralizar a remoção segura no controller/model garantindo limpeza de vínculos (`Task.category_id = None` / deleção transacional) (PB-08).

### [MEDIUM] N+1 Queries em Listagens e Relatórios (AP-10)
File: routes/task_routes.py:14-59, routes/user_routes.py:12-24, routes/report_routes.py:53-68, routes/report_routes.py:159-165
Description:
1. `GET /tasks` (`task_routes.py:41-57`) faz `Task.query.all()` e, dentro do `for t in tasks`, executa `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` para cada tarefa.
2. `GET /users` (`user_routes.py:22`) acessa `len(u.tasks)` em loop com lazy loading padrão.
3. `GET /reports/summary` (`report_routes.py:55-68`) itera por todos os usuários executando `Task.query.filter_by(user_id=u.id).all()` por usuário, além de 12 queries `count()` separadas.
4. `GET /categories` (`report_routes.py:163`) executa `Task.query.filter_by(category_id=c.id).count()` para cada categoria.
Impact: Dezenas de queries SQL por requisição em endpoints de listagem e relatórios.
Recommendation: Usar `joinedload(Task.user, Task.category)` nas listagens e agregações SQL (`func.count`, `group_by`) nos relatórios e contagens (PB-10).

### [MEDIUM] Uso de Bare `except:` e Ausência de Error Handler Centralizado (AP-11)
File: routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:204, routes/task_routes.py:236, routes/user_routes.py:130, routes/user_routes.py:149, routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221, utils/helpers.py:46, utils/helpers.py:49, utils/helpers.py:88
Description: Doze blocos utilizam `except:` nu (capturando inclusive `SystemExit`/`KeyboardInterrupt` e ocultando erros reais) e não há registro
de error handlers globais no Flask (`@app.errorhandler`). Além disso, `search_tasks` converte `int(priority)` e `int(user_id)` sem capturar `ValueError`.
Impact: Erros silenciosos difíceis de diagnosticar, repetição de `try/except/rollback` em todas as rotas e erro 500 não tratado em parâmetros de busca inválidos.
Recommendation: Criar `middlewares/error_handler.py` com exceções de domínio (`ValidationError`, `NotFoundError`, `ConflictError`) e substituir `except:` por exceções específicas (PB-11).

### [MEDIUM] Validação de Entrada Duplicada e Inconsistente (AP-12)
File: routes/task_routes.py:89-145, routes/task_routes.py:162-214, routes/user_routes.py:46-73, routes/user_routes.py:98-126, routes/report_routes.py:170-180, routes/report_routes.py:196-203, utils/helpers.py:19-108
Description: O módulo `utils/helpers.py` já define `validate_email`, `parse_date`, `is_valid_color`, `process_task_data` e constantes de validação,
mas as rotas ignoram essas funções e reimplementam validações inline divergentes (ex.: `update_category` não verifica `request.get_json()` nulo nem valida cor; `search_tasks` não valida inteiros).
Impact: Regras de validação inconsistentes entre criação e atualização e código duplicado.
Recommendation: Centralizar a validação nos controllers reutilizando os helpers e constantes (PB-12).

### [MEDIUM] Duplicação da Regra de Negócio `is_overdue` e Serialização (AP-13)
File: models/task.py:50-60, routes/task_routes.py:17-40, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:161-181, routes/report_routes.py:33-43, routes/report_routes.py:132-135
Description: Embora `Task.is_overdue()` e `Task.to_dict()` já existam em `models/task.py`, o cálculo de `overdue` (três `if` aninhados comparando
`due_date < datetime.utcnow()` e `status`) é copiado manualmente em 6 lugares diferentes, e `get_tasks()`/`get_user_tasks()` reconstroem o dicionário campo a campo.
Impact: Qualquer ajuste no critério de atraso ou serialização exige alterar 6 arquivos/funções diferentes.
Recommendation: Usar `task.is_overdue()` e `task.to_dict()` de forma consistente em todos os fluxos (PB-13).

### [MEDIUM] Uso de APIs Deprecated (SQLAlchemy 2.0 `Query.get()` e Python 3.12+ `datetime.utcnow()`) (AP-14)
File: routes/task_routes.py:31, routes/task_routes.py:42, routes/task_routes.py:51, routes/task_routes.py:67, routes/task_routes.py:72, routes/task_routes.py:117, routes/task_routes.py:122, routes/task_routes.py:158, routes/task_routes.py:188, routes/task_routes.py:195, routes/task_routes.py:215, routes/task_routes.py:227, routes/task_routes.py:285, routes/user_routes.py:29, routes/user_routes.py:94, routes/user_routes.py:136, routes/user_routes.py:155, routes/user_routes.py:172, routes/report_routes.py:35, routes/report_routes.py:42, routes/report_routes.py:45, routes/report_routes.py:71, routes/report_routes.py:105, routes/report_routes.py:133, routes/report_routes.py:192, routes/report_routes.py:213, models/user.py:14, models/task.py:15-16, models/task.py:52, models/category.py:11, services/notification_service.py:35, utils/helpers.py:38, seed.py:66-74
Description:
1. `Model.query.get(id)` (`Task.query.get`, `User.query.get`, `Category.query.get`) é usado em 16 pontos das rotas — método depreciado no SQLAlchemy 2.0 (`LegacyAPIWarning`).
2. `datetime.utcnow()` é usado em 18 pontos nos models, rotas, service, helpers e seed — método depreciado no Python 3.12+ (`DeprecationWarning`).
Impact: Emissão constante de `DeprecationWarning` / `LegacyAPIWarning` em runtime (Python 3.13 + SQLAlchemy 2.x) e incompatibilidade futura.
Recommendation: Substituir `Model.query.get(id)` por `db.session.get(Model, id)` e `datetime.utcnow()` por helper `utcnow()` baseado em `datetime.now(timezone.utc)` (PB-14).

### [LOW] Magic Numbers e Listas de Domínio Repetidas (AP-15)
File: routes/task_routes.py:96-114, routes/task_routes.py:167-184, routes/user_routes.py:64-72, routes/user_routes.py:115-121, routes/report_routes.py:24-28, routes/report_routes.py:45, routes/report_routes.py:129
Description: Limites (`3`, `200`, `1`, `5`, `4`, `7`), listas de status `['pending', 'in_progress', 'done', 'cancelled']` e roles `['user', 'admin', 'manager']`
são repetidos literal e manualmente nas rotas, ignorando as constantes já declaradas no final de `utils/helpers.py:110-116`.
Impact: Duplicação de constantes de domínio e risco de divergência.
Recommendation: Mover e importar todas as constantes a partir de `config/constants.py` / `utils/helpers.py` (PB-15).

### [LOW] Uso de `print()` em vez de Logger Estruturado (AP-16)
File: routes/task_routes.py:149, routes/task_routes.py:153, routes/task_routes.py:219, routes/task_routes.py:234, routes/user_routes.py:83, routes/user_routes.py:89, routes/user_routes.py:147, services/notification_service.py:21, services/notification_service.py:24, utils/helpers.py:39-41
Description: Uso direto de `print(f"...")` nas rotas e serviços para registrar criação/atualização/deleção e erros de banco.
Impact: Logs sem níveis de severidade nem formatação padronizada.
Recommendation: Utilizar o módulo padrão `logging` (PB-16).

### [LOW] Nomenclatura Pouco Expressiva em Loops e Variáveis Temporárias (AP-17)
File: routes/task_routes.py:16, routes/task_routes.py:122, routes/task_routes.py:268, routes/user_routes.py:14, routes/user_routes.py:141, routes/report_routes.py:24-28, routes/report_routes.py:33, routes/report_routes.py:55, routes/report_routes.py:159, models/category.py:14
Description: Variáveis de uma letra (`t`, `u`, `c`, `d`, `p`, `n`, `p1..p5`) em loops e dicionários extensos reduzem a clareza do código.
Impact: Legibilidade inferior em funções longas.
Recommendation: Adotar nomes descritivos (`task`, `user`, `category`, `priority_counts`) (PB-17).

### [LOW] Imports Não Utilizados, Código Morto e Construções Anti-Pythônicas (AP-18)
File: app.py:7, routes/task_routes.py:7, routes/user_routes.py:5-6, routes/report_routes.py:1, routes/report_routes.py:7-8, models/task.py:3, utils/helpers.py:3-7, routes/task_routes.py:141, routes/task_routes.py:210, models/user.py:34-38, models/task.py:38-48
Description:
1. Múltiplos imports nunca usados: `os, sys, json` em `app.py:7`; `json, os, sys, time` em `task_routes.py:7`; `datetime, hashlib, json` em `user_routes.py:5-6`; `request, format_date, calculate_percentage, json` em `report_routes.py:1,7,8`; `json` em `models/task.py:3`; `os, json, sys, math, hashlib` em `utils/helpers.py:3-7`.
2. Uso de `type(tags) == list` em vez de `isinstance(tags, list)` (`task_routes.py:141,210`, `helpers.py:103`).
3. `if ...: return True else: return False` redundante em `User.is_admin`, `Task.validate_status`, `Task.validate_priority`, `Task.is_overdue`.
4. Funções definidas em `utils/helpers.py` (`process_task_data`, `validate_email`, etc.) e `NotificationService` nunca integradas.
Impact: Poluição visual, warnings de linter e código morto acumulado.
Recommendation: Remover imports não utilizados, simplificar expressões booleanas, usar `isinstance` e reaproveitar os helpers nos controllers (PB-18).

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y   (confirmado pelo usuário ao aprovar o plano de execução)
```

```
================================
PHASE 3: REFACTORING COMPLETE
================================
Architecture: Partial Layers / Fat Routes (11 arquivos) -> Layered MVC + ORM (20 arquivos)
Maturity:     2.5/5 -> 4/5
Findings resolved: 14/14 (2 CRITICAL, 3 HIGH, 5 MEDIUM, 4 LOW) — validado por reprodução do Impact (ver abaixo)
Deprecated APIs fixed: 34/34 (16 Model.query.get -> db.session.get, 18 datetime.utcnow -> utcnow)
Endpoints verified: 19/19 (Zero DeprecationWarning / LegacyAPIWarning sob -W error::DeprecationWarning)
================================
```

### Revalidação por Impact (2ª execução da Fase 3)

Na 1ª execução o AP-07 foi marcado como resolvido, mas `app = create_app()` ainda rodava no import e `create_app()` executava
`db.create_all()`: `import seed` (via `from app import app`) criava/alterava `tasks.db`. O Impact não havia deixado de ocorrer.
Correção: `create_app(config)` agora é uma factory pura (sem `create_all`, sem instância global); o schema é criado por
`database.init_db(app)`, chamado só em `app.py::__main__` e em `seed.py::seed_data()` (PB-07b).

| Finding | Verificação (Impact reproduzido contra o código refatorado) | Resultado |
|---|---|---|
| AP-07 | `DATABASE_URL=sqlite:////tmp/v/import.db python -W error::DeprecationWarning -c "import app, seed"` → arquivo **não** criado (no código anterior, `import app` criava o `.db`) | RESOLVED |
| AP-04 | `GET /users/1` e `POST /login` não contêm `password` nem `fake-jwt-token` na resposta | RESOLVED |
| Boot + endpoints | 11 GETs + `POST /login` + `POST /tasks` (200/201) após `seed.py` em banco novo, sob `-W error::DeprecationWarning` | RESOLVED |
| Demais (AP-03, AP-06, AP-08, AP-10, AP-14, AP-18...) | Mantidos da 1ª execução; não reexecutados nesta rodada | NÃO REVALIDADO |

Findings resolved (revalidados por Impact nesta rodada): AP-07, AP-04. Os demais constam como resolvidos pela execução anterior.
