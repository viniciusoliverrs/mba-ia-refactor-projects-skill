```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express 4.18.2
Dependencies:  express ^4.18.2, sqlite3 ^5.1.6
Domain:        LMS API com fluxo de checkout (usuários, cursos, matrículas, pagamentos, auditoria e relatório financeiro)
Architecture:  God Class — 3 arquivos em src/, com AppManager concentrando conexão SQLite, DDL/seeds, rotas HTTP e regras de negócio
Maturity:      1/5 (No Architecture — God Class monolítica)
Source files:  3 files analyzed (~180 LOC)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite em memória :memory:)
Entry point:   src/app.js
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 3 | HIGH: 4 | MEDIUM: 4 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets & Vazamento em Log (AP-01)
File: src/utils.js:1-7, src/AppManager.js:45
Description: Objeto `config` contém credenciais de produção hardcoded (`dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`,
`paymentGatewayKey: "pk_live_1234567890abcdef"`, `smtpUser: "no-reply@fullcycle.com.br"`); além disso, o fluxo de checkout executa
`console.log("Processando cartão " + cc + " na chave " + config.paymentGatewayKey)`, gravando o número completo do cartão de crédito (PAN)
e a chave privada do gateway em texto puro no stdout.
Impact: Exposição direta de segredos de produção e violação grave de segurança (PCI-DSS) por logar dados de cartão e chaves de API.
Recommendation: Extrair configurações para `src/config/settings.js` lendo `process.env` (PB-01) e jamais registrar PAN de cartão ou chaves em logs (PB-16).

### [CRITICAL] God Class / Violação Total de Camadas MVC (AP-03)
File: src/AppManager.js:4-139
Description: A classe `AppManager` acumula instanciação do banco (`new sqlite3.Database(':memory:')`), criação de tabelas e seeds (`initDb`),
registro de rotas Express (`setupRoutes`), validação de request, simulação de gateway de pagamento, persistência em 5 tabelas e agregação de
relatório financeiro. Não existem camadas `models/`, `controllers/` ou `routes/`.
Impact: Acoplamento extremo entre HTTP, regras de negócio e SQLite; impossível testar regras ou reutilizar queries isoladamente.
Recommendation: Decompor `AppManager` em `src/database/`, `src/models/` (por entidade), `src/controllers/` e `src/routes/` (PB-03).

### [CRITICAL] Hash de Senha Caseiro Inseguro (`badCrypto`) e Senha Fraca em Seed (AP-04)
File: src/utils.js:17-23, src/AppManager.js:18, src/AppManager.js:68
Description: A função `badCrypto(pwd)` não utiliza algoritmo criptográfico: apenas repete `Buffer.from(pwd).toString('base64').substring(0, 2)`
10.000 vezes em loop bloqueante na event loop e trunca para 10 caracteres (entropia de apenas 2 caracteres Base64 da senha original, reversível
e com colisão total para senhas com os mesmos 2 primeiros bytes). O seed inicial grava senha `'123'` em texto puro (`AppManager.js:18`) e o
checkout usa fallback `"123456"` quando `pwd` não é enviado (`AppManager.js:68`).
Impact: Comprometimento trivial de todas as senhas de usuários e bloqueio desnecessário da thread principal do Node.js.
Recommendation: Substituir `badCrypto` por `crypto.scryptSync` com salt aleatório (`crypto.randomBytes(16)`) e exigir senha válida no cadastro (PB-04).

### [HIGH] Regra de Negócio Acoplada às Rotas (Fat Routes) (AP-06)
File: src/AppManager.js:28-78, src/AppManager.js:80-129, src/AppManager.js:131-137
Description: Os handlers de `POST /api/checkout`, `GET /api/admin/financial-report` e `DELETE /api/users/:id` contêm toda a lógica de
negócio, regras de aprovação de cartão, orquestração de matrícula/pagamento/auditoria e queries SQL diretamente dentro do callback da rota.
Impact: Viola o padrão MVC e o princípio da responsabilidade única (SRP), impedindo testes unitários dos fluxos de checkout e relatórios.
Recommendation: Extrair a lógica para `checkoutController`, `reportController` e `userController`, deixando as rotas apenas com o mapeamento HTTP (PB-06).

### [HIGH] Estado Global Mutável e Acoplamento sem Injeção de Dependência (AP-07)
File: src/utils.js:9-15, src/AppManager.js:5-8, src/app.js:8-10
Description: `globalCache` e `totalRevenue` são variáveis globais mutáveis exportadas por `src/utils.js`; `logAndCache` altera `globalCache`
sem limite de memória (memory leak); `AppManager` instancia `new sqlite3.Database(':memory:')` diretamente no construtor sem permitir injeção.
Impact: Estado compartilhado imprevisível entre requisições, vazamento de memória em execução prolongada e dificuldade de testar com dublês.
Recommendation: Encapsular conexão de banco em `src/database/connection.js`, injetar models nos controllers e remover estado global mutável (PB-07).

### [HIGH] Quebra de Integridade Referencial e Ausência de Transação (AP-08)
File: src/AppManager.js:50-63, src/AppManager.js:131-137
Description: Em `DELETE /api/users/:id` (`AppManager.js:131-137`), o código executa apenas `DELETE FROM users WHERE id = ?` e responde
explicitamente `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."`, deixando registros órfãos em `enrollments` e `payments`.
Além disso, o checkout realiza múltiplos `INSERT` sequenciais (`users`, `enrollments`, `payments`, `audit_logs`) fora de uma transação atômica.
Impact: Banco de dados inconsistente, matrículas e pagamentos órfãos no relatório financeiro (`student: 'Unknown'`) e dados parciais em caso de falha.
Recommendation: Executar operações multi-tabela dentro de transação (`BEGIN` / `COMMIT` / `ROLLBACK`) e remover em cascata pagamentos e matrículas ao deletar usuário (PB-08).

