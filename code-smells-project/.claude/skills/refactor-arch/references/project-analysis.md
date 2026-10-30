# Análise de Projeto — Heurísticas de Detecção (Fase 1)

Use estas heurísticas para identificar a stack **sem assumir nada**. Procure primeiro na raiz do projeto.

## 1. Linguagem

| Sinal | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `*.py` | Python |
| `package.json`, `*.js`, `*.ts`, `node_modules/` | JavaScript / TypeScript (Node.js) |
| `pom.xml`, `build.gradle`, `*.java` | Java |
| `go.mod`, `*.go` | Go |
| `composer.json`, `*.php` | PHP |
| `Gemfile`, `*.rb` | Ruby |
| `*.csproj`, `*.cs` | C# |

Em caso de mais de uma, a linguagem do **entry point** e do manifesto de dependências vence.

## 2. Framework (e versão)

Leia o manifesto de dependências (versão) e confirme pelos imports no entry point.

| Framework | Manifesto | Sinal no código |
|---|---|---|
| Flask | `flask` | `from flask import Flask`, `@app.route`, `Blueprint`, `app.add_url_rule` |
| FastAPI | `fastapi` | `FastAPI()`, `@app.get` |
| Django | `django` | `manage.py`, `urls.py`, `settings.py` |
| Express | `express` | `require('express')`, `app.get/post(...)`, `Router()` |
| NestJS | `@nestjs/core` | decorators `@Controller` |
| Spring Boot | `spring-boot-starter` | `@RestController` |
| Gin / Echo | `go.mod` | `gin.Default()` |
| Laravel / Rails | `composer.json` / `Gemfile` | `routes/web.php` / `config/routes.rb` |

## 3. Banco de dados

| Sinal | Banco / acesso |
|---|---|
| `sqlite3.connect`, `new sqlite3.Database`, `sqlite:///`, `*.db` | SQLite |
| `psycopg2`, `pg`, `postgresql://` | PostgreSQL |
| `mysql`, `pymysql`, `mysql2` | MySQL |
| `pymongo`, `mongoose` | MongoDB |
| `flask_sqlalchemy`, `SQLAlchemy`, `db.Model` | ORM SQLAlchemy |
| `sequelize`, `typeorm`, `prisma` | ORM Node |

Tabelas/entidades: procure `CREATE TABLE`, classes `db.Model`/`Schema`, `__tablename__`, migrations.
Anote também se o banco é em memória (`:memory:`) ou arquivo.

## 4. Domínio

Deduza do nome das rotas, tabelas e entidades (ex.: `produtos/pedidos/usuarios` → E-commerce;
`courses/enrollments/payments` → LMS com checkout; `tasks/categories/users` → Task Manager).
Descreva em uma linha, listando as entidades principais.

## 5. Mapeamento da arquitetura atual

Responda às perguntas, anotando os arquivos:

1. Onde está o **entry point** e a criação do app/servidor? (`app.py`, `src/app.js`, `main.go`)
2. Onde estão as **rotas**? Ficam no mesmo arquivo que a lógica ou separadas?
3. Existe camada de **controllers/services**? Ou a regra de negócio vive nas rotas?
4. Onde está o **acesso a dados**? (SQL cru em models? ORM nas rotas?)
5. Onde está a **configuração** (porta, segredos, caminho do DB)? Hardcoded?
6. Existe **tratamento centralizado de erros**/middleware?
7. Há **estado global** mutável (variáveis de módulo, singletons, caches)?

Classifique:

| Classificação | Maturidade | Critério |
|---|---|---|
| Monolítica total / God Class | **1/5** | Tudo em 1-3 arquivos; uma classe/módulo concentra rotas + DB + negócio |
| Separação mínima | **2/5** | Arquivos `app + models + controllers` no mesmo nível, mas com SQL/regra misturados |
| Parcialmente em camadas | **2.5/5 – 3/5** | Existem `models/` e `routes/`, mas lógica de negócio e queries vazam para as rotas, sem controllers |
| MVC completo | **4/5** | Camadas `config`, `models`, `controllers`, `routes`, `middlewares` separadas e com responsabilidades corretas |
| Clean / Hexagonal | **5/5** | Portas e adaptadores, inversão de dependência e testes automatizados por camada |

## 6. Tabelas de Referência de APIs Deprecated por Framework/Versão

Ao inspecionar os arquivos na Fase 1 e Fase 2, cruze com esta tabela:

| Tecnologia / Versão | API / Padrão Deprecated | Substituto Moderno |
|---|---|---|
| **Python 3.12+** | `datetime.utcnow()` / `datetime.utcfromtimestamp()` | `datetime.now(timezone.utc)` / `datetime.fromtimestamp(ts, timezone.utc)` |
| **SQLAlchemy 2.0+** | `Model.query.get(id)` / `Query.get()` | `db.session.get(Model, id)` |
| **Flask 2.3+** | `@app.before_first_request` | Inicializar dentro de `with app.app_context():` no `create_app()` |
| **Flask 2.2+** | `flask.json.JSONEncoder` / `JSON_SORT_KEYS` | `app.json` provider |
| **Express 4.x** | `res.json(status, body)` / `res.send(status)` | `res.status(status).json(body)` / `res.sendStatus(status)` |
| **Express 4.x** | `req.param('id')` / `app.del()` | `req.params.id`, `req.query`, `req.body` / `app.delete()` |
| **Node.js / SQLite3** | Callbacks aninhados `(err, row) =>` / `new Buffer()` | `Promises` + `async/await` / `Buffer.from()` |
| **Criptografia (Geral)** | `hashlib.md5()` / `sha1()` / Base64 para senhas | `werkzeug.security.generate_password_hash` / `crypto.scryptSync` / `bcrypt` |

## 7. Métricas

- **Source files**: arquivos de código de aplicação (exclua dependências, lockfiles, bancos, docs, seeds se forem scripts auxiliares — mencione-os se incluídos).
- **LOC**: `wc -l` nos arquivos analisados.
- Ordem sugerida de comandos (agnóstica): listar arquivos (`find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*'`), ler manifesto, ler entry point, ler o restante.

## 7. Como descobrir os endpoints (para validação na Fase 3)

Extraia todas as rotas (método + path) do código de roteamento e de arquivos de exemplo
(`api.http`, README, coleções). Monte uma lista numerada: ela é a base do baseline e da validação final.

