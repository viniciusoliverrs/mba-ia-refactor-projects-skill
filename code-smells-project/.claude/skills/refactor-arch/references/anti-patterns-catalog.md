# Catálogo de Anti-Patterns (Fase 2)

Cada entrada tem **ID**, **severidade**, **sinais de detecção acionáveis** e o item do playbook que a corrige
([refactoring-playbook.md](refactoring-playbook.md)). Os sinais são exemplos por stack; generalize para a linguagem detectada.

## Escala de severidade

- **CRITICAL**: falhas graves de arquitetura/segurança — credenciais hardcoded, SQL Injection, vazamento de dados sensíveis, God Class/Module que mistura DB + regra + rotas.
- **HIGH**: fortes violações de MVC/SOLID — regra de negócio em controllers/rotas, acoplamento sem DI, estado global mutável.
- **MEDIUM**: padronização, duplicação, performance moderada — N+1, validação ausente, falta de middleware de erro, APIs deprecated.
- **LOW**: legibilidade — nomes ruins, magic numbers, `print`/`console.log` soltos, imports/código morto.

---

## CRITICAL

### AP-01 — Hardcoded Credentials / Secrets  `CRITICAL`
- **Sinais**: `SECRET_KEY = "..."`, `password = '...'`, `apiKey/pk_live_/token` em literais; senhas de SMTP/DB no código; segredo devolvido em resposta (`/health` com `secret_key`); log imprimindo chave ou número de cartão.
- **Grep**: `SECRET|PASSWORD|PASS|KEY|TOKEN|pk_live|smtp` em atribuições a strings literais.
- **Playbook**: PB-01.

### AP-02 — SQL Injection / Query Construída por Concatenação  `CRITICAL`
- **Sinais**: `"SELECT ... " + var`, f-string/template literal dentro de `execute(...)`, `LIKE '%" + termo + "%'`; endpoint que executa SQL recebido do cliente (`/admin/query`).
- **Playbook**: PB-02.

### AP-03 — God Class / God Module  `CRITICAL`
- **Sinais**: um arquivo/classe com rotas + SQL + regra de negócio + criação de schema + seeds; arquivo com >300 linhas cobrindo vários domínios; classe `Manager`/`Utils` que faz tudo; rotas definidas dentro de método de classe de dados.
- **Playbook**: PB-03.

### AP-04 — Senhas Fracas / Sensíveis Expostas  `CRITICAL`
- **Sinais**: senha em texto puro no DB; `md5`/`sha1` sem salt; hash caseiro (loop base64); `to_dict` / SELECT devolvendo campo `senha`/`password`; comparação de senha direto na query SQL; token falso previsível (`'fake-jwt-token-' + id`).
- **Playbook**: PB-04.

### AP-05 — Endpoints Administrativos Perigosos Sem Autenticação  `CRITICAL`
- **Sinais**: rotas `/admin/reset-db`, `/admin/query`, `DELETE` de dados em massa sem verificação de identidade/papel; `debug=True` em produção.
- **Playbook**: PB-05.

## HIGH

### AP-06 — Regra de Negócio Presa em Controllers / Rotas (Fat Routes)  `HIGH`
- **Sinais**: handler de rota com >40 linhas; validação + query ORM + cálculo + serialização no mesmo handler; ausência de camada controller/service; cálculo de desconto/overdue dentro de rota ou model de dados.
- **Playbook**: PB-06.

### AP-07 — Estado Global Mutável / Acoplamento sem DI  `HIGH`
- **Sinais**: `global db_connection`, singleton de módulo, `let globalCache = {}` exportado e mutado, `totalRevenue` global; dependências criadas dentro das funções (`new sqlite3.Database` no construtor, `Modular.get`).
- **Playbook**: PB-07.

### AP-08 — Integridade de Dados / Falta de Transação  `HIGH`
- **Sinais**: múltiplos writes dependentes sem transação (`INSERT pedido` + `INSERT itens` + `UPDATE estoque`); deleção que deixa órfãos (`DELETE users` sem tratar `enrollments/payments`); commit parcial; check-then-act de estoque sem atomicidade.
- **Playbook**: PB-08.

### AP-09 — Callback Hell / Fluxo Assíncrono Aninhado  `HIGH`
- **Sinais**: callbacks aninhados em 4+ níveis; contadores manuais (`pending--`) para sincronizar; ausência de `async/await`/Promises.
- **Playbook**: PB-09.