### [HIGH] Callback Hell e Sincronização Manual Assíncrona (AP-09)
File: src/AppManager.js:37-77, src/AppManager.js:83-128
Description: O endpoint `/api/checkout` aninha até 6 níveis de callbacks do `sqlite3` (misturando `this.db` e `self.db`), e `/api/admin/financial-report`
usa contadores mutáveis manuais (`coursesPending--`, `enrPending--`) dentro de `forEach` assíncronos para descobrir quando responder `res.json(report)`.
Impact: Código frágil, difícil de ler e propenso a race conditions ou respostas HTTP duplicadas/penduradas se ocorrer erro em qualquer callback interno.
Recommendation: Promisificar o acesso ao `sqlite3` (`run`, `get`, `all`) e refatorar todos os fluxos para `async/await` (PB-09).

### [MEDIUM] N+1 Queries no Relatório Financeiro (AP-10)
File: src/AppManager.js:83-127
Description: `GET /api/admin/financial-report` executa 1 query para listar cursos (`SELECT * FROM courses`), depois 1 query por curso para buscar
matrículas (`SELECT * FROM enrollments WHERE course_id = ?`), e para cada matrícula executa mais 2 queries individuais (`SELECT name, email FROM users`
e `SELECT amount, status FROM payments`), totalizando `1 + C + 2*E` queries.
Impact: Degradação severa de latência conforme o número de cursos e matrículas cresce.
Recommendation: Substituir o loop de queries por uma consulta com `LEFT JOIN` entre `courses`, `enrollments`, `users` e `payments` e agregar em memória (PB-10).

### [MEDIUM] Tratamento de Erros Inconsistente e Sem Middleware Central (AP-11)
File: src/AppManager.js:38, src/AppManager.js:41, src/AppManager.js:51, src/AppManager.js:55, src/AppManager.js:57, src/AppManager.js:70, src/AppManager.js:84, src/AppManager.js:92, src/AppManager.js:104, src/AppManager.js:106, src/AppManager.js:133
Description: Alguns callbacks retornam texto puro (`res.status(500).send("Erro DB")`), enquanto outros ignoram completamente o parâmetro `err`
(`audit_logs` na linha 57, `enrollments` na linha 92, `users` na linha 104, `payments` na linha 106, `DELETE users` na linha 133). Não há middleware de erro Express.
Impact: Erros silenciosos de banco de dados passam despercebidos e a API mistura respostas texto puro e JSON sem padronização.
Recommendation: Criar `src/middlewares/errorHandler.js` e classes de erro de domínio, encaminhando falhas via `next(err)` (PB-11).

### [MEDIUM] Validação de Entrada Fraca no Checkout e Exclusão (AP-12)
File: src/AppManager.js:29-35, src/AppManager.js:46, src/AppManager.js:131-133
Description: O checkout não valida tipo/formato de `eml`, `c_id` ou `card` (ex.: se `card` não for string, `cc.startsWith("4")` lança `TypeError`
e derruba a requisição); `DELETE /api/users/:id` não valida o ID nem verifica se o usuário existe.
Impact: Exceções não tratadas (`TypeError`) com payloads malformados e falta de feedback adequado ao cliente.
Recommendation: Validar tipos e campos obrigatórios no controller antes de chamar os models (PB-12).

### [MEDIUM] Uso de Padrões e APIs Obsoletas / Deprecated (AP-14)
File: src/AppManager.js:1, src/AppManager.js:26-128, src/utils.js:17-23
Description: Uso de callbacks legados `(err, row) =>` com `const self = this` em vez de `Promises`/`async-await`, `sqlite3.verbose()` ativo
incondicionalmente, declarações `let` onde deveriam ser `const`, e implementação manual insegura de hash (`badCrypto`) em vez da API nativa `crypto.scryptSync`.
Impact: Código verboso, propenso a erros de escopo (`this` vs `self`) e desalinhado com Node.js moderno.
Recommendation: Adotar `async/await` com wrappers baseados em Promise, `const` por padrão e `crypto.scryptSync` (PB-14).

