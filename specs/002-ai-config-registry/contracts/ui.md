# Contrato da tela: Configurações do sistema

Rota: `/app-settings` (a mesma de hoje, só para admin).

## Layout

```text
ADMINISTRAÇÃO
Configurações do sistema
[ Texto | Imagem | Transcrição | Voz | Vídeo ]                        [+ Nova configuração]

┌──────────┬─────────────────┬──────────────────┬───────┬─────────┬──────────────────────────┐
│ Ativa    │ Nome            │ Tipo · Modelo    │ Chave │ URL     │                          │
├──────────┼─────────────────┼──────────────────┼───────┼─────────┼──────────────────────────┤
│ (●━━)    │ BytePlus prod.  │ OpenAI · seed-…  │ …ab12 │ ark.ap… │ Testar · Editar · Excluir│
│ (━━○)    │ OpenAI          │ OpenAI · gpt-…   │ …9f3c │ api.op… │ Testar · Editar · Excluir│
└──────────┴─────────────────┴──────────────────┴───────┴─────────┴──────────────────────────┘
Resultado do teste aparece abaixo da linha testada (texto, imagem, áudio ou erro).
```

- Grid vazio: "Nenhuma configuração de <tipo>. Clique em Nova configuração."
- Sem nenhuma ativa: um aviso acima do grid, "Nenhuma IA de <tipo> ativa. As funções de <tipo>
  ficam indisponíveis."
- **Interruptor "Ativa"** na linha: chama `PATCH …/active` e redesenha o grid com a resposta
  (FR-019/020).
- **Excluir**:
  - desabilitado na linha ativa, com a dica "Desative antes de excluir";
  - nas demais, pede confirmação num `<dialog>` simples (sem `confirm()` do navegador).
- **Testar (transcrição)**: grava pelo microfone usando o `DictationService`, envia o áudio e
  mostra o texto.
- **Testar (voz)**: toca o áudio retornado num `<audio controls>`.

## Popup (`<dialog>` modal)

```text
┌ Nova configuração de Texto ──────────────────────────┐
│ Nome        [BytePlus produção                    ] │
│ Tipo        [OpenAI-compatível ▾]                   │
│ URL base    [https://api.openai.com/v1            ] │  ← preenchida ao trocar o Tipo
│ Chave       [••••••••                             ] │  ← edição: "Atual …ab12. Deixe em branco para manter."
│ Modelo      [seed-1-6-250615                      ] │
│ Idioma      [pt]                                    │  ← só na aba Transcrição
│ [x] Ativa   (desativa a atual: "OpenAI")            │
│                               [Cancelar] [Salvar]   │
└─────────────────────────────────────────────────────┘
```

- O Tipo lista só os valores da aba atual (data-model, tabela `kind`).
- Trocar o Tipo preenche a URL padrão **se** ela estiver vazia ou ainda for a padrão do Tipo
  anterior. Uma URL digitada pelo usuário não é sobrescrita.
- Os erros de validação (422) aparecem no próprio popup, que não fecha.
- Esc ou Cancelar fecha sem salvar.

## URLs padrão (`ai-kinds.ts`)

| Aba | Tipo | Rótulo | URL padrão |
|---|---|---|---|
| Texto | `openai` | OpenAI-compatível | `https://api.openai.com/v1` |
| Texto | `anthropic` | Anthropic | `https://api.anthropic.com` |
| Imagem | `openai` | OpenAI | `https://api.openai.com/v1` |
| Imagem | `seedream` | Seedream (ByteDance) | `https://ark.ap-southeast.bytepluses.com/api/v3` |
| Imagem | `minimax` | MiniMax | `https://api.minimax.io` |
| Transcrição | `openai` | OpenAI-compatível | `https://api.openai.com/v1` |
| Voz | `minimax` | MiniMax | `https://api.minimax.io` |
| Vídeo | `minimax` | MiniMax | `https://api.minimax.io` |

Para usar ByteDance ou MiniMax no texto, escolha OpenAI-compatível e troque a URL. A dica
abaixo do campo mostra os exemplos `…bytepluses.com/api/v3` e `api.minimax.io/v1`.
