# Implementation Plan: Cadastro de configurações de IA por tipo

**Branch**: `main` | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-ai-config-registry/spec.md`

## Summary

A tela "Configurações do sistema" é substituída por cinco cadastros (Texto, Imagem, Transcrição,
Voz, Vídeo). Cada um tem várias configurações com os mesmos campos (nome, tipo, URL, chave,
modelo; e idioma na transcrição) e no máximo uma ativa. O grid tem um interruptor de ativação, e
a inclusão e a edição acontecem num popup.

No backend:
- cinco tabelas novas;
- uma migração que converte `app_settings` + `.env` e remove `app_settings`;
- um módulo `ai/registry.py` que entrega a config ativa a adaptadores escolhidos pelo `kind`.

Toda leitura de chave, modelo ou URL por nome de fornecedor sai do código (inventário em
[research.md](research.md) R8). O texto de ByteDance e MiniMax passa pelo adaptador
OpenAI-compatível, e a Anthropic ganha um adaptador `httpx`.

## Technical Context

- **Language/Version**: Python 3.13 (sumi-api); TypeScript / Angular 21 (sumi-web)
- **Primary Dependencies**: FastAPI, SQLAlchemy, Alembic, `openai` SDK, `httpx`, `cryptography`
  (todas já presentes). **Nenhuma dependência nova.**
- **Storage**: PostgreSQL (cinco tabelas novas, `app_settings` removida)
- **Testing**: pytest com SQLite em memória (`tests/conftest.py`). O índice parcial é declarado
  com `postgresql_where` + `sqlite_where`, para valer nos dois bancos.
- **Target Platform**: API Linux/Docker; web no navegador
- **Project Type**: web-service + SPA
- **Performance Goals**: trocar a ativa vale na próxima chamada (cache invalidado na escrita)
- **Constraints**:
  - chave nunca volta na resposta;
  - cifra com Fernet derivada do `JWT_SECRET_KEY` (a mesma de hoje).
- **Scale/Scope**: poucas dezenas de linhas por tabela; 1 tela; cerca de 25 arquivos tocados

## Constitution Check

| Princípio | Situação |
|---|---|
| I. Planejamento antes de código | ✅ Este plano aguarda confirmação |
| II. Caminho mais simples | ✅ Sem dependência nova. Anthropic com `httpx`; popup com `<dialog>` nativo; texto MiniMax/ByteDance reaproveita o adaptador OpenAI e elimina o `MinimaxTextClient` |
| III. Programar para abstrações | ✅ `AIProvider` continua. Novos `SpeechToText` e `TextToSpeech` (`Protocol`, uma implementação cada, injetados via `Depends`). No front, `AiConfigApi` abstrata com `HttpAiConfigApi` via `providers`. Vídeo sem protocolo, por não ter consumidor (R5) |
| IV. Legibilidade | ✅ Cinco modelos explícitos sem mixin. Serviço único com um `dict` `ai_type → modelo`, sem generics. Um nível de abstração |
| V. Sem comentários óbvios | ✅ Só os comentários de invariante (índice parcial, `<think>`) |
| Stack | ✅ Nada novo |
| Commits | ✅ Em português, sem atribuição de IA, só quando pedido |

**Reavaliação pós-design**: sem violações. *Complexity Tracking* vazio.

## Project Structure

### Documentation (this feature)

```text
specs/002-ai-config-registry/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── api.md
│   └── ui.md
└── tasks.md            # /speckit-tasks
```

### Source Code

```text
sumi-api/
├── models/
│   ├── ai_text_config.py            # novo
│   ├── ai_image_config.py           # novo
│   ├── ai_transcription_config.py   # novo
│   ├── ai_voice_config.py           # novo
│   ├── ai_video_config.py           # novo
│   └── app_settings.py              # removido
├── alembic/versions/
│   └── g1h2i3j4k5l6_ai_config_tables.py   # cria 5 tabelas, converte, remove app_settings
├── src/prompt_clinica/
│   ├── config.py                    # remove campos de IA por fornecedor
│   ├── main.py                      # troca apply_from_db por nada (registry lê do banco)
│   ├── ai/
│   │   ├── __init__.py              # singleton `ai` monta de registry; remove env/overrides
│   │   ├── registry.py              # novo: AIConfig, get_active(), build_*()
│   │   ├── base.py                  # + SpeechToText, TextToSpeech (Protocol)
│   │   ├── speech.py                # vira OpenAISpeechToText
│   │   ├── providers/
│   │   │   ├── openai_provider.py   # base_url sempre; strip <think>; regra max_tokens por host
│   │   │   ├── anthropic_provider.py  # novo (httpx /v1/messages)
│   │   │   ├── seedream_provider.py # recebe base_url/api_key/model no construtor
│   │   │   ├── minimax_provider.py  # só imagem; recebe AIConfig
│   │   │   └── comfyui_provider.py  # removido (R9)
│   │   └── minimax/
│   │       ├── config.py            # sem _env(); campos obrigatórios + constantes técnicas
│   │       ├── text.py              # removido (coberto pelo adaptador OpenAI)
│   │       └── voice.py             # implementa TextToSpeech
│   ├── schemas/ai_config.py         # novo (AIConfigIn/Update/Out, *TestOut)
│   ├── services/ai_config_service.py  # novo: CRUD, ativação exclusiva, testes
│   ├── routers/ai_configs.py        # novo: /admin/ai-configs/{ai_type}
│   ├── routers/admin.py             # remove rotas app-settings
│   ├── routers/health.py            # usa config de texto ativa
│   ├── routers/speech.py            # Depends(build_speech_to_text)
│   ├── routers/voice.py             # Depends(build_text_to_speech)
│   ├── routers/image_test.py        # config de imagem ativa (400 se não minimax)
│   ├── services/video_service.py    # TextToSpeech em vez de MinimaxVoiceClient direto
│   ├── services/character_service.py  # remove ramo comfyui
│   ├── services/app_settings_service.py  # removido
│   └── schemas/app_settings.py      # removido (TranscriptionOut migra p/ schemas/speech ou ai_config)
├── tests/test_ai_config.py          # novo
├── .env.example                     # remove variáveis de IA por fornecedor
└── ARCHITECTURE.md                  # atualiza seção de IA

