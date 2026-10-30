---
name: refactor-arch
description: Analisa uma codebase backend (qualquer linguagem/framework), audita anti-patterns e code smells por severidade com arquivo e linha exatos, gera relatório e, após confirmação do usuário, refatora o projeto para o padrão MVC validando que a aplicação continua funcionando. Use quando o usuário pedir "/refactor-arch", auditoria de arquitetura, refatoração para MVC ou limpeza de código legado.
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

Você é um arquiteto de software sênior. Execute **3 fases sequenciais** no diretório do projeto atual.
Esta skill é **agnóstica de tecnologia**: o conhecimento específico vive nos arquivos de referência.
Nunca assuma a stack — detecte-a na Fase 1.

## Arquivos de referência (leia sob demanda)

| Fase | Arquivo | Conteúdo |
|---|---|---|
| 1 | [project-analysis.md](references/project-analysis.md) | Heurísticas de detecção de linguagem, framework, banco, domínio e arquitetura |
| 2 | [anti-patterns-catalog.md](references/anti-patterns-catalog.md) | Catálogo de anti-patterns, sinais de detecção, severidade e APIs deprecated |
| 2 | [report-template.md](references/report-template.md) | Formato obrigatório do relatório de auditoria |
| 3 | [mvc-guidelines.md](references/mvc-guidelines.md) | Regras do MVC alvo (Models, Views/Routes, Controllers, config, middlewares) |
| 3 | [refactoring-playbook.md](references/refactoring-playbook.md) | Transformações concretas antes/depois para cada anti-pattern |

## Regras gerais

- **Nunca modifique arquivos antes da confirmação do usuário ao final da Fase 2.** Fases 1 e 2 são somente leitura
  (a única escrita permitida antes da confirmação é salvar o relatório em `reports/`, se o usuário pedir).
- Cite sempre `arquivo:linha` reais (leia o arquivo e confira os números de linha; nunca estime).
- Preserve o **contrato HTTP** (rotas, métodos, formato de payload e status codes). Corrigir um bug de segurança
  que exija mudança de contrato (ex.: parar de devolver senha) deve ser registrado no resumo final.
- Respeite o idioma de domínio já presente no código (ex.: nomes em português).
- Não instale dependências desnecessárias; prefira a biblioteca padrão da linguagem.

---

## FASE 1 — Análise do Projeto

Objetivo: entender o projeto antes de julgá-lo. Siga [project-analysis.md](references/project-analysis.md).

1. Liste os arquivos-fonte (ignore `node_modules`, `venv`, `__pycache__`, `.git`, `*.db`, lockfiles).
2. Detecte **linguagem**, **framework** (com versão), **dependências**, **banco de dados** e **tabelas/entidades**.
3. Descreva o **domínio** da aplicação (o que o sistema faz) lendo rotas e models.
4. Mapeie a **arquitetura atual** (monolítica, parcialmente em camadas, etc.) e o entry point.
5. Conte os arquivos analisados e as linhas de código aproximadas.
6. Imprima exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <principais dependências>
Domain:        <descrição do domínio>
Architecture:  <arquitetura atual em 1 linha>
Source files:  <N> files analyzed (~<L> LOC)
DB tables:     <tabelas/entidades>
Entry point:   <arquivo>
================================
```

---

## FASE 2 — Auditoria de Arquitetura

Objetivo: cruzar o código com o catálogo e produzir o relatório. Siga
[anti-patterns-catalog.md](references/anti-patterns-catalog.md) e [report-template.md](references/report-template.md).

1. Leia **todos** os arquivos-fonte por completo (com números de linha).
2. Para cada anti-pattern do catálogo, procure os **sinais de detecção**. Inclua obrigatoriamente a
   categoria **APIs deprecated** (informe a API obsoleta e o equivalente moderno).
3. Registre cada ocorrência com: severidade, nome, `arquivo:linha-inicial-linha-final`, descrição,
   impacto e recomendação. Agrupe ocorrências repetidas do mesmo anti-pattern em um único finding
   listando os locais.
4. **Ordene de CRITICAL → HIGH → MEDIUM → LOW.**
5. Imprima o relatório no formato do template, com o total de findings.
6. Se o usuário pediu para salvar, grave o relatório em `reports/audit-project-N.md` na raiz do repositório.
7. **PAUSE** e pergunte, usando exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Aguarde a resposta. **Não altere nenhum arquivo** se a resposta não for afirmativa. Encerre a execução em caso de "n".

---

## FASE 3 — Refatoração para MVC

Executar **somente após confirmação**. Siga [mvc-guidelines.md](references/mvc-guidelines.md) e
[refactoring-playbook.md](references/refactoring-playbook.md).

1. **Baseline**: antes de mexer, suba a aplicação e registre a resposta de cada endpoint (status + corpo)
   para comparar depois. Anote o comando de boot.
2. **Planeje a estrutura alvo** adaptada à stack e ao nível de organização atual:
   - Projeto monolítico → crie todas as camadas.
   - Projeto parcialmente organizado → mantenha o que já é adequado, extraia o que falta
     (ex.: camada `controllers/`, `config/`, error handler) e corrija rotas gordas.
3. **Aplique as transformações** do playbook na ordem: config/segredos → models (queries parametrizadas,
   sem N+1) → controllers (regra de negócio) → views/routes (só roteamento) → middleware de erro →
   entry point (composition root). Corrija também as APIs deprecated.
4. Remova código morto e imports não usados gerados pela migração; apague os arquivos antigos substituídos.
5. **Validação obrigatória**:
   1. Boot da aplicação sem erros (`python app.py` / `npm start` / equivalente).
   2. Chame **todos** os endpoints originais (com `curl` ou script) e compare com o baseline: mesmos
      status codes e formato. Divergências permitidas somente por correção de segurança (documente-as).
   3. Procure novamente os anti-patterns do catálogo no código novo (grep dos sinais de detecção);
      nenhum CRITICAL/HIGH pode restar.
   4. Se algo falhar, corrija e repita a validação até passar.
6. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Changes Applied
<lista de transformações aplicadas, por finding>

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly (<N>/<N>)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining
================================
```

