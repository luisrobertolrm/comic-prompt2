# GEMINI.md

This file provides guidance to Gemini / Antigravity when working with code in this repository.

## Project Status

Stack definido: Python (FastAPI + SQLAlchemy + Alembic) em `sumi-api/` e Angular em `sumi-web/`. Referência visual em `comic-prompt/`. Ver `README.md` para arquitetura completa.

## Environment

- Platform: Windows 11 / PowerShell
- Working directory: `C:\Git\comic-prompt2`

## Princípios de implementação

- **Planejamento antes de código.** Para qualquer tarefa não trivial, proponha o plano (arquivos afetados, abordagem, decisões) e aguarde confirmação antes de implementar.
- **Caminho mais simples primeiro.** Entre duas soluções que resolvem o problema, escolha sempre a mais simples. Complexidade só se justifica quando a simples falha.
- **Sem código desnecessário.** Não adicione abstrações, helpers, classes base, interfaces ou camadas que o problema atual não exige. Três linhas parecidas não precisam virar uma função genérica.
- **Sem antecipação de requisitos futuros.** Implemente o que foi pedido. Extensibilidade e reuso só entram quando o caso de uso concreto existir.
- **Sem comentários óbvios.** Só comente o que o código não consegue expressar sozinho (invariante não evidente, workaround de bug externo, restrição oculta).

## Comandos úteis

### Backend (`sumi-api/`)
- Executar servidor de desenvolvimento: `fastapi dev` ou `uvicorn main:app --reload`
- Executar testes: `pytest`
- Linting e formatação: `ruff check` e `ruff format`
- Type checking: `pyright`
- Migrações (Alembic):
  - Criar migração: `alembic revision --autogenerate -m "descrição"`
  - Aplicar migrações: `alembic upgrade head`
  - Reverter última migração: `alembic downgrade -1`

### Frontend (`sumi-web/`)
- Iniciar servidor de desenvolvimento: `npm run start` (ou `ng serve`)
- Build do projeto: `npm run build`
- Executar testes: `npm run test` (ou `vitest`)

## Banco de Dados e MCP

- **Sempre usar o MCP para Postgres**: Ao interagir com o banco de dados PostgreSQL (consultas, inserções, inspeção de tabelas), utilize **sempre** o servidor MCP `postgres` e suas ferramentas correspondentes (`connect_db`, `query`, `execute`, etc.). Evite criar scripts Python ou executar comandos diretos no terminal para essa finalidade.