## MEDIUM

### AP-10 — N+1 Queries  `MEDIUM`
- **Sinais**: query ou `Model.query.get(...)` dentro de `for`/`forEach`/`map`; cursor aninhado por linha; relação lazy acessada em loop (`len(u.tasks)`).
- **Playbook**: PB-10.

### AP-11 — Tratamento de Erros Ausente, Duplicado ou Inseguro  `MEDIUM`
- **Sinais**: `try/except Exception` repetido em todo handler devolvendo `str(e)` ao cliente; `except:` nu; `res.status(500).send("Erro DB")` espalhado; ausência de middleware/`errorhandler` global.
- **Playbook**: PB-11.

### AP-12 — Validação de Entrada Ausente ou Duplicada  `MEDIUM`
- **Sinais**: `request.get_json()` usado sem checar `None`; `int(request.args[...])` sem tratamento; mesmas regras copiadas em POST e PUT; sem validação de tipo/formato (email, preço, cartão); funções de validação existentes em `utils` não usadas.
- **Playbook**: PB-12.

### AP-13 — Duplicação de Código  `MEDIUM`
- **Sinais**: mesmo bloco de serialização/`overdue`/mapeamento row→dict copiado 3+ vezes; funções utilitárias já existentes ignoradas.
- **Playbook**: PB-13.

### AP-14 — APIs Deprecated / Obsoletas  `MEDIUM`
Sempre varrer. Recomendar o equivalente moderno:

| Obsoleto | Moderno | Stack |
|---|---|---|
| `Model.query.get(id)` | `db.session.get(Model, id)` | SQLAlchemy 2.x |
| `datetime.utcnow()` | `datetime.now(timezone.utc)` | Python ≥3.12 |
| `datetime.utcfromtimestamp` | `datetime.fromtimestamp(ts, timezone.utc)` | Python ≥3.12 |
| `@app.before_first_request` | init no app factory | Flask 2.3+ |
| `flask.json.JSONEncoder` | `app.json` provider | Flask 2.2+ |
| `hashlib.md5/sha1` para senha | `werkzeug.security` / `bcrypt` / `scrypt` | qualquer |
| `new Buffer(x)` | `Buffer.from(x)` | Node.js |
| `var` | `let`/`const` | JS |
| Callbacks `(err, data) =>` | `async/await` + Promises (`util.promisify`) | Node.js |
| `body-parser` separado | `express.json()` | Express 4.16+ |
| `req.param()` | `req.params/query/body` | Express |
| `res.send(status)` / `res.json(obj, status)` | `res.status(n).json()` | Express |
| `sqlite3 .verbose()` em produção | remover | Node |
- **Playbook**: PB-14.

## LOW

### AP-15 — Magic Numbers / Strings Hardcoded  `LOW`
- **Sinais**: literais numéricos de regra (`10000`, `0.1`, `5000`), listas de status/categorias repetidas, `"4"` prefixo de cartão, senha default `"123456"`, limites `200`/`3`.
- **Playbook**: PB-15.

### AP-16 — Logging Amador (`print` / `console.log`)  `LOW`
- **Sinais**: `print(...)`/`console.log(...)` para log de negócio, simulação de e-mail/SMS/push no controller.
- **Playbook**: PB-16.

### AP-17 — Nomenclatura Ruim  `LOW`
- **Sinais**: variáveis de 1-3 letras (`u`, `e`, `p`, `cid`, `cc`), payload críptico, nomes que não revelam intenção.
- **Playbook**: PB-17.

### AP-18 — Código Morto / Imports Não Usados  `LOW`
- **Sinais**: imports nunca usados (`import os, sys, json`), funções nunca chamadas, variáveis exportadas não usadas (`totalRevenue`), `type(x) == list` em vez de `isinstance`, métodos `is_admin()` com `if/else` redundante.
- **Playbook**: PB-18.

---

## Distribuição mínima

O catálogo cobre 18 anti-patterns: 5 CRITICAL, 4 HIGH, 5 MEDIUM (incluindo APIs deprecated), 4 LOW.

## Como classificar dúvidas

- Impacta segurança ou integridade e é explorável → CRITICAL.
- Impede teste/manutenção por violar camadas → HIGH.
- Custo moderado de performance/padronização → MEDIUM.
- Só estética/legibilidade → LOW.
- Em projetos já em camadas, não reporte "God Module" se não existir; reporte as violações reais (AP-06 etc.).
