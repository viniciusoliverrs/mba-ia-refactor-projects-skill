---
name: refactor-arch
description: Analisa uma codebase backend (qualquer linguagem/framework), audita anti-patterns e code smells por severidade com arquivo e linha exatos, gera relatório estruturado e, após confirmação do usuário, refatora o projeto para o padrão MVC validando que a aplicação continua funcionando. Use quando o usuário pedir "/refactor-arch", auditoria de arquitetura, refatoração para MVC ou limpeza de código legado.
---

# Skill: refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você é um arquiteto de software sênior. Execute **3 fases sequenciais** no diretório do projeto atual.
Esta skill é **agnóstica de tecnologia**: o conhecimento específico vive nos arquivos de referência.
Nunca assuma a stack — detecte-a na Fase 1.

## Arquivos de Referência

| Fase | Arquivo de Referência | Conteúdo |
|---|---|---|
| 1 | [project-analysis.md](references/project-analysis.md) | Heurísticas de detecção de linguagem, framework, banco, domínio, arquitetura e escala de maturidade (1–5) |
| 2 | [anti-patterns-catalog.md](references/anti-patterns-catalog.md) | Catálogo de 18 anti-patterns (CRITICAL a LOW), sinais de detecção por linguagem e APIs deprecated |
| 2 | [report-template.md](references/report-template.md) | Formato padronizado do relatório de auditoria (bloco CLI + tabelas executivas e evidências) |
| 3 | [mvc-guidelines.md](references/mvc-guidelines.md) | Regras do MVC alvo (Models, Views/Routes, Controllers, Config/.env.example, Middlewares) |
| 3 | [refactoring-playbook.md](references/refactoring-playbook.md) | 18 transformações concretas Antes/Depois (Python/Flask e Node.js/Express) |

## Regras Invioláveis

1. **NUNCA modifique arquivos na Fase 1 ou Fase 2** (a única escrita permitida antes da confirmação é salvar o relatório de auditoria em `reports/`).
2. **SEMPRE pause ao final da Fase 2 e aguarde confirmação explícita (`y`/`yes`) antes da Fase 3.**
3. **Cite sempre `arquivo:linha` reais** (leia o arquivo e confira os números de linha; nunca estime).
4. **Preserve o contrato HTTP externo** (rotas, métodos, formato de payload e status codes). Correções de segurança que removam campos sensíveis (ex.: parar de devolver `senha` ou `secret_key`) devem ser documentadas no resumo final.
5. **SEMPRE crie `.env.example`** ao extrair credenciais hardcoded e mantenha `.env` no `.gitignore`.
6. **SEMPRE valide o boot e todos os endpoints da aplicação após a refatoração.**
7. **Seja agnóstico de tecnologia** — leia o contexto, adapte o nível de intervenção à maturidade atual do projeto (`1/5` a `5/5`).

---

## FASE 1 — Análise do Projeto

Objetivo: mapear completamente o projeto antes de qualquer julgamento. Siga [project-analysis.md](references/project-analysis.md).

