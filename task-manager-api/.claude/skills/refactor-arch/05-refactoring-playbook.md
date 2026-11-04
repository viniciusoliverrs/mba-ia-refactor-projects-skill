# Playbook de Refatoração (Fase 3)

Cada padrão **PB-xx** corrige o anti-pattern **AP-xx** correspondente do [catálogo](anti-patterns-catalog.md).
Exemplos em Python/Flask e Node/Express; adapte para outras stacks mantendo a ideia.

---

## PB-01 — Extrair segredos para config/ambiente (AP-01)

Antes (Python):
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
return jsonify({"secret_key": "minha-chave-super-secreta-123", "debug": True})
```
Depois:
```python
# config/settings.py
import os
class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("APP_DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    PORT = int(os.environ.get("PORT", "5000"))
# /health nunca devolve segredos nem flags internas
```
Antes (Node):
```js
const config = { dbPass: "senha_super_secreta_prod_123", paymentGatewayKey: "pk_live_123", port: 3000 };
console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`);
```
Depois:
```js
// config/settings.js
module.exports = {
  port: Number(process.env.PORT) || 3000,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || "",
};
// log sem dados sensíveis: logger.info(`Processando pagamento do curso ${courseId}`)
```

## PB-02 — Queries parametrizadas (AP-02)

Antes:
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO produtos (nome) VALUES ('" + nome + "')")
```
Depois:
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO produtos (nome) VALUES (?)", (nome,))
# LIKE: params.append(f"%{termo}%") e "nome LIKE ?"
# filtros dinâmicos: monte a lista de condições com placeholders e a lista de params
```
Node: `db.get("SELECT * FROM users WHERE email = ?", [email], cb)` (já parametrizado: mantenha).

## PB-03 — Quebrar God Class/Module por camada e domínio (AP-03)

Antes: `models.py` (314 linhas) com produtos + usuários + pedidos + relatórios + regras; `AppManager.js` com DB + rotas + checkout.
Depois:
```
models/produto_model.py  usuario_model.py  pedido_model.py  relatorio_model.py
controllers/produto_controller.py ...
routes/produto_routes.py ...
```
Passos: (1) liste responsabilidades; (2) mova cada função para o arquivo do domínio; (3) rotas viram arquivos
de routes que apenas chamam controllers; (4) schema/seed vão para `database/`; (5) apague o arquivo antigo.

## PB-04 — Hash de senha seguro e não expor credenciais (AP-04)

Antes:
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
def to_dict(self): return {..., "password": self.password}
cursor.execute("SELECT * FROM usuarios WHERE email='"+email+"' AND senha='"+senha+"'")
```
Depois:
```python
from werkzeug.security import generate_password_hash, check_password_hash
self.password = generate_password_hash(pwd)          # scrypt/pbkdf2 com salt
def check_password(self, pwd): return check_password_hash(self.password, pwd)
def to_dict(self): return {"id": self.id, "name": self.name, "email": self.email}  # sem senha
# login: buscar por email (parametrizado) e verificar o hash em código
```
Compatibilidade: ao verificar, aceite hashes legados (ex.: texto puro/md5 já gravados) e **re-hash no login bem-sucedido**;
seeds devem gravar com o novo hash.
Node:
```js
const crypto = require('crypto');
const hashPassword = (pwd) => {
  const salt = crypto.randomBytes(16).toString('hex');
  return `${salt}:${crypto.scryptSync(pwd, salt, 32).toString('hex')}`;
};
```

## PB-05 — Neutralizar endpoints administrativos perigosos (AP-05)

Antes:
```python
@app.route("/admin/query", methods=["POST"])
def executar_query(): cursor.execute(request.get_json()["sql"])
```
Depois: remova `/admin/query` (execução arbitrária de SQL é indefensável). Para `/admin/reset-db`, proteja com
token de admin vindo de config e habilite só fora de produção:
```python
def require_admin(): 
    if request.headers.get("X-Admin-Token") != Settings.ADMIN_TOKEN or not Settings.ADMIN_TOKEN:
        raise AuthError("Acesso negado")
```
`debug=True` → `Settings.DEBUG` (padrão `False`). Documente a mudança de contrato no resumo.

## PB-06 — Mover regra de negócio de rotas para controllers (AP-06)

Antes:
```python
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json(); ...30 linhas de validação + db.session.add + commit...
```
Depois:
```python
# routes/task_routes.py
@task_bp.route('/tasks', methods=['POST'])
def create_task():
    task = task_controller.create_task(request.get_json())
    return jsonify(task), 201
# controllers/task_controller.py  -> valida, aplica regras, usa Task/ models
```
Regra: a rota tem ≤10 linhas; o controller não importa `flask.request`; models/queries ficam em model.

## PB-07 — Eliminar estado global; injetar dependências (AP-07)

Antes:
```python
db_connection = None
def get_db():
    global db_connection ...
```
```js
let globalCache = {}; module.exports = { globalCache, totalRevenue };
```
Depois:
```python
# database/connection.py
def get_connection():            # conexão por requisição (flask.g) ou factory explícita
    if "db" not in g: g.db = sqlite3.connect(Settings.DB_PATH); g.db.row_factory = sqlite3.Row
    return g.db
@app.teardown_appcontext
def close_db(exc): conn = g.pop("db", None); conn and conn.close()
```
```js
class CheckoutController { constructor({ userModel, courseModel, logger }) { ... } }
// composition root monta e injeta; cache vira classe/serviço injetado ou é removido se não usado
```

### PB-07b — Import sem efeitos colaterais: app e schema fora do escopo de módulo (AP-07)

Importar um módulo (`import app`, `from app import ...`, `import seed`, testes) **nunca** pode abrir conexão, criar arquivo de banco,
criar tabelas, semear dados ou subir servidor. Montar a app e criar o schema são ações **explícitas**.

Antes:
```python
# app.py
def create_app():
    ...
    with flask_app.app_context():
        db.create_all()          # efeito colateral no banco
    return flask_app

app = create_app()               # roda no import -> seed.py (from app import app) já cria/toca tasks.db
```
```js
const app = express(); db.serialize(() => db.run("CREATE TABLE ..."));   // schema criado no require()
app.listen(3000);                                                       // servidor sobe no require()
```
Depois:
```python
# app.py  -> factory pura: só monta objetos, sem I/O de banco
def create_app(config=Settings):
    flask_app = Flask(__name__); flask_app.config.from_object(config)
    db.init_app(flask_app); register_error_handlers(flask_app); register_routes(flask_app)
    return flask_app             # SEM db.create_all(), SEM app = create_app() no módulo

if __name__ == "__main__":       # somente execução direta cria app, schema e sobe servidor
    app = create_app()
    with app.app_context():
        db.create_all()          # (ou init_db(): função explícita, idempotente)
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)

