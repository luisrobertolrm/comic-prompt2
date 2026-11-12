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
- **Programar para abstrações.** Dependências entre componentes (serviços, repositórios, provedores de IA, armazenamento, integrações externas) são declaradas contra classes abstratas ou interfaces (Python: `abc.ABC`/`typing.Protocol`; Angular/Flutter: classe abstrata ou interface com injeção via DI/provider), nunca contra a implementação concreta. A implementação é injetada, não instanciada pelo consumidor. Abstração com uma única implementação é permitida; mais de um nível de herança abstrata não.
- **Legibilidade acima de engenhosidade.** Código que um humano lê com facilidade. Abstrações separam contrato de implementação, não criam camadas: sem helpers, classes base, generics ou metaprogramação que o problema atual não exige. Três linhas parecidas não precisam virar uma função genérica. Implemente só o que foi pedido.
- **Sem comentários óbvios.** Só comente o que o código não consegue expressar sozinho (invariante não evidente, workaround de bug externo, restrição oculta).

## Commits

- Mensagens sempre em português, no formato `tipo: descrição` (`feat:`, `fix:`, `docs:`…).
- Nunca incluir nome ou atribuição de IA (sem `Co-Authored-By` de IA, sem menção ao Claude).
- Commit e push só quando solicitados.

A fonte da verdade destes princípios é `.specify/memory/constitution.md`.
