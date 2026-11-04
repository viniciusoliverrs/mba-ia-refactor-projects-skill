# Guidelines de Arquitetura — MVC Alvo (Fase 3)

Padrão alvo para APIs backend (a "View" numa API é a camada de **roteamento/serialização da resposta**).

## Camadas e responsabilidades

| Camada | Responsabilidade | Pode depender de | NUNCA faz |
|---|---|---|---|
| **config/** | Ler configuração de ambiente (porta, segredos, caminho do DB, flags), constantes de domínio | — | Hardcodar segredos |
| **models/** | Acesso a dados: queries parametrizadas, mapeamento row→dict/entidade, schema/seed, transações | config | Regra de negócio, `request/response`, HTTP |
| **controllers/** | Fluxo da aplicação: valida entrada, aplica regra de negócio, orquestra models, devolve resultado/erro de domínio | models, config | SQL direto, conhecer detalhes do framework HTTP além de request/response mínimos |
| **views/** (ou **routes/**) | Mapear método+path → controller; serializar resposta e status code | controllers | Regra de negócio, acesso a dados |
| **middlewares/** | Preocupações transversais: error handler central, logging, auth | — | Regra de negócio |
| **app (entry point)** | Composition root: cria app, carrega config, inicializa DB, registra rotas e middlewares, sobe servidor | todos | Lógica de negócio |

Fluxo de dependência: `routes → controllers → models → database` (nunca o contrário).

## Estrutura de diretórios sugerida

Python/Flask:
```
app.py                  # composition root
config/settings.py
models/<dominio>_model.py
controllers/<dominio>_controller.py
routes/<dominio>_routes.py   (ou views/)
middlewares/error_handler.py
utils/                  # helpers puros, sem I/O
```

Node/Express:
```
src/
  app.js                # composition root
  config/settings.js
  database/connection.js
  models/<dominio>Model.js
  controllers/<dominio>Controller.js
  routes/index.js (+ <dominio>Routes.js)
  middlewares/errorHandler.js
  utils/
```

Projeto **já em camadas** (ex.: `models/ routes/ services/`): preserve a nomenclatura existente, acrescente o que falta
(normalmente `controllers/`, `config/`, `middlewares/`), mova regra de negócio das rotas para controllers e
queries das rotas para models/repositórios. Não renomeie por renomear.

## Regras

1. **Configuração via ambiente**: `os.environ.get("X", default_dev)` / `process.env.X || default`. Segredos reais nunca versionados; defaults apenas para desenvolvimento e sem valores sensíveis reais.
2. **Models**: uma responsabilidade por agregado (produto, usuário, pedido...). Somente SQL parametrizado (`?`/`%s`/ORM). Retornam estruturas simples (dict/objeto); **nunca** retornam campos sensíveis (hash de senha).
3. **Controllers**: funções/classes sem conhecimento de SQL. Validam entrada, aplicam regras (ex.: estoque, desconto), chamam models. Sinalizam erros com **exceções de domínio** (`ValidationError`, `NotFoundError`, `AuthError`) capturadas pelo error handler.
4. **Routes/Views**: finas — extraem dados do request, chamam o controller, devolvem `jsonify(...)`/`res.json(...)` com o status adequado. Agrupe por domínio (Blueprint/Router).
5. **Error handling centralizado**: um único handler converte exceções de domínio em `{erro: msg}` + status; exceções inesperadas viram 500 genérico (sem vazar `str(e)`/stacktrace) e são logadas.
6. **Entry point claro**: `app.py`/`src/app.js` apenas monta a aplicação (factory `create_app()` quando fizer sentido).
7. **Sem estado global mutável**: conexões/serviços criados no composition root e injetados (ou módulo com acesso encapsulado e thread-safe).
   - **Import sem efeitos colaterais**: importar qualquer módulo (inclusive o entry point) não cria app, conexão, arquivo de banco, tabelas nem sobe servidor. O entry point expõe apenas a factory (`create_app()`/`createApp()`); a instância e a criação do schema (`db.create_all()`/`init_db()`) ficam atrás de `if __name__ == "__main__"` / `require.main === module`, de um comando CLI ou do seed. A factory é pura (só monta config, extensões, middlewares e rotas). Padrão completo em PB-07b.
8. **Transações** em operações multi-etapa; integridade referencial em deleções.
9. **Logging** via `logging` / logger configurável, não `print`/`console.log`.
10. **Contrato preservado**: mesmas rotas, métodos, nomes de campos e status codes. Mudanças inevitáveis (ex.: remover senha/segredo das respostas) ficam documentadas.

## Checklist de aceitação da Fase 3

- [ ] Estrutura de diretórios MVC criada
- [ ] Configuração extraída para módulo de config (sem segredos hardcoded)
- [ ] Models abstraem os dados (sem SQL fora de models)
- [ ] Views/Routes só roteiam
- [ ] Controllers concentram o fluxo e as regras
- [ ] Error handling centralizado
- [ ] Entry point claro (composition root)
- [ ] Import sem efeitos colaterais: sem `app = create_app()`, `create_all()`/DDL, `listen()` ou conexão no escopo de módulo ou dentro da factory
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem como antes (exceto correções de segurança documentadas)