sumi-web/src/app/
├── core/services/
│   ├── ai-config.api.ts             # novo: abstract AiConfigApi + HttpAiConfigApi
│   └── admin.service.ts             # remove métodos app-settings
└── features/app-settings/
    ├── ai-kinds.ts                  # novo: tipos, rótulos e URLs padrão por aba
    ├── app-settings.component.ts/html   # reescrito: abas + grid
    └── ai-config-dialog.component.ts/html  # novo: popup <dialog>

README.md                            # remove variáveis de IA; aponta para a tela
```

**Structure Decision**: a estrutura existente (`sumi-api` + `sumi-web`) continua. Os arquivos
novos seguem as pastas e os nomes de cada camada. O `sumi-mobile` não é afetado, porque não tem
a tela de administração.

## Ordem de implementação

1. Modelos, migração e conversão (P1, base de tudo).
2. `registry.py`, adaptadores (OpenAI genérico, Anthropic, Seedream e MiniMax recebendo
   `AIConfig`) e singleton `ai`.
3. Serviço, schemas e rotas `/admin/ai-configs`, e os testes do serviço.
4. Adaptar os consumidores: speech, voice, video_service, image_test, health, character_service.
   Remover `app_settings*`, ComfyUI e `minimax/text.py`. Limpar o `config.py`.
5. Front: `AiConfigApi`, `ai-kinds.ts`, grid com abas e popup.
6. `.env.example`, README e ARCHITECTURE.
7. Varredura do SC-006 e execução do quickstart.

## Pontos para confirmação

1. **Seedream como Tipo próprio na Imagem** (R3). O payload do Seedream (referências, tamanhos
   2K) não cabe no adaptador OpenAI. A spec FR-005 foi atualizada.
2. **Remover o ComfyUI** (R9). Se ainda for usado, entra como Tipo `comfyui` da Imagem, sem
   campos novos.
3. **Vídeo não tem consumidor hoje** (R5). O cadastro e o teste de conexão são entregues, mas
   nada do sistema gera vídeo pelo MiniMax ainda.

## Complexity Tracking

Sem violações a justificar.
