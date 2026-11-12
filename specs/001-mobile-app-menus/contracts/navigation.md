# Contrato: navegação do app (go_router)

| Rota | Tela | Menu |
|---|---|---|
| `/login` | Login (e-mail + senha) | — |
| `/` | Início (painel: projetos + personagens recentes) | **Início** |
| `/projects` | Lista completa de HQs (grade/lista, filtro) | **Projetos** |
| `/library` | Biblioteca de personagens | **Biblioteca** |
| `/library/new` · `/library/:id` | Criar / editar personagem | — |
| `/series` | Séries | **Séries** |
| `/voice-test` | Teste de Voz | **Teste de Voz** |
| `/production/new/idea` | Ideia (Nova HQ) | — |
| `/production/:id/characters` | Personagens (projeto já criado na Ideia) | — |
| `/production/:id/scenarios` | Cenários | — |
| `/production/:id/script` | Roteiro | — |
| `/production/:id/review` | Revisão | — |
| `/production/:id/editor` | Editor | — |
| `/production/:id/finalize` | Finalizar | — |
| `/production/:id/video` | Vídeo | — |

## Regras

- Sem token válido → redirect para `/login`; com token, `/login` → `/`.
- Menu principal: `NavigationDrawer` com os 5 itens + "Sair", destacando o item atual (FR-002).
  Alcance de qualquer menu: abrir o drawer (1 toque) + item (1 toque) — SC-004.
- Rotas `/production/*` mostram uma barra de etapas (atual e concluídas tocáveis; futuras não) e a ação
  "Excluir projeto" (com código de confirmação) quando o projeto já existe.
- Abrir projeto em Início/Projetos → `/production/:id/<etapa derivada>` (data-model, ProductionStep).
- Botão voltar do Android dentro da produção volta à etapa anterior; na primeira etapa, volta à
  tela de origem.
