# Criação de Skills — Refatoração Arquitetural Automatizada (`refactor-arch`)

Repositório de entrega do desafio do módulo **Desenvolvimento de Software e Aplicações com IA**, contendo a skill agnóstica de tecnologia **`refactor-arch`**, os relatórios de auditoria arquitetural (`reports/audit-project-{1,2,3}.md`) e o código refatorado para o padrão **MVC (Model-View-Controller)** dos três projetos legados:

1. **`code-smells-project/`** — API de E-commerce em **Python / Flask** (originalmente monolítica em 4 arquivos)
2. **`ecommerce-api-legacy/`** — LMS API com fluxo de checkout em **Node.js / Express** (originalmente concentrada em uma *God Class* `AppManager`)
3. **`task-manager-api/`** — API de Task Manager em **Python / Flask + SQLAlchemy** (originalmente com separação parcial de pastas, mas com *Fat Routes* e problemas de segurança/qualidade)

---

## Sumário

- [A) Análise Manual](#a-análise-manual)
  - [Projeto 1 — `code-smells-project` (Python / Flask)](#1-projeto-1--code-smells-project-python--flask)
  - [Projeto 2 — `ecommerce-api-legacy` (Node.js / Express)](#2-projeto-2--ecommerce-api-legacy-nodejs--express)
  - [Projeto 3 — `task-manager-api` (Python / Flask + SQLAlchemy)](#3-projeto-3--task-manager-api-python--flask--sqlalchemy)
- [B) Construção da Skill](#b-construção-da-skill)
- [C) Resultados](#c-resultados)
  - [Resumo Quantitativo das Auditorias](#resumo-quantitativo-das-auditorias)
  - [Comparação Antes vs. Depois da Estrutura de Diretórios](#comparação-antes-vs-depois-da-estrutura-de-diretórios)
  - [Checklists de Validação por Projeto](#checklists-de-validação-por-projeto)
  - [Logs Reais de Execução e Validação dos Endpoints](#logs-reais-de-execução-e-validação-dos-endpoints)
  - [Comportamento da Skill em Stacks e Organizações Diferentes](#comportamento-da-skill-em-stacks-e-organizações-diferentes)
- [D) Como Executar](#d-como-executar)

---

## A) Análise Manual

Antes de projetar a skill `refactor-arch`, realizamos a leitura integral de todos os arquivos-fonte dos 3 projetos para identificar as falhas arquiteturais, vulnerabilidades de segurança e *code smells*.

### 1. Projeto 1 — `code-smells-project/` (Python / Flask)

| # | Severidade | Problema / Anti-Pattern | Arquivo e Linhas (Original) | Justificativa de Relevância |
|---|---|---|---|---|
| 1 | **CRITICAL** | **SQL Injection & Execução Arbitrária de SQL** | `models.py:28, 47-50, 58-61, 68, 92, 109-111, 126-129, 289-297` e `app.py:59-78` | Todas as queries SQL são concatenadas com strings (`"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"`), permitindo bypass de login e adulteração do banco. Além disso, `POST /admin/query` executa qualquer comando SQL enviado no body JSON sem autenticação. |
| 2 | **CRITICAL** | **Credenciais Hardcoded e Expostas em Endpoint Público** | `app.py:7-8` e `controllers.py:285-289` | `SECRET_KEY = "minha-chave-super-secreta-123"` está hardcoded no código e é retornada publicamente no payload JSON do endpoint `GET /health` junto com `debug: true` e `db_path`. |
| 3 | **CRITICAL** | **Senhas em Texto Puro no Banco e Vazadas na API** | `database.py:75-79` e `models.py:79-86, 95-102, 122-131` | Senhas são armazenadas sem hash (`admin123`, `123456`) e retornadas integralmente nos endpoints `GET /usuarios` e `GET /usuarios/<id>`. |
| 4 | **HIGH** | **God Module / Violação Completa de Camadas MVC** | `models.py:1-314`, `controllers.py:1-292` e `app.py:47-78` | Um único arquivo `models.py` mistura SQL de 4 domínios (`produtos`, `usuarios`, `pedidos`, `relatorios`) com regras de negócio (cálculo de pedido, baixa de estoque e faixas de desconto); `app.py` e `controllers.py` também acessam `get_db()` e rodam SQL diretamente. |
| 5 | **HIGH** | **Estado Global Mutável de Conexão SQLite** | `database.py:4-11` | Variável global `db_connection` compartilhada entre threads com `check_same_thread=False`, sujeita a *race conditions* e impossibilitando isolamento em testes. |
| 6 | **MEDIUM** | **Queries N+1 na Listagem de Pedidos** | `models.py:171-233` | `get_pedidos_usuario` e `get_todos_pedidos` abrem um `cursor2` por pedido para buscar `itens_pedido` e, dentro dele, um `cursor3` por item para buscar o nome do produto (`1 + P + I` queries). |
| 7 | **MEDIUM** | **Ausência de Error Handler Centralizado e Validação Duplicada** | `controllers.py:5-292` | 14 blocos `try/except Exception as e` repetidos expondo `str(e)` ao cliente com status 500; validação manual de produto duplicada entre `criar_produto` e `atualizar_produto`. |
| 8 | **LOW** | **Magic Numbers e Regras Inline** | `models.py:256-262` e `controllers.py:47-54, 242` | Faixas de desconto (`10000`, `0.1`, `5000`, `0.05`, `1000`, `0.02`), limites de caracteres (`2`, `200`) e listas de categorias/status espalhados no corpo das funções. |
| 9 | **LOW** | **Logging Amador com `print()`** | `controllers.py:8, 11, 57, 61, 106, 161, 179, 208-210, 248-250` | Uso de `print()` para auditoria, erros e simulação de envio de e-mail/SMS/push diretamente nos controllers. |

---

### 2. Projeto 2 — `ecommerce-api-legacy/` (Node.js / Express)

| # | Severidade | Problema / Anti-Pattern | Arquivo e Linhas (Original) | Justificativa de Relevância |
|---|---|---|---|---|
| 1 | **CRITICAL** | **God Class (`AppManager`)** | `src/AppManager.js:4-139` | A classe `AppManager` concentra criação do banco SQLite em memória, DDL/seeds, definição das rotas Express, lógica de checkout, gateway de pagamento e agregação financeira em um único arquivo. |
| 2 | **CRITICAL** | **Segredos Hardcoded e Vazamento de Cartão/Chave em Log** | `src/utils.js:1-7` e `src/AppManager.js:45` | `dbPass` e `paymentGatewayKey` hardcoded em `utils.js`; o checkout executa `console.log("Processando cartão " + cc + " na chave " + config.paymentGatewayKey)`, vazando o PAN completo do cartão de crédito e a chave privada no stdout. |
| 3 | **CRITICAL** | **Criptografia Caseira Insegura (`badCrypto`)** | `src/utils.js:17-23` e `src/AppManager.js:18, 68` | `badCrypto` repete os 2 primeiros caracteres Base64 da senha 10.000 vezes em loop síncrono bloqueante e trunca para 10 caracteres — colisão total para senhas com o mesmo prefixo e facilmente reversível. |
| 4 | **HIGH** | **Callback Hell e Sincronização Assíncrona Manual** | `src/AppManager.js:37-77, 83-128` | Até 6 níveis de callbacks aninhados no checkout (usando `const self = this`) e contadores mutáveis manuais (`coursesPending--`, `enrPending--`) dentro de `forEach` para sincronizar queries assíncronas. |
| 5 | **HIGH** | **Quebra de Integridade Referencial e Falta de Transação** | `src/AppManager.js:50-63, 131-137` | `DELETE /api/users/:id` apaga apenas o registro em `users` e deixa matrículas e pagamentos órfãos no banco; o checkout faz múltiplos `INSERT` dependentes sem transação (`BEGIN/COMMIT/ROLLBACK`). |
| 6 | **MEDIUM** | **Queries N+1 no Relatório Financeiro** | `src/AppManager.js:83-127` | `GET /api/admin/financial-report` busca todos os cursos, faz uma query de `enrollments` por curso e, para cada matrícula, faz mais duas queries (`users` e `payments`). |
| 7 | **MEDIUM** | **Ausência de Middleware de Erro e Callbacks sem Tratamento** | `src/AppManager.js:38-135` | Respostas de erro inconsistentes em texto puro (`"Erro DB"`) e vários callbacks do `sqlite3` que sequer verificam o parâmetro `err`. |
| 8 | **LOW** | **Nomenclatura Críptica de Variáveis** | `src/AppManager.js:29-33, 52, 89-106` | Variáveis de 1 a 3 letras (`u`, `e`, `p`, `cid`, `cc`, `enrId`, `c`, `enr`) que dificultam a leitura e manutenção. |
| 9 | **LOW** | **Código Morto (`totalRevenue`) e Estado Global (`globalCache`)** | `src/utils.js:9-15, 25` e `src/AppManager.js:2` | `totalRevenue` é exportado e importado mas nunca utilizado; `globalCache` acumula chaves em memória sem política de expiração. |

---

### 3. Projeto 3 — `task-manager-api/` (Python / Flask + SQLAlchemy)

| # | Severidade | Problema / Anti-Pattern | Arquivo e Linhas (Original) | Justificativa de Relevância |
|---|---|---|---|---|
| 1 | **CRITICAL** | **Hashing MD5 sem Salt, Vazamento de Senha em `User.to_dict()` e Token Fake** | `models/user.py:16-32` e `routes/user_routes.py:29-40, 85-86, 129, 207-211` | Senhas são gravadas com `hashlib.md5` sem salt; `User.to_dict()` inclui `'password': self.password` em todas as respostas de usuário e login; e `/login` devolve `'fake-jwt-token-' + str(user.id)`. |
| 2 | **CRITICAL** | **Credenciais Hardcoded (App e SMTP)** | `app.py:11-13` e `services/notification_service.py:7-10` | `SECRET_KEY = 'super-secret-key-123'` e `self.email_password = 'senha123'` fixos no código-fonte. |
| 3 | **HIGH** | **Fat Routes / Ausência da Camada de Controllers e Mistura de Domínios** | `routes/task_routes.py:11-299`, `routes/user_routes.py:10-211` e `routes/report_routes.py:12-223` | Apesar de ter pastas `models/` e `routes/`, não existe `controllers/`: toda regra de negócio, validação e manipulação de `db.session` está nas rotas. Além disso, o CRUD de `categories` está dentro de `report_routes.py:157-223`. |
| 4 | **MEDIUM** | **Uso de APIs Deprecated (`Model.query.get` e `datetime.utcnow`)** | `routes/task_routes.py:31-285`, `routes/user_routes.py:29-172`, `routes/report_routes.py:35-213` e `models/*.py` | 16 chamadas a `Model.query.get(id)` (depreciado no SQLAlchemy 2.0 em favor de `db.session.get(Model, id)`) e 18 chamadas a `datetime.utcnow()` (depreciado no Python 3.12+ em favor de `datetime.now(timezone.utc)`). |
| 5 | **MEDIUM** | **Queries N+1 e Duplicação da Lógica `overdue`** | `routes/task_routes.py:14-59`, `routes/report_routes.py:53-68, 159-165` | `GET /tasks` busca `User` e `Category` dentro do loop `for t in tasks`; `GET /reports/summary` e `GET /categories` executam queries por registro em loop; e a regra `Task.is_overdue()` já existente no Model é reescrita manualmente em 6 lugares. |
| 6 | **MEDIUM** | **Cláusulas `except:` Genéricas (Bare Except) e Sem Error Handler** | `routes/task_routes.py:62, 137, 204, 236`, `routes/report_routes.py:186, 207, 221` e `utils/helpers.py:46, 49, 88` | 12 blocos `except:` sem especificar a exceção ocultam falhas reais e duplicam rollbacks manuais por toda a aplicação. |
| 7 | **LOW** | **Imports Não Utilizados, Código Morto e `type(x) == list`** | `app.py:7`, `routes/task_routes.py:7, 141, 210` e `utils/helpers.py:3-7, 57-108` | Dezenas de imports mortos (`os, sys, json, time, math, hashlib`), checagem `type(tags) == list` em vez de `isinstance`, e helpers em `utils/helpers.py` ignorados pelas rotas. |
| 8 | **LOW** | **Logging com `print()` e `if/else` Booleano Redundante** | `routes/task_routes.py:149, 153, 219, 234` e `models/user.py:34-38`, `models/task.py:38-60` | Uso de `print()` em vez de `logging` e métodos retornando `if cond: return True else: return False`. |

---

## B) Construção da Skill

A skill `refactor-arch` foi criada em `.claude/skills/refactor-arch/` dentro de cada um dos 3 projetos, utilizando o princípio de **Progressive Disclosure**: o arquivo principal `SKILL.md` atua como o prompt orquestrador das 3 fases sequenciais, enquanto o conhecimento profundo de domínio fica modularizado em 5 arquivos de referência em `references/`.

### 1. Decisões de Design e Estrutura de Arquivos

```text
.claude/skills/refactor-arch/
├── SKILL.md                               # Orquestrador de 3 fases (Análise → Auditoria com pausa → Refatoração + Validação)
├── 01-project-analysis.md                 # Área 1 (raiz + espelhado em references/)
├── 02-antipatterns-catalog.md             # Área 2 (raiz + espelhado em references/)
├── 03-audit-report-template.md            # Área 3 (raiz + espelhado em references/)
├── 04-mvc-guidelines.md                   # Área 4 (raiz + espelhado em references/)
├── 05-refactoring-playbook.md             # Área 5 (raiz + espelhado em references/)
└── references/
    ├── project-analysis.md                # Heurísticas de detecção de linguagem, framework, banco, domínio e maturidade (1/5 a 5/5)
    ├── anti-patterns-catalog.md           # Catálogo de 18 anti-patterns (CRITICAL a LOW) + tabelas de APIs deprecated por stack
    ├── report-template.md                 # Template estrito do relatório de auditoria da Fase 2 + resumo da Fase 3
    ├── mvc-guidelines.md                  # Regras da arquitetura MVC alvo (camadas, dependências e responsabilidades)
    └── refactoring-playbook.md            # 18 padrões concretos de transformação Antes/Depois (Python e Node.js)
```

- **Separação entre Fluxo e Conhecimento**: O `SKILL.md` define regras invioláveis (somente leitura nas Fases 1 e 2, citação obrigatória de `arquivo:linha` reais, preservação de contrato HTTP, pausa obrigatória na Fase 2 com `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]`, e validação de boot + endpoints na Fase 3).
- **Rastreabilidade Catálogo ↔ Playbook**: Cada anti-pattern do catálogo (`AP-01` a `AP-18`) aponta diretamente para a transformação correspondente no playbook (`PB-01` a `PB-18`), garantindo que todo problema diagnosticado na Fase 2 tenha uma receita clara de correção na Fase 3.

### 2. Catálogo de Anti-Patterns (18 Padrões + APIs Deprecated)

Incluímos **18 anti-patterns** distribuídos nas 4 severidades (superando o mínimo exigido de 8):
- **CRITICAL (`AP-01` a `AP-05`)**: Hardcoded Credentials/Secrets (`AP-01`), SQL Injection (`AP-02`), God Class/Module (`AP-03`), Senhas Fracas/Expostas (`AP-04`), Endpoints Administrativos Perigosos Sem Auth (`AP-05`).
- **HIGH (`AP-06` a `AP-09`)**: Fat Routes / Regra de Negócio nas Rotas (`AP-06`), Estado Global Mutável / Falta de DI (`AP-07`), Quebra de Integridade Referencial / Falta de Transação (`AP-08`), Callback Hell (`AP-09`).
- **MEDIUM (`AP-10` a `AP-14`)**: N+1 Queries (`AP-10`), Tratamento de Erros Ausente/Inseguro (`AP-11`), Validação Ausente/Duplicada (`AP-12`), Duplicação de Código (`AP-13`), e **APIs Deprecated / Obsoletas (`AP-14`)** (como `Model.query.get(id)` → `db.session.get(Model, id)`, `datetime.utcnow()` → `datetime.now(timezone.utc)`, `hashlib.md5` → `scrypt/pbkdf2`, callbacks → `async/await`).
- **LOW (`AP-15` a `AP-18`)**: Magic Numbers (`AP-15`), Logging com `print`/`console.log` (`AP-16`), Nomenclatura Ruim (`AP-17`), Código Morto e Imports Não Usados (`AP-18`).

### 3. Como Garantimos que a Skill é Agnóstica de Tecnologia

1. **Detecção baseada em sinais (Fase 1)**: `project-analysis.md` instrui o agente a inspecionar manifestos (`requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`, etc.), entry points e drivers de banco antes de assumir qualquer tecnologia.
2. **Diretrizes conceituais de camadas (`mvc-guidelines.md`)**: Define o papel de `config/`, `models/`, `controllers/`, `routes/` (`views/`) e `middlewares/` em termos de fluxo de dependência (`Routes → Controllers → Models → Database`), adaptando-se tanto a projetos monolíticos quanto a projetos parcialmente estruturados.
3. **Exemplos multi-stack no Playbook (`refactoring-playbook.md`)**: Demonstra cada transformação tanto em Python/Flask (SQLite puro e SQLAlchemy) quanto em Node.js/Express, permitindo generalização imediata.

### 4. Desafios Encontrados e Soluções Aplicadas

- **Compatibilidade com dados existentes e seeds após troca de hash de senha**: Ao migrar senhas em texto puro (Projeto 1) e MD5 (Projeto 3) para `werkzeug.security.generate_password_hash`, atualizamos os seeds e adicionamos verificação híbrida com *re-hash* transparente no login caso exista um banco legado.
- **Substituição de `datetime.utcnow()` sem quebrar comparações SQLite**: No Python 3.12+, `datetime.now(timezone.utc)` retorna um objeto *timezone-aware*, enquanto o SQLite retorna colunas `DateTime` *naive*, causando `TypeError: can't compare offset-naive and offset-aware datetimes`. Resolvemos isso no playbook (`PB-14`) e no helper `utcnow()` usando `datetime.now(timezone.utc).replace(tzinfo=None)`, eliminando 100% dos `DeprecationWarning` mantendo compatibilidade total com SQLite.
- **Conflito entre módulo `models.py` e pacote `models/`**: No Projeto 1, documentamos no playbook a remoção explícita dos arquivos monolíticos antigos (`models.py`, `controllers.py`, `database.py`) ao criar os pacotes equivalentes para evitar shadowing de imports em Python.

---

## C) Resultados

### Resumo Quantitativo das Auditorias

Os relatórios completos gerados na Fase 2 estão disponíveis na pasta [`reports/`](file:///Users/vinicius/Documents/mba-ia-refactor-projects-skill/reports):

| Projeto | Stack Detectada | Arquivos Analisados | Maturidade (Antes → Depois) | CRITICAL | HIGH | MEDIUM | LOW | Total de Findings | Relatório Completo |
|---|---|---:|:---:|---:|---:|---:|---:|---:|---|
| **1. `code-smells-project`** | Python 3 + Flask 3.1.1 (SQLite) | 4 (~780 LOC) | `2/5 → 4/5` | 5 | 3 | 4 | 4 | **16** | [reports/audit-project-1.md](file:///Users/vinicius/Documents/mba-ia-refactor-projects-skill/reports/audit-project-1.md) |
| **2. `ecommerce-api-legacy`** | Node.js + Express 4.18.2 (SQLite) | 3 (~180 LOC) | `1/5 → 4/5` | 3 | 4 | 4 | 4 | **15** | [reports/audit-project-2.md](file:///Users/vinicius/Documents/mba-ia-refactor-projects-skill/reports/audit-project-2.md) |
| **3. `task-manager-api`** | Python 3 + Flask 3.0.0 + SQLAlchemy | 11 (~1.083 LOC) | `2.5/5 → 4/5` | 2 | 3 | 5 | 4 | **14** | [reports/audit-project-3.md](file:///Users/vinicius/Documents/mba-ia-refactor-projects-skill/reports/audit-project-3.md) |

---

### Comparação Antes vs. Depois da Estrutura de Diretórios

#### Projeto 1 — `code-smells-project/` (Python / Flask)

```text
ANTES (Monolítico — 4 arquivos)          DEPOIS (Padrão MVC)
code-smells-project/                     code-smells-project/
├── app.py                               ├── app.py                        # Composition root (create_app)
├── controllers.py                       ├── config/
├── models.py                            │   ├── constants.py              # Faixas de desconto, categorias e status
├── database.py                          │   └── settings.py               # Variáveis de ambiente sem hardcoded
└── requirements.txt                     ├── database/
                                         │   ├── connection.py             # Conexão por request (flask.g) + teardown
                                         │   └── schema.py                 # DDL + seed com hash seguro
                                         ├── models/
                                         │   ├── produto_model.py          # Queries parametrizadas de produtos
                                         │   ├── usuario_model.py          # Queries de usuários (sem expor senha)
                                         │   ├── pedido_model.py           # JOIN único (sem N+1) + transação atômica
                                         │   ├── relatorio_model.py        # Agregação SQL de vendas
                                         │   └── sistema_model.py          # Health counts e reset seguro
                                         ├── controllers/
                                         │   ├── produto_controller.py     # Validação e regras de produto
                                         │   ├── usuario_controller.py     # Cadastro e login com hash seguro
                                         │   ├── pedido_controller.py      # Regras de pedido, estoque e cancelamento
                                         │   ├── relatorio_controller.py   # Cálculo de desconto e ticket médio
                                         │   └── sistema_controller.py     # Health e proteção de reset por token
                                         ├── routes/
                                         │   ├── produto_routes.py         # Blueprint de produtos
                                         │   ├── usuario_routes.py         # Blueprint de usuários/login
                                         │   ├── pedido_routes.py          # Blueprint de pedidos/relatório
                                         │   └── sistema_routes.py         # Blueprint /, /health, /admin/reset-db
                                         ├── services/
                                         │   └── notification_service.py   # Serviço de notificações com logging
                                         ├── middlewares/
                                         │   └── error_handler.py          # Tratamento centralizado de erros HTTP/AppError
                                         └── utils/
                                             └── exceptions.py             # Hierarquia AppError (400, 401, 403, 404)
```

#### Projeto 2 — `ecommerce-api-legacy/` (Node.js / Express)

```text
ANTES (God Class — 3 arquivos)           DEPOIS (Padrão MVC)
ecommerce-api-legacy/src/                ecommerce-api-legacy/src/
├── app.js                               ├── app.js                        # Composition root (createApp + DI)
├── AppManager.js                        ├── config/
└── utils.js                             │   ├── constants.js              # Status de pagamento, prefixo de cartão, regex
                                         │   └── settings.js               # Configurações via process.env
                                         ├── database/
                                         │   ├── connection.js             # Wrapper Promise (run/get/all/withTransaction)
                                         │   └── schema.js                 # Tabelas + seed com crypto.scryptSync
                                         ├── models/
                                         │   ├── userModel.js              # CRUD + deleteWithCascade transacional
                                         │   ├── courseModel.js            # Busca ativa + JOIN único do relatório
                                         │   ├── enrollmentModel.js        # Persistência de matrículas
                                         │   ├── paymentModel.js           # Persistência de pagamentos
                                         │   └── auditLogModel.js          # Persistência de auditoria
                                         ├── controllers/
                                         │   ├── checkoutController.js     # Fluxo async/await transacional de checkout
                                         │   ├── reportController.js       # Agregação do relatório sem N+1
                                         │   └── userController.js         # Exclusão limpa de usuário e vínculos
                                         ├── routes/
                                         │   ├── index.js                  # Roteador principal /api
                                         │   ├── checkoutRoutes.js         # POST /api/checkout
                                         │   ├── reportRoutes.js           # GET /api/admin/financial-report
                                         │   └── userRoutes.js             # DELETE /api/users/:id
                                         ├── middlewares/
                                         │   └── errorHandler.js           # Middleware global de erros Express
                                         └── utils/
                                             ├── crypto.js                 # Hash seguro com crypto.scryptSync + salt
                                             ├── errors.js                 # AppError, ValidationError, NotFoundError
                                             └── logger.js                 # Logger estruturado sem vazar cartão/chaves
```

#### Projeto 3 — `task-manager-api/` (Python / Flask + SQLAlchemy)

```text
ANTES (Parcial, sem Controllers)         DEPOIS (Padrão MVC Completo)
task-manager-api/                        task-manager-api/
├── app.py                               ├── app.py                        # Composition root (create_app)
├── database.py                          ├── database.py                   # Instância SQLAlchemy
├── seed.py                              ├── seed.py                       # Seed atualizado (sem datetime.utcnow)
├── models/                              ├── config/
│   ├── user.py                          │   ├── constants.py              # Status, prioridades, limites
│   ├── task.py                          │   └── settings.py               # Configurações via variáveis de ambiente
│   └── category.py                      ├── models/
├── routes/                              │   ├── user.py                   # Hash werkzeug (sem MD5) e to_dict sem senha
│   ├── task_routes.py (299 linhas)      │   ├── task.py                   # Relacionamentos com cascade + is_overdue()
│   ├── user_routes.py (211 linhas)      │   └── category.py               # Entidade Category limpa
│   └── report_routes.py (223 linhas)    ├── controllers/                  # ← CAMADA CRIADA
├── services/                            │   ├── task_controller.py        # Regras de tasks, joinedload e stats SQL
│   └── notification_service.py          │   ├── user_controller.py        # Regras de usuários e token assinado
└── utils/                               │   ├── category_controller.py    # CRUD de categorias desacoplado de reports
    └── helpers.py                       │   └── report_controller.py      # Agregações SQL sem N+1
                                         ├── routes/
                                         │   ├── task_routes.py            # Rotas enxutas delegando ao controller
                                         │   ├── user_routes.py            # Rotas enxutas de usuários e login
                                         │   ├── category_routes.py        # Rotas de categorias separadas
                                         │   └── report_routes.py          # Rotas exclusivas de relatórios
                                         ├── middlewares/
                                         │   └── error_handler.py          # Handler global de AppError e HTTPException
                                         ├── services/
                                         │   └── notification_service.py   # SMTP via env + logging
                                         └── utils/
                                             ├── exceptions.py             # ValidationError, NotFoundError, ConflictError...
                                             └── helpers.py                # Helpers limpos + utcnow() compatível Python 3.13
```

---

### Checklists de Validação por Projeto

| Item de Validação | Projeto 1 (`code-smells-project`) | Projeto 2 (`ecommerce-api-legacy`) | Projeto 3 (`task-manager-api`) |
|---|:---:|:---:|:---:|
| **Fase 1 — Análise** | | | |
| Linguagem detectada corretamente | [x] Python 3 | [x] JavaScript (Node.js) | [x] Python 3 |
| Framework detectado corretamente | [x] Flask 3.1.1 | [x] Express 4.18.2 | [x] Flask 3.0.0 + SQLAlchemy |
| Domínio da aplicação descrito corretamente | [x] E-commerce API | [x] LMS API com Checkout | [x] Task Manager API |
| Número de arquivos analisados condiz com a realidade | [x] 4 arquivos | [x] 3 arquivos | [x] 11 arquivos |
| **Fase 2 — Auditoria** | | | |
| Relatório segue o template definido nos arquivos de referência | [x] Sim | [x] Sim | [x] Sim |
| Cada finding tem arquivo e linhas exatos | [x] Sim | [x] Sim | [x] Sim |
| Findings ordenados por severidade (CRITICAL → LOW) | [x] Sim | [x] Sim | [x] Sim |
| Mínimo de 5 findings identificados | [x] 16 findings | [x] 15 findings | [x] 14 findings |
| Detecção de APIs deprecated incluída (se aplicável) | [x] Verificado | [x] Sim (`AP-14`) | [x] Sim (`AP-14`: `Query.get`, `utcnow`) |
| Skill pausa e pede confirmação antes da Fase 3 | [x] Sim | [x] Sim | [x] Sim |
| **Fase 3 — Refatoração** | | | |
| Estrutura de diretórios segue padrão MVC | [x] Sim | [x] Sim | [x] Sim |
| Configuração extraída para módulo de config (sem hardcoded) | [x] `config/settings.py` | [x] `src/config/settings.js` | [x] `config/settings.py` |
| Models criados para abstrair dados | [x] 5 models | [x] 5 models | [x] 3 models ORM |
| Views/Routes separadas para visualização ou roteamento | [x] 4 blueprints | [x] 4 routers | [x] 4 blueprints |
| Controllers concentram o fluxo da aplicação | [x] 5 controllers | [x] 3 controllers | [x] 4 controllers |
| Error handling centralizado | [x] `error_handler.py` | [x] `errorHandler.js` | [x] `error_handler.py` |
| Entry point claro | [x] `app.py` | [x] `src/app.js` | [x] `app.py` |
| Aplicação inicia sem erros | [x] Sim | [x] Sim | [x] Sim |
| Endpoints originais respondem corretamente | [x] 100% validados | [x] 100% validados | [x] 100% validados |

---

### Logs Reais de Execução e Validação dos Endpoints

#### 1. Logs de Validação — Projeto 1 (`code-smells-project`)
```text
01 GET / -> 200 {"endpoints":{"health":"/health","login":"/login","pedidos":"/pedidos","produtos":"/produtos","relatorios":"/relatorios/vendas","usuarios":"/usuarios"},"mensagem":"Bem-vindo à API da Loja","versao":"1.0.0"}
02 GET /health -> 200 {"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}
03 GET /produtos -> 200 {"dados":[{"ativo":1,"categoria":"informatica","descricao":"Notebook potente para jogos","estoque":10,"id":1,"nome":"Notebook Gamer","preco":5999.99}, ...],"sucesso":true}
04 GET /produtos/1 -> 200 {"dados":{"ativo":1,"categoria":"informatica","estoque":10,"id":1,"nome":"Notebook Gamer","preco":5999.99},"sucesso":true}
05 GET /produtos/999 -> 404 {"erro":"Produto não encontrado","sucesso":false}
06 GET /produtos/busca?q=mouse&preco_max=500 -> 200 {"dados":[{"categoria":"informatica","id":2,"nome":"Mouse Wireless","preco":89.9}],"sucesso":true,"total":1}
07 POST /produtos -> 201 {"dados":{"id":11},"mensagem":"Produto criado","sucesso":true}
08 POST /produtos (inválido) -> 400 {"erro":"Preço é obrigatório","sucesso":false}
09 PUT /produtos/1 -> 200 {"mensagem":"Produto atualizado","sucesso":true}
10 DELETE /produtos/11 -> 200 {"mensagem":"Produto deletado","sucesso":true}
11 GET /usuarios -> 200 {"dados":[{"email":"admin@loja.com","id":1,"nome":"Admin","tipo":"admin"}, ...],"sucesso":true}  (sem expor senha!)
14 POST /login -> 200 {"dados":{"email":"joao@email.com","id":2,"nome":"João Silva","tipo":"cliente"},"mensagem":"Login OK","sucesso":true}
15 POST /login (senha incorreta) -> 401 {"erro":"Email ou senha inválidos","sucesso":false}
17 POST /pedidos -> 201 {"dados":{"pedido_id":1,"total":479.7},"mensagem":"Pedido criado com sucesso","sucesso":true}
19 GET /pedidos -> 200 {"dados":[{"id":1,"itens":[{"preco_unitario":89.9,"produto_id":2,"produto_nome":"Mouse Wireless","quantidade":2}, ...],"status":"pendente","total":479.7,"usuario_id":2}],"sucesso":true}
21 PUT /pedidos/1/status -> 200 {"mensagem":"Status atualizado","sucesso":true}
23 GET /relatorios/vendas -> 200 {"dados":{"desconto_aplicavel":0,"faturamento_bruto":479.7,"faturamento_liquido":479.7,"pedidos_aprovados":1,"pedidos_cancelados":0,"pedidos_pendentes":0,"ticket_medio":479.7,"total_pedidos":1},"sucesso":true}
26 POST /admin/reset-db (sem token) -> 403 {"erro":"Acesso negado","sucesso":false}
27 POST /admin/query (removido por segurança) -> 404
```

#### 2. Logs de Validação — Projeto 2 (`ecommerce-api-legacy`)
```text
[2026-10-30T16:42:07.209Z] [INFO] LMS API rodando na porta 3000
01 GET /health -> 200 {"status":"ok"}
02 GET /api/admin/financial-report -> 200 [{"course":"Clean Architecture","revenue":997,"students":[{"paid":997,"student":"Leonan"}]},{"course":"Docker","revenue":0,"students":[]}]
03 POST /api/checkout (Guilherme, curso 2, cartão 4111...) -> 200 {"enrollment_id":2,"msg":"Sucesso"}
04 POST /api/checkout (Leonan, curso 2, cartão 4111...) -> 200 {"enrollment_id":3,"msg":"Sucesso"}
05 POST /api/checkout (cartão recusado 5111...) -> 400 {"erro":"Pagamento recusado"}
06 POST /api/checkout (curso inexistente 999) -> 404 {"erro":"Curso não encontrado"}
07 POST /api/checkout (payload incompleto) -> 400 {"erro":"Bad Request"}
08 GET /api/admin/financial-report -> 200 [{"course":"Clean Architecture","revenue":997,"students":[{"paid":997,"student":"Leonan"}]},{"course":"Docker","revenue":994,"students":[{"paid":497,"student":"Guilherme"},{"paid":497,"student":"Leonan"}]}]
09 DELETE /api/users/1 -> 200 {"msg":"Usuário e registros associados (matrículas e pagamentos) removidos com sucesso."}
10 DELETE /api/users/999 -> 404 {"erro":"Usuário não encontrado"}
11 GET /api/admin/financial-report -> 200 [{"course":"Clean Architecture","revenue":0,"students":[]},{"course":"Docker","revenue":497,"students":[{"paid":497,"student":"Guilherme"}]}]
```

#### 3. Logs de Validação — Projeto 3 (`task-manager-api`)
```text
Seed concluído com sucesso!
  3 usuários | 4 categorias | 10 tasks
01 GET / -> 200 {"message":"Task Manager API","version":"1.0"}
02 GET /health -> 200 {"status":"ok","timestamp":"2026-10-30 16:51:26.459689"}
03 GET /tasks -> 200 [{"category_id":1,"category_name":"Backend","id":1,"overdue":true,"priority":1,"status":"pending","title":"Implementar autenticação JWT","user_id":1,"user_name":"João Silva"}, ...]
04 GET /tasks/1 -> 200 {"category_id":1,"id":1,"overdue":true,"priority":1,"status":"pending","title":"Implementar autenticação JWT","user_id":1}
05 GET /tasks/999 -> 404 {"error":"Task não encontrada"}
06 POST /tasks -> 201 {"category_id":1,"id":11,"priority":2,"status":"pending","tags":["mvc","clean"],"title":"Nova Task Refatorada","user_id":1}
07 POST /tasks (título curto) -> 400 {"error":"Título muito curto"}
08 PUT /tasks/1 -> 200 {"id":1,"priority":2,"status":"in_progress","title":"Implementar autenticação JWT"}
09 GET /tasks/search?q=JWT&priority=2 -> 200 [{"id":1,"priority":2,"status":"in_progress","title":"Implementar autenticação JWT"}]
10 GET /tasks/stats -> 200 {"cancelled":1,"completion_rate":9.09,"done":1,"in_progress":3,"overdue":2,"pending":6,"total":11}
11 DELETE /tasks/11 -> 200 {"message":"Task deletada com sucesso"}
12 GET /users -> 200 [{"active":true,"email":"joao@email.com","id":1,"name":"João Silva","role":"admin","task_count":4}, ...]
15 POST /users -> 201 {"active":true,"email":"ana@email.com","id":4,"name":"Ana","role":"user"}
17 POST /login -> 200 {"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxfQ...","user":{"active":true,"email":"joao@email.com","id":1,"name":"João Silva","role":"admin"}}
18 POST /login (credenciais inválidas) -> 401 {"error":"Credenciais inválidas"}
20 GET /categories -> 200 [{"color":"#3498db","id":1,"name":"Backend","task_count":6}, ...]
21 POST /categories -> 201 {"color":"#1abc9c","description":"Hardening","id":5,"name":"Segurança"}
24 GET /reports/summary -> 200 {"overview":{"total_categories":4,"total_tasks":10,"total_users":3},"tasks_by_priority":{"critical":1,"high":4,"low":2,"medium":3,"minimal":0},"tasks_by_status":{"cancelled":1,"done":1,"in_progress":3,"pending":5}, ...}
25 GET /reports/user/1 -> 200 {"statistics":{"cancelled":0,"completion_rate":0.0,"done":0,"high_priority":2,"in_progress":1,"overdue":2,"pending":3,"total_tasks":4},"user":{"email":"joao@email.com","id":1,"name":"João Silva"}}
✓ Security check passed: no password leaked in User.to_dict()
✓ Zero DeprecationWarnings / LegacyAPIWarnings (Python 3.13 + SQLAlchemy 2.x)
```

---

### Comportamento da Skill em Stacks e Organizações Diferentes

1. **Monolito Python/Flask (`code-smells-project`)**: A skill detectou que `models.py` e `controllers.py` eram arquivos únicos que concentravam todos os domínios e criavam vulnerabilidades críticas de SQL Injection. Na Fase 3, decompôs os arquivos em pacotes `models/`, `controllers/`, `routes/`, `database/`, `config/` e `middlewares/`, parametrizando 100% das queries.
2. **God Class Node.js/Express (`ecommerce-api-legacy`)**: Mesmo mudando de linguagem (JavaScript), runtime (Node.js) e paradigma (callbacks do `sqlite3`), a skill mapeou a classe `AppManager` e converteu o *Callback Hell* em `async/await` com suporte a transações (`withTransaction`), além de substituir o `badCrypto` por `crypto.scryptSync` nativo e eliminar o N+1 com `LEFT JOIN`.
3. **Projeto Parcialmente Organizado (`task-manager-api`)**: A skill reconheceu que `models/`, `routes/`, `services/` e `utils/` já existiam, evitando recriar o que estava bom, e focou no que faltava: extraiu a camada `controllers/`, desmembrou `category_routes.py` de `report_routes.py`, eliminou `Model.query.get()` e `datetime.utcnow()` depreciados e corrigiu o vazamento de senhas MD5 em `User.to_dict()`.

---

## D) Como Executar

### 1. Pré-requisitos

- **Python 3.10+** e `pip` (para os Projetos 1 e 3)
- **Node.js 18+** e `npm` (para o Projeto 2)
- Ferramenta agêntica compatível com Skills: **Claude Code** (`claude`), **Gemini CLI** ou **Antigravity**

### 2. Comandos para Invocar a Skill em Cada Projeto

```bash
# Projeto 1 — code-smells-project (Python/Flask)
cd code-smells-project
claude "/refactor-arch"

# Projeto 2 — ecommerce-api-legacy (Node.js/Express)
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3 — task-manager-api (Python/Flask + SQLAlchemy)
cd ../task-manager-api
claude "/refactor-arch"
```

### 3. Como Rodar e Validar Cada Projeto Refatorado

#### Projeto 1 (`code-smells-project`)
```bash
cd code-smells-project
pip install -r requirements.txt
python app.py
# Em outro terminal:
curl http://localhost:5000/health
curl http://localhost:5000/produtos
curl http://localhost:5000/relatorios/vendas
```

#### Projeto 2 (`ecommerce-api-legacy`)
```bash
cd ecommerce-api-legacy
npm install
npm start
# Em outro terminal:
curl http://localhost:3000/health
curl http://localhost:3000/api/admin/financial-report
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
```

#### Projeto 3 (`task-manager-api`)
```bash
cd task-manager-api
pip install -r requirements.txt
python seed.py
python app.py
# Em outro terminal:
curl http://localhost:5000/health
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary
```