### [LOW] Magic Numbers e Strings Hardcoded de Regra de Negócio (AP-15)
File: src/AppManager.js:46, src/AppManager.js:68, src/utils.js:19-22
Description: Prefixo `"4"` para aprovação de cartão, status `'PAID'`/`'DENIED'`, senha fallback `"123456"` e constantes `10000`/`10` espalhadas no código.
Impact: Dificulta leitura e manutenção das regras de pagamento e matrícula.
Recommendation: Extrair constantes nomeadas para `src/config/constants.js` (PB-15).

### [LOW] Uso de `console.log` Direto para Auditoria e Cache (AP-16)
File: src/app.js:13, src/AppManager.js:45, src/utils.js:13
Description: Uso direto de `console.log` espalhado para eventos de servidor, cache e processamento de pagamento.
Impact: Logs sem nível de severidade nem padronização.
Recommendation: Centralizar logs em `src/utils/logger.js` sem expor dados sensíveis (PB-16).

### [LOW] Nomenclatura Críptica de Variáveis (AP-17)
File: src/AppManager.js:26, src/AppManager.js:29-33, src/AppManager.js:52, src/AppManager.js:89-106
Description: Variáveis abreviadas de 1 a 3 letras (`u`, `e`, `p`, `cid`, `cc`, `enrId`, `c`, `enr`, `self`) dificultam a compreensão imediata do fluxo.
Impact: Baixa legibilidade e maior custo cognitivo na manutenção.
Recommendation: Desestruturar o payload mantendo os nomes externos do contrato (`usr`, `eml`, `pwd`, `c_id`, `card`) mas atribuindo a variáveis internas descritivas (`userName`, `email`, `password`, `courseId`, `cardNumber`) (PB-17).

### [LOW] Código Morto / Variável Exportada e Nunca Utilizada (AP-18)
File: src/utils.js:10, src/utils.js:25, src/AppManager.js:2
Description: A variável `totalRevenue` é declarada, exportada em `src/utils.js` e importada em `src/AppManager.js`, mas nunca é lida ou atualizada.
Impact: Ruído e confusão sobre qual é a fonte da verdade da receita financeira.
Recommendation: Remover `totalRevenue` e variáveis mortas (PB-18).

================================
Total: 15 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y   (confirmado pelo usuário ao aprovar o plano de execução)
```

```
================================
PHASE 3: REFACTORING COMPLETE
================================
Architecture: God Class (3 arquivos) -> Layered MVC + Services (18 arquivos)
Maturity:     1/5 -> 4/5
Findings resolved: 15/15 (3 CRITICAL, 4 HIGH, 4 MEDIUM, 4 LOW)
Endpoints verified: 4/4 (/health, POST /api/checkout, GET /api/admin/financial-report, DELETE /api/users/:id)
================================
```

### Revalidação por Impact (2ª execução da Fase 3)

Na 1ª execução, `src/database/connection.js` exportava `dbConnection = new DatabaseConnection()` (abre o SQLite no `require`) e `createApp()` criava o schema dentro da factory (AP-07 não estava de fato resolvido: conexão global criada no import).
Correção (PB-07b): sem singleton no módulo; `src/app.js::createApp(db)` é factory pura; `new DatabaseConnection()` e `initDatabase(db)` ocorrem só sob `require.main === module`.

| Finding | Verificação | Resultado |
|---|---|---|
| AP-07 | `DB_PATH=/tmp/w2/p2.db node -e "require('./src/app'); require('./src/database/connection')"` → arquivo **não** criado | RESOLVED |
| Boot + endpoints | `npm start`: `/health` 200, `GET /api/admin/financial-report` 200, `POST /api/checkout` 200, `DELETE /api/users/1` 200 | RESOLVED |
| AP-01 | Checkout com cartão completo: nenhuma linha de log contém o PAN ou chaves; só `cardLast4` | RESOLVED |
| AP-04 | Todos os hashes em `users.pass` no formato `salt(32 hex):scrypt(64 hex)` | RESOLVED |
| AP-08 | Novo usuário sem senha → 400 e usuário **não** criado; cartão recusado → 400 e 0 matrículas novas; `DELETE /api/users/:id` → 0 matrículas e 0 pagamentos órfãos | RESOLVED |
| AP-10 | `GET /api/admin/financial-report` com 5 matrículas → **1** query (antes 1+C+2E) | RESOLVED |
| AP-11/AP-12 | Payload vazio / tipos inválidos / id `abc` → 400 JSON; **rota inexistente → 404 JSON** e **JSON malformado → 400** (ambos reproduziam resposta HTML/500 antes da correção em `errorHandler.js`) | RESOLVED (corrigido nesta rodada) |
| AP-03/06/09/14/15/16/17/18 | Verificação estrutural: `grep` sem `console.log`, `badCrypto`, `globalCache`, `totalRevenue`, `self = this`; fluxo 100% `async/await`; controllers ≤ 98 linhas (não são provas comportamentais) | RESOLVED (estrutural) |