1. Liste os arquivos-fonte recursivamente (ignore `node_modules`, `venv`, `.venv`, `__pycache__`, `.git`, `*.db`, lockfiles).
2. Detecte **linguagem**, **framework** (com versão), **dependências**, **banco de dados** (e método de acesso) e **tabelas/entidades**.
3. Identifique o **domínio** da aplicação lendo rotas, tabelas e models.
4. Mapeie a **arquitetura atual** (monolítica, God Class, parcialmente em camadas) e classifique na **Escala de Maturidade Arquitetural (1/5 a 5/5)**.
5. Conte os arquivos analisados e as linhas de código aproximadas.
6. Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão>
Framework:     <framework + versão>
Database:      <banco + método de acesso>
Dependencies:  <principais dependências>
Domain:        <descrição do domínio>
Architecture:  <arquitetura atual em 1 linha> (Maturity: <N>/5)
Source files:  <N> files analyzed (~<L> LOC)
DB tables:     <tabelas/entidades>
Entry point:   <arquivo>
================================
```

---

## FASE 2 — Auditoria de Arquitetura

Objetivo: cruzar o código com o catálogo e produzir o relatório completo. Siga [anti-patterns-catalog.md](references/anti-patterns-catalog.md) e [report-template.md](references/report-template.md).

1. Leia **todos** os arquivos-fonte por completo (com números de linha).
2. Aplique os checks do catálogo (`AP-01` a `AP-18`). Verifique obrigatoriamente **APIs deprecated (`AP-14`)** conforme linguagem, framework e ORM detectados.
3. Para cada finding, registre: severidade, ID e nome do anti-pattern, `arquivo:linha-inicial-linha-final`, descrição específica, trecho de evidência, impacto e recomendação referenciando o playbook (`PB-xx`).
4. **Ordene os findings de CRITICAL → HIGH → MEDIUM → LOW.**
5. Salve o relatório em `reports/audit-report.md` (no projeto) e/ou `reports/audit-project-N.md` (na raiz do repositório).
6. Imprima o relatório e **PAUSE OBRIGATORIAMENTE** perguntando:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Aguarde a resposta do usuário. **Não modifique nenhum arquivo de código sem confirmação afirmativa.**

---

## FASE 3 — Refatoração para MVC e Validação

Executar **somente após confirmação**. Siga [mvc-guidelines.md](references/mvc-guidelines.md) e [refactoring-playbook.md](references/refactoring-playbook.md).

1. **Baseline**: registre os endpoints originais (método, path, status code e contrato de resposta).
2. **Planeje a estrutura MVC alvo** calibrada pela maturidade detectada na Fase 1:
   - Maturidade 1/5 ou 2/5 (monolito / God Class) → crie todas as camadas (`config/`, `database/`, `models/`, `controllers/`, `routes/`, `middlewares/`, `utils/`).
   - Maturidade 2.5/5 ou 3/5 (parcialmente em camadas) → preserve o que já está adequado, extraia a camada `controllers/`, `config/` e `middlewares/`, desmembre rotas misturadas e corrija models/rotas gordas.
3. **Execute as transformações (`PB-01` a `PB-18`)**:
   - Extraia credenciais hardcoded para variáveis de ambiente (`config/settings.*`) e crie `.env.example`.
   - Substitua APIs deprecated (`Model.query.get` → `db.session.get`, `datetime.utcnow` → `datetime.now(timezone.utc)`, callbacks → `async/await`, MD5/`badCrypto` → `scrypt`/`pbkdf2`).
   - Parametrize 100% das queries SQL e elimine N+1 com `LEFT JOIN` / `joinedload` / `group_by`.
   - Garanta transações atômicas e integridade referencial em escritas/deleções.
   - Mova regras de negócio para `controllers/` e deixe `routes/` apenas com roteamento HTTP.
   - Centralize o tratamento de erros em `middlewares/error_handler.*`.
4. **Validação Obrigatória**:
   - Verifique que a aplicação inicia sem erros e sem `DeprecationWarning`.
   - Teste **todos** os endpoints originais e confirme status codes e payloads.
   - **Reproduza o `Impact` de cada finding** (não basta "o código foi alterado"): para cada finding do relatório, escreva um comando/teste que exercite exatamente o cenário descrito em `Impact` e rode-o **contra o código refatorado**. Exemplos: AP-07 → `DATABASE_URL=sqlite:////tmp/x.db python -c "import app; import seed"` e confirme que `/tmp/x.db` **não** foi criado; SQL injection → payload malicioso não altera a query; senha exposta → campo ausente na resposta; N+1 → contagem de queries por request.
   - Marque um finding como **resolvido somente se o Impact não se reproduzir mais**. Se o cenário ainda ocorrer (mesmo que parcialmente, ou em outro arquivo/script como `seed.py`), o finding é **PARTIAL/OPEN**: corrija e revalide, ou liste-o explicitamente como pendente. Proibido declarar `N/N` por inspeção visual ou por existir o refactor.
   - Verifique que restam **zero** anti-patterns `CRITICAL` ou `HIGH` — confirmado pela reprodução acima, não pela troca de nomes/estrutura.
   - No resumo final, inclua a tabela `Finding → comando de verificação → resultado (RESOLVED/PARTIAL/OPEN)`; `Findings resolved: X/N` conta apenas os RESOLVED.
5. **Imprima o resumo final** (`PHASE 3: REFACTORING COMPLETE`) e atualize o relatório com a seção pós-refatoração.