# seed.py -> cria sua própria app e inicializa o schema DENTRO da função
def seed_data():
    app = create_app()
    with app.app_context():
        db.create_all(); ...
```
```js
// src/app.js -> exporta createApp(); schema em initDb() chamado só no entry point
async function createApp() { /* monta e retorna app, sem listen */ }
if (require.main === module) { initDb().then(createApp).then(app => app.listen(port)); }
```
Regras:
1. Nenhum `app = create_app()`, `db.create_all()`, `init_db()`, `listen()` ou `connect()` no nível do módulo nem dentro da factory.
2. Criação de schema/migração vive em função nomeada (`init_db`, `initDb`) chamada apenas pelo entry point (`__main__`/`require.main`), pelo seed ou por um comando CLI.
3. Servidores WSGI usam a factory (`flask --app app:create_app run` / `gunicorn "app:create_app()"`), não uma instância global.
4. Testes criam a app com config própria (ex.: `sqlite:///:memory:`) via `create_app(TestConfig)`.
5. **Prova**: importar o módulo com `DATABASE_URL` apontando para um arquivo inexistente **não pode criá-lo** (ver validação da Fase 3).

## PB-08 — Transações e integridade referencial (AP-08)

Antes:
```python
cursor.execute("INSERT INTO pedidos ..."); ...; cursor.execute("UPDATE produtos SET estoque = estoque - ...")
db.commit()   # erro no meio deixa dados inconsistentes
```
Depois:
```python
try:
    cursor.execute("BEGIN")
    ... inserts/updates ...
    db.commit()
except Exception:
    db.rollback(); raise
# estoque: UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?  (verifique rowcount)
```
Deleção em cascata (Node):
```js
await run("DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)", [id]);
await run("DELETE FROM enrollments WHERE user_id = ?", [id]);
await run("DELETE FROM users WHERE id = ?", [id]);   // dentro de BEGIN/COMMIT
```

## PB-09 — Callbacks → async/await (AP-09)

Antes:
```js
this.db.get(sql, [cid], (err, course) => { this.db.get(sql2, [e], (err, user) => { ... }) })
```
Depois:
```js
// database/connection.js: promisifique run/get/all
const get = (sql, p = []) => new Promise((res, rej) => db.get(sql, p, (e, r) => (e ? rej(e) : res(r))));
// controller
async checkout(req, res, next) {
  try {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError("Curso não encontrado");
    ...
  } catch (err) { next(err); }
}
```

## PB-10 — Eliminar N+1 (AP-10)

Antes:
```python
for row in pedidos:
    itens = cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens: cursor3.execute("SELECT nome FROM produtos WHERE id = ...")
```
Depois:
```python
rows = cursor.execute("""
  SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
         i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
  FROM pedidos p
  LEFT JOIN itens_pedido i ON i.pedido_id = p.id
  LEFT JOIN produtos pr ON pr.id = i.produto_id
""").fetchall()
# agrupe por pedido em um dict em memória
```
SQLAlchemy: `Task.query.options(joinedload(Task.user), joinedload(Task.category))`; contagens com
`db.session.query(Task.user_id, func.count()).group_by(Task.user_id)`.
Node: um único `SELECT ... JOIN` + agregação em JS.

