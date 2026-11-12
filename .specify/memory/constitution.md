<!--
Sync Impact Report
- Version change: (template) → 1.0.0
- Modified principles: n/a (primeira ratificação; derivada de CLAUDE.md)
  - "Sem antecipação de requisitos futuros" redefinido: a regra "Extensibilidade e reuso só entram
    quando o caso de uso concreto existir" foi substituída por "Programar para abstrações"
  - "Sem código desnecessário" ajustado para não conflitar com o uso obrigatório de abstrações
- Added sections: Core Principles (I–VI), Stack e Restrições, Fluxo de Trabalho, Governance
- Removed sections: nenhuma
- Templates: não alterados (leem a constituição em tempo de execução)
- Follow-up TODOs: alinhar CLAUDE.md (seção "Princípios de implementação") com os princípios III e IV
-->

# Sumi Constitution

## Core Principles

### I. Planejamento Antes de Código

Toda tarefa não trivial MUST começar com um plano (arquivos afetados, abordagem, decisões) e
MUST aguardar confirmação antes da implementação. Tarefas triviais (ajuste pontual, typo,
renomeação local) podem ser feitas diretamente.

**Racional**: evita retrabalho e decisões arquiteturais tomadas sem o dono do projeto.

### II. Caminho Mais Simples Primeiro

Entre duas soluções que resolvem o problema, MUST ser escolhida a mais simples. Complexidade
adicional só é aceita quando a solução simples comprovadamente falha, e a justificativa MUST
constar no plano.

### III. Programar para Abstrações

Dependências entre componentes (serviços, repositórios, provedores de IA, armazenamento,
integrações externas) MUST ser declaradas contra classes abstratas ou interfaces (em Python:
`abc.ABC` ou `typing.Protocol`; em Angular: classes abstratas ou `interface` com injeção via DI),
nunca diretamente contra a implementação concreta.

- A abstração MUST ser pequena e nomeada pelo que faz no domínio, não pela tecnologia.
- A implementação concreta é injetada (FastAPI `Depends`, DI do Angular), não instanciada pelo
  consumidor.
- Uma abstração com uma única implementação é permitida; hierarquias com mais de um nível de
  herança abstrata NÃO são.

**Racional**: troca de implementação (ex.: provedores de IA) e testes sem tocar nos consumidores.

### IV. Legibilidade Acima de Engenhosidade

O código MUST ser lido com facilidade por um humano. Abstrações existem para separar contrato de
implementação, não para criar camadas ou genericidade.

- NÃO adicionar helpers, classes base, generics ou metaprogramação que o problema atual não exige.
- Três linhas parecidas não precisam virar uma função genérica.
- Implementar o que foi pedido; sem funcionalidades especulativas além do contrato abstrato.
- Nomes explícitos e fluxo linear têm prioridade sobre concisão.

### V. Sem Comentários Óbvios

Comentários MUST ser usados apenas para o que o código não expressa sozinho: invariante não
evidente, workaround de bug externo ou restrição oculta. Comentários que repetem o código são
removidos em revisão.

## Stack e Restrições

- Backend: Python (FastAPI + SQLAlchemy + Alembic) em `sumi-api/`.
- Frontend: Angular em `sumi-web/`.
- Referência visual: `comic-prompt/`.
- Arquitetura detalhada: `README.md` e `sumi-api/ARCHITECTURE.md`.
- Ambiente de desenvolvimento: Windows 11 / PowerShell.
- Novas dependências de stack MUST ser justificadas no plano (Princípio I).

## Fluxo de Trabalho

- Mensagens de commit MUST ser escritas em português.
- Commits MUST NOT conter o nome ou atribuição de assistentes de IA (sem `Co-Authored-By` de IA,
  sem menções a "Claude" ou ferramentas geradoras). A autoria é sempre do desenvolvedor.
- Commits seguem o formato `tipo: descrição` (ex.: `feat:`, `fix:`, `docs:`), como no histórico.
- Commit e push só ocorrem quando solicitados explicitamente.

## Governance

Esta constituição prevalece sobre outras práticas do projeto; `CLAUDE.md` é o guia operacional
em tempo de execução e MUST permanecer consistente com ela.

- **Emendas**: propostas via `/speckit-constitution`, com Sync Impact Report, e aprovadas pelo
  dono do projeto antes do commit.
- **Versionamento**: semântico — MAJOR para remoção/redefinição incompatível de princípios, MINOR
  para princípio ou seção nova/expandida, PATCH para redação e esclarecimentos.
- **Conformidade**: todo plano (`/speckit-plan`) e revisão MUST verificar aderência aos princípios;
  desvios MUST ser justificados explicitamente no plano.

**Version**: 1.0.0 | **Ratified**: 2026-11-12 | **Last Amended**: 2026-11-12
