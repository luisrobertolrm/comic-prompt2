# Data Model: Cadastro de configurações de IA por tipo

## Tabelas

As cinco tabelas têm as mesmas colunas. `ai_transcription_config` tem também `language`.

| Coluna | Tipo | Regra |
|---|---|---|
| `id` | `integer` PK | autoincremento |
| `name` | `varchar(80)` | obrigatório, sem espaços nas pontas; repetição permitida |
| `kind` | `varchar(20)` | obrigatório; valores por tabela (abaixo) |
| `base_url` | `varchar(300)` | obrigatório; deve começar com `http://` ou `https://`; barra final removida |
| `api_key` | `text` | cifrada (`utils/crypto.encrypt`); pode ser vazia (ex.: Ollama local) |
| `model` | `varchar(120)` | obrigatório |
| `language` | `varchar(10)` | **só em `ai_transcription_config`**; vazio = detecção automática |
| `active` | `boolean` | padrão `false` |
| `updated_at` | `timestamptz` | `now()` e atualizado em cada escrita |

**Índice** em cada tabela: `UNIQUE (active) WHERE active`, para no máximo uma ativa (FR-003).

### `kind` permitido por tabela

| Tabela | `kind` |
|---|---|
| `ai_text_config` | `openai`, `anthropic` |
| `ai_image_config` | `openai`, `seedream`, `minimax` |
| `ai_transcription_config` | `openai` |
| `ai_voice_config` | `minimax` |
| `ai_video_config` | `minimax` |

## Modelos SQLAlchemy (`sumi-api/models/`)

`ai_text_config.py`, `ai_image_config.py`, `ai_transcription_config.py`, `ai_voice_config.py` e
`ai_video_config.py`, um modelo explícito por arquivo, no padrão de `models/app_settings.py`.

## Objeto em memória: `AIConfig` (`ai/registry.py`)

```text
AIConfig(kind, base_url, api_key (decifrada), model, language="")
```

É o que os adaptadores recebem. A linha do banco nunca chega a eles.

## Transições de estado

```text
          criar (active=false)            ativar (grid ou popup)
 [novo] ─────────────────────▶ [inativa] ─────────────────────▶ [ativa]
                                   ▲                                │
                                   │   desativar / outra é ativada  │
                                   └────────────────────────────────┘
 excluir: só a partir de [inativa]; em [ativa] → 409
```

## Validações (serviço)

- `kind` fora da lista da tabela → 422.
- `base_url` sem esquema http(s) → 422.
- `api_key` na edição: `null` mantém a atual, `""` apaga e texto substitui (o mesmo contrato de
  hoje em `ApiKeysUpdate`).
- Excluir uma configuração ativa → 409 "Desative a configuração antes de excluir."
- Toda escrita invalida o cache do singleton `ai` (R4).

## Removido

- Tabela `app_settings` e `models/app_settings.py` (a migração R7 converte o conteúdo antes).
