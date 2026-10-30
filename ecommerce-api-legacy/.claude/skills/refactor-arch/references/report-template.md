# Template do Relatório de Auditoria (Fase 2)

Gere o relatório **exatamente** neste formato. Findings em ordem **CRITICAL → HIGH → MEDIUM → LOW**.
Cada finding deve ter arquivo e intervalo de linhas reais (`arquivo:inicio-fim` ou `arquivo:linha`).
Quando o mesmo anti-pattern ocorre em vários lugares, liste todos em `File:` separados por vírgula.

````markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-da-pasta>
Stack:   <Linguagem> + <Framework>
Files:   <N> analyzed | ~<LOC> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern> (<AP-ID>)
File: <arquivo>:<linhas>[, <arquivo>:<linhas>]
Description: <o que foi encontrado, de forma concreta, citando o código>
Impact: <consequência técnica/negócio>
Recommendation: <correção, referenciando o padrão do playbook (PB-xx)>

### [HIGH] ...
...

### [MEDIUM] ...
...

### [LOW] ...
...

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
````

## Regras de preenchimento

1. `Summary` deve bater exatamente com a contagem de findings por severidade.
2. Mínimo de 5 findings, com pelo menos 1 CRITICAL ou HIGH (se o projeto realmente tiver menos, explique).
3. Inclua um finding **APIs Deprecated (AP-14)** quando houver ocorrência; caso contrário escreva
   `Deprecated APIs: none detected` abaixo do `Total`.
4. `Description` cita nomes reais (funções, variáveis, valores) — nunca texto genérico.
5. `Recommendation` diz **o que fazer** e em qual camada MVC o código deve parar.
6. O relatório termina sempre com a pergunta de confirmação; a skill **para** até receber a resposta.
7. Ao salvar em `reports/audit-project-N.md`, salve o relatório completo (sem a linha de confirmação é aceitável,
   mas mantenha a estrutura).

