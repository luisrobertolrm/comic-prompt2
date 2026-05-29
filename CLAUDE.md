# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

Stack definido: Python (FastAPI + SQLAlchemy + Alembic) em `sumi-api/` e Angular em `sumi-web/`. Referência visual em `comic-prompt/`. Ver `README.md` para arquitetura completa.

## Environment

- Platform: Windows 11 / PowerShell
- Working directory: `C:\Git\comic-prompt`

## Princípios de implementação

- **Planejamento antes de código.** Para qualquer tarefa não trivial, proponha o plano (arquivos afetados, abordagem, decisões) e aguarde confirmação antes de implementar.
- **Caminho mais simples primeiro.** Entre duas soluções que resolvem o problema, escolha sempre a mais simples. Complexidade só se justifica quando a simples falha.
- **Sem código desnecessário.** Não adicione abstrações, helpers, classes base, interfaces ou camadas que o problema atual não exige. Três linhas parecidas não precisam virar uma função genérica.
- **Sem antecipação de requisitos futuros.** Implemente o que foi pedido. Extensibilidade e reuso só entram quando o caso de uso concreto existir.
- **Sem comentários óbvios.** Só comente o que o código não consegue expressar sozinho (invariante não evidente, workaround de bug externo, restrição oculta).