## PB-11 — Error handling centralizado (AP-11)

Antes: `try: ... except Exception as e: return jsonify({"erro": str(e)}), 500` em cada handler.
Depois:
```python
# middlewares/error_handler.py
class AppError(Exception): status = 500
class ValidationError(AppError): status = 400
class NotFoundError(AppError): status = 404
def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app(e): return jsonify({"erro": str(e), "sucesso": False}), e.status
    @app.errorhandler(Exception)
    def handle_unexpected(e):
        app.logger.exception("Erro inesperado"); return jsonify({"erro": "Erro interno do servidor"}), 500
```
Node: `app.use((err, req, res, next) => res.status(err.status || 500).json({ erro: err.status ? err.message : "Erro interno" }))`.
Troque `except:` nu por `except SQLAlchemyError`/exceções específicas.

## PB-12 — Validação centralizada de entrada (AP-12)

Antes: validações copiadas em `criar_produto` e `atualizar_produto`; `request.get_json()` sem checar `None`.
Depois:
```python
# controllers/produto_controller.py
def _validar_produto(dados):
    if not isinstance(dados, dict): raise ValidationError("Dados inválidos")
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados: raise ValidationError(f"{campo.capitalize()} é obrigatório")
    ...
# criar e atualizar chamam a mesma função
```
Para query params: converta com try/except e devolva 400 em vez de 500.

## PB-13 — Remover duplicação (AP-13)

Antes: bloco `overdue` copiado em 5 rotas; row→dict repetido 4 vezes.
Depois:
```python
# models/task.py (já existe is_overdue) -> use-o
data["overdue"] = task.is_overdue()
# models: def _row_to_produto(row): return {...}  # usado em todas as consultas
```
Prefira reaproveitar métodos/helpers existentes antes de criar novos.

## PB-14 — Substituir APIs deprecated (AP-14)

```python
# antes                                   # depois
User.query.get(user_id)                   db.session.get(User, user_id)
datetime.utcnow()                         datetime.now(timezone.utc)   # default=lambda: datetime.now(timezone.utc)
hashlib.md5(...)                          werkzeug.security.generate_password_hash(...)
```
```js
new Buffer(x)  ->  Buffer.from(x)       callbacks -> async/await       var -> const/let
```
Atenção: com `datetime.now(timezone.utc)` (aware) comparar com colunas naive do SQLite quebra; use
`datetime.now(timezone.utc).replace(tzinfo=None)` ou normalize ambos os lados em um helper único (`utils/time.py: utcnow()`).

## PB-15 — Constantes nomeadas (AP-15)

Antes: `if faturamento > 10000: desconto = faturamento * 0.1`
Depois:
```python
# config/constants.py
FAIXAS_DESCONTO = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
STATUS_PEDIDO = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
def calcular_desconto(valor):
    return next((valor * pct for limite, pct in FAIXAS_DESCONTO if valor > limite), 0)
```

## PB-16 — Logger no lugar de print/console.log (AP-16)

Antes: `print("ENVIANDO EMAIL: ...")`, `console.log("[LOG] ...")`
Depois:
```python
import logging; logger = logging.getLogger(__name__)
logger.info("Pedido %s criado para usuário %s", pedido_id, usuario_id)
```
```js
const logger = require('../utils/logger'); // wrapper fino: info/error com timestamp
```
Efeitos colaterais (e-mail/SMS) vão para um service de notificação (`services/notification_service`), não para o controller.

## PB-17 — Nomes expressivos (AP-17)

Antes: `let u = req.body.usr; let cid = req.body.c_id; let cc = req.body.card;`
Depois:
```js
const { usr: userName, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;
```
Renomeie apenas identificadores internos; **mantenha** os nomes de campos do contrato HTTP.

## PB-18 — Remover código morto e imports não usados (AP-18)

Antes: `import os, sys, json, time`; `totalRevenue` exportado e nunca usado; `type(tags) == list`; `if x: return True else: return False`.
Depois: apague imports/variáveis mortas; `isinstance(tags, list)`; `return self.role == 'admin'`.
Confirme com grep que o símbolo não é usado antes de remover (inclusive em scripts como `seed.py`).

---

## Ordem de aplicação recomendada

1. PB-01 → 2. PB-14 (APIs) → 3. PB-03 (estrutura) → 4. PB-02/PB-04/PB-05 (segurança no model)
→ 5. PB-10/PB-08 (performance/integridade) → 6. PB-06/PB-12/PB-13 (controllers) → 7. PB-11 (erros)
→ 8. PB-07/PB-09 (estado/async) → 9. PB-15..18 (limpeza) → 10. validação.

