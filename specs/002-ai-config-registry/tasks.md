# Tasks: Cadastro de configurações de IA por tipo

**Input**: Design documents from `specs/002-ai-config-registry/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, contracts/ui.md,
quickstart.md

**Tests**: só os testes de serviço previstos no plan/quickstart (`tests/test_ai_config.py`). Não
há testes de contrato nem de integração (a spec não pede).

**Organization**:
- A Fase 2 é grande de propósito. A migração remove `app_settings`, e o código atual de IA
  (`current_config`, `minimax_config`, `app_settings_service`) para de funcionar no mesmo
  instante. Por isso a troca da fonte de configuração em todo o backend tem de entrar junta.
- As fases de história entregam a tela e o **Testar** de cada tipo.

Caminhos relativos à raiz do repositório (`C:\Git\comic-prompt`). `API` = `sumi-api/`,
`PC` = `sumi-api/src/prompt_clinica/`, `WEB` = `sumi-web/src/app/`.

## Phase 1: Setup

- [ ] T001 Fazer backup do banco local antes da migração
  (`pg_dump` do banco de `DATABASE_URL` para um arquivo fora do repo) e conferir que o head do
  Alembic é `e2f3a4b5c6d7` (`uv run alembic heads` em `sumi-api/`).

---

## Phase 2: Foundational (bloqueia todas as histórias)

**Purpose**: tabelas, conversão de dados, leitura da config ativa, adaptadores, CRUD da API e
consumidores trocados para a nova fonte. Ao fim, o sistema funciona com o que a migração
converteu, ainda sem tela nova.

### Modelos e migração

- [X] T002 [P] Criar `sumi-api/models/ai_text_config.py`: classe `AITextConfig`, tabela
  `ai_text_config`, no padrão de `models/app_settings.py`. Colunas:
  - `id` `integer` PK autoincremento;
  - `name` `String(80)` obrigatório;
  - `kind` `String(20)` obrigatório;
  - `base_url` `String(300)` obrigatório;
  - `api_key` `Text` `server_default=""` ("cifrada (`utils/crypto.encrypt`); pode ser vazia");
  - `model` `String(120)` obrigatório;
  - `active` `Boolean` `server_default=false`;
  - `updated_at` `DateTime(timezone=True)` `server_default=now()` e `onupdate`.

  Índice `Index("uq_ai_text_config_active", "active", unique=True,
  postgresql_where=text("active"), sqlite_where=text("active"))`, para "no máximo uma ativa".
- [X] T003 [P] Criar `sumi-api/models/ai_image_config.py` (`AIImageConfig`, tabela
  `ai_image_config`): mesmas colunas e índice do T002, com nome `uq_ai_image_config_active`.
- [X] T004 [P] Criar `sumi-api/models/ai_transcription_config.py` (`AITranscriptionConfig`,
  tabela `ai_transcription_config`): mesmas colunas e índice do T002, mais `language`
  `String(10)` `server_default=""` ("vazio = detecção automática").
- [X] T005 [P] Criar `sumi-api/models/ai_voice_config.py` (`AIVoiceConfig`, tabela
  `ai_voice_config`): mesmas colunas e índice do T002.
- [X] T006 [P] Criar `sumi-api/models/ai_video_config.py` (`AIVideoConfig`, tabela
  `ai_video_config`): mesmas colunas e índice do T002.
- [X] T007 Atualizar `sumi-api/models/all_models.py`: importar e exportar os cinco modelos novos
  e remover `AppSettings`. Apagar `sumi-api/models/app_settings.py`.
- [X] T008 Criar a migração `sumi-api/alembic/versions/g1h2i3j4k5l6_ai_config_tables.py`
  (`down_revision = "e2f3a4b5c6d7"`).
  - `upgrade`:
    1. criar as cinco tabelas e os índices parciais `UNIQUE (active) WHERE active`;
    2. ler a linha `id=1` de `app_settings`, se existir;
    3. calcular o valor efetivo de cada campo: coluna preenchida, senão variável do `.env` via
       `os.getenv` (o `env.py` já chama `load_dotenv`);
    4. inserir as linhas de research.md R7 (uma por fornecedor **com chave**; ativa = provider
       em uso, com `AI_TEXT_PROVIDER`/`AI_IMAGE_PROVIDER`, senão `AI_PROVIDER`). As chaves do
       `app_settings` são copiadas cifradas como estão; as do `.env` são cifradas com
       `prompt_clinica.utils.crypto.encrypt`. Com provider `comfyui` em uso, nenhuma imagem
       fica ativa;
    5. `drop_table("app_settings")`.
  - `downgrade`: recriar `app_settings` com as colunas das migrações `d1e2f3a4b5c6` +
    `e2f3a4b5c6d7` (vazia) e remover as cinco tabelas.

  URLs fixas da conversão:
  - OpenAI: `https://api.openai.com/v1`;
  - MiniMax texto: `https://api.minimax.io/v1`;
  - MiniMax imagem, voz e vídeo: `MINIMAX_BASE_URL` ou `https://api.minimax.io`;
  - Seedream: `BYTEPLUS_BASE_URL` ou `https://ark.ap-southeast.bytepluses.com/api/v3`.

### Leitura da config ativa e abstrações

- [X] T009 Criar `PC/ai/registry.py`:
  - `@dataclass(frozen=True) AIConfig(kind, base_url, api_key, model, language="")`;
  - `AI_TYPES: dict[str, type]` com `"text"→AITextConfig, "image"→AIImageConfig,
    "transcription"→AITranscriptionConfig, "voice"→AIVoiceConfig, "video"→AIVideoConfig`;
  - `KINDS: dict[str, tuple[str, ...]]` com `text=("openai","anthropic")`,
    `image=("openai","seedream","minimax")`, `transcription=("openai",)`, `voice=("minimax",)`,
    `video=("minimax",)`;
  - `LABELS` (`"texto"`, `"imagem"`, `"transcrição"`, `"voz"`, `"vídeo"`);
  - `class NoActiveConfig(Exception)` com a mensagem "Nenhuma IA de {label} ativa. Configure em
    Configurações do sistema.";
  - `to_ai_config(row) -> AIConfig`, que decifra com `utils/crypto.decrypt`;
  - `get_active(ai_type) -> AIConfig`, que abre `SessionLocal`, busca `active` e lança
    `NoActiveConfig` se não achar.
- [X] T010 Em `PC/ai/base.py`, adicionar `Protocol`s ao lado de `AIProvider`:
  - `SpeechToText.transcribe(self, audio: bytes, filename: str) -> str`;
  - `TextToSpeech.synthesize(self, text: str, voice_id: str) -> bytes`.

### Adaptadores

- [X] T011 Ajustar `PC/ai/providers/openai_provider.py`:
  - construtor `OpenAIProvider(api_key, base_url, text_model="", image_model="")`, com
    `base_url` sempre passado ao SDK e `api_key or "none"`, porque o SDK exige um valor;
  - `max_completion_tokens` só se `"api.openai.com"` estiver no `base_url`, senão `max_tokens`;
  - `temperature` omitida só para os modelos de `_fixed_temperature`;
  - remover blocos `<think>…</think>` e `<think>` sem fechamento do conteúdo, movendo as regex
    de `PC/ai/minimax/text.py`;
  - `name` = host do `base_url` (ex.: `api.openai.com`).

  Atualizar `build_local_text_provider` em `PC/ai/__init__.py` para a nova assinatura.
- [X] T012 [P] Criar `PC/ai/providers/anthropic_provider.py`: `AnthropicProvider(api_key,
  base_url, model)` com `text()` via `httpx.post(f"{base_url}/v1/messages")` e:
  - headers `x-api-key` e `anthropic-version: 2023-06-01`;
  - mensagens `system` concatenadas no campo `system`;
  - `max_tokens = req.max_tokens or 4096`;
  - `json_mode` acrescenta ao system "Responda somente com JSON válido.";
  - `timeout=180`;
  - erro HTTP ≥ 400 → `RuntimeError(f"Anthropic HTTP {status}: {body}")`.

  `image()` lança `NotImplementedError`.
- [X] T013 [P] Ajustar `PC/ai/providers/seedream_provider.py`: construtor `SeedreamProvider(api_key,
  base_url, model)`, sem ler `settings`. O `text()` continua lançando erro.
- [X] T014 Ajustar o MiniMax:
  - `PC/ai/minimax/config.py`:
    - remover `_env` e os `default_factory` de `api_key`, `base_url`, `group_id` e `model`;
    - `MinimaxConfig(api_key, base_url, model)` com sub-configs de parâmetros técnicos fixos
      (sample_rate, bitrate, audio_format, voice_id padrão `English_Graceful_Lady`, duration,
      resolution, aspect_ratio, response_format, prompt_optimizer);
    - manter `payload_log` lendo `MINIMAX_PAYLOAD_LOG`.
  - `PC/ai/minimax/client.py`: remover o envio de `GroupId`.
  - Apagar `PC/ai/minimax/text.py` e tirá-lo de `PC/ai/minimax/__init__.py`.
  - `PC/ai/minimax/image.py`, `voice.py` e `video.py`: usar `config.model`.
  - `PC/ai/providers/minimax_provider.py`: só `image()`; o `text()` lança `NotImplementedError`.
- [X] T015 Fazer `MinimaxVoiceClient` em `PC/ai/minimax/voice.py` satisfazer `TextToSpeech`:
  `synthesize(text, voice_id) -> bytes`, com o `voice_id` vazio caindo no padrão. Ajustar quem lê
  o resultado antigo.
- [X] T016 Reescrever `PC/ai/speech.py` como `class OpenAISpeechToText` (implementa
  `SpeechToText`), recebendo `AIConfig` e usando `OpenAI(api_key, base_url).audio.transcriptions`
  com `model` e `language or None`.
- [X] T017 Em `PC/ai/registry.py`, adicionar as fábricas:
  - `build_text_provider(cfg)`: `openai`→`OpenAIProvider`, `anthropic`→`AnthropicProvider`;
  - `build_image_provider(cfg)`: `openai`→`OpenAIProvider`, `seedream`→`SeedreamProvider`,
    `minimax`→`MinimaxProvider`;
  - `build_speech_to_text() -> SpeechToText`, a partir de `get_active("transcription")`;
  - `build_text_to_speech() -> TextToSpeech`, a partir de `get_active("voice")`.

  `kind` desconhecido → `ValueError`.
- [X] T018 Refatorar `PC/ai/__init__.py`:
  - remover `env_ai_config`, `_overrides`, `current_config`, `minimax_config`, `configure`,
    `_build_provider` e `build_default`;
  - `_ReloadableProvider` passa a montar `_CompositeProvider(build_text_provider(get_active("text")),
    build_image_provider(get_active("image")))` de forma preguiçosa e **separada por modalidade**
    (falta de imagem ativa não impede o texto);
  - `invalidate()` zera o cache;
  - atualizar a docstring do módulo e o `__all__`.
- [X] T019 Apagar `PC/ai/providers/comfyui_provider.py` e, em `PC/services/character_service.py`,
  remover o ramo `if ai.name != "comfyui"` e o prompt SD associado (`_SD_*`), mantendo só
  `build_portrait_prompt`.

### API do cadastro

- [X] T020 [P] Criar `PC/schemas/ai_config.py` conforme contracts/api.md:
  - `AIConfigIn`: `name` `max_length=80` com strip e não vazio; `kind` `max_length=20`; `base_url`
    `max_length=300`, que deve começar com `http://` ou `https://` (barra final removida);
    `api_key` `max_length=500`; `model` `max_length=120`, não vazio; `language` `max_length=10`;
    `active: bool = False`;
  - `AIConfigUpdate`: igual, com `api_key: str | None = None` ("`null` mantém a atual, `""`
    apaga, texto substitui");
  - `AIConfigOut`, com `key_hint` `…xxxx` e `updated_at`;
  - `ActiveIn(active: bool)`;
  - `TextTestOut`, `ImageTestOut`, `TranscriptionTestOut`, `VoiceTestOut`, `VideoTestOut`;
  - mover `TranscriptionOut` (usado por `routers/speech.py`) para cá.
- [X] T021 Criar `PC/services/ai_config_service.py`:
  - `list_configs(ai_type, db)`: ativa primeiro, depois por nome;
  - `create_config`, `update_config` (chave `None` mantém) e `set_active(ai_type, id, active,
    db)`. Com `active=True`, `UPDATE … SET active=false WHERE active` e ativa o `id` na mesma
    transação;
  - `delete_config`: `HTTPException(409, "Desative a configuração antes de excluir.")` se
    ativa;
  - validar `kind in KINDS[ai_type]`, senão 422;
  - toda escrita chama `ai.invalidate()`.
- [X] T022 Criar `PC/routers/ai_configs.py` (`prefix="/admin/ai-configs"`,
  `Depends(get_current_admin)`) com GET, POST (201), PUT, `PATCH /{id}/active` (retorna a lista
  inteira) e DELETE (204) de contracts/api.md. `ai_type` fora de `AI_TYPES` → 404. Registrar em
  `PC/main.py`.
- [X] T023 Em `PC/main.py`, tratar `NoActiveConfig` globalmente: `exception_handler` → `400
  {"detail": str(exc)}` (FR-011).

### Consumidores trocados para a config ativa

- [X] T024 [P] `PC/routers/health.py`: `/health/ai` usa `get_active("text")` para provider e modelo.
  Remover `_text_model`. Sem ativa → `{"status": "error", "detail": "Nenhuma IA de texto ativa."}`.
- [X] T025 [P] `PC/routers/speech.py`: injetar `stt: SpeechToText = Depends(build_speech_to_text)`
  e chamar `stt.transcribe`. Importar `TranscriptionOut` de `schemas/ai_config.py`.
- [X] T026 [P] `PC/routers/voice.py`: injetar `tts: TextToSpeech = Depends(build_text_to_speech)`
  no lugar de `MinimaxVoiceClient(minimax_config())`.
- [X] T027 [P] `PC/services/video_service.py`: receber `TextToSpeech` (montado por
  `build_text_to_speech()` no ponto de entrada do job) no lugar de `minimax_config()` e
  `MinimaxVoiceClient`. Ajustar `_synthesize` e o `voice_id` padrão.
- [X] T028 [P] `PC/routers/image_test.py`: usar `get_active("image")`. Se `kind != "minimax"` →
  400 "A IA de imagem ativa não é MiniMax." Montar `MinimaxHTTPBase` com `MinimaxConfig` a
  partir da `AIConfig`.
- [X] T029 Remover a configuração antiga:
  - apagar `PC/services/app_settings_service.py` e `PC/schemas/app_settings.py`;
  - remover as rotas `/admin/app-settings*` de `PC/routers/admin.py`;
  - remover `app_settings_service.apply_from_db()` e o import em `PC/main.py`;
  - remover de `PC/config.py` `openai_api_key`, `ai_provider`, `ai_text_provider`,
    `ai_image_provider`, `ai_text_model`, `ai_image_model`, `stt_model`, `stt_language`,
    `byteplus_api_key`, `byteplus_base_url` e `seedream_model`.

### Testes do serviço

- [X] T030 Criar `sumi-api/tests/test_ai_config.py` (usa a fixture SQLite de
  `tests/conftest.py`; admin via override de `get_current_admin`):
  - criar duas configs de texto, ativar a 2ª via `PATCH` → a 1ª fica `active=false`;
  - `POST` com `active=true` desativa a anterior;
  - `DELETE` da ativa → 409;
  - `PUT` com `api_key: null` mantém o `key_hint`;
  - `kind="minimax"` em `text` → 422;
  - `ai_type="foo"` → 404;
  - a resposta nunca contém o campo `api_key`.
- [ ] T031 Rodar `uv run alembic upgrade head`, `uv run pytest -q` e subir a API. Conferir o
  SQL da quickstart §1 e gerar uma sinopse com a config convertida (SC-003).

**Checkpoint**: backend inteiro na nova fonte; tela antiga quebrada (esperado até a Fase 3).

---

## Phase 3: User Story 1 - Cadastrar e ativar uma IA de texto (P1) 🎯 MVP

**Goal**: grid com abas e popup funcionando; Texto com Testar; ByteDance e Anthropic
utilizáveis.

**Independent Test**: quickstart §3, cenários 1–4 e 8.

- [X] T032 [P] [US1] Criar `WEB/core/services/ai-config.api.ts`:
  - `export type AiType = 'text'|'image'|'transcription'|'voice'|'video'`;
  - interfaces `AiConfig`, `AiConfigIn`, `AiConfigUpdate` e os `*TestOut` de contracts/api.md;
  - `export abstract class AiConfigApi` com `list`, `create`, `update`, `setActive`, `remove`,
    `testText`, `testImage`, `testTranscription(id, blob)`, `testVoice` e `testVideo`;
  - `@Injectable() export class HttpAiConfigApi extends AiConfigApi` usando
    `${environment.apiUrl}/admin/ai-configs`.
- [X] T033 [P] [US1] Criar `WEB/features/app-settings/ai-kinds.ts` com as abas (`AiType` + rótulo)
  e, por aba, a lista `{kind, label, defaultUrl}` da tabela "URLs padrão" de contracts/ui.md, mais
  a dica de exemplos de URL da aba Texto.
- [X] T034 [US1] Criar `WEB/features/app-settings/ai-config-dialog.component.ts` e `.html`
  (standalone), com o `<dialog>` nativo aberto por `showModal()`:
  - inputs `aiType` e `config?`; output `saved`;
  - campos Nome, Tipo (só os kinds da aba), URL base, Chave (`type="password"`; na edição, dica
    "Atual …xxxx. Deixe em branco para manter.", enviando `null` se vazia), Modelo, Idioma (só
    transcrição) e checkbox **Ativa** com o aviso "(desativa a atual: <nome>)";
  - trocar o Tipo preenche a URL só se ela estiver vazia ou ainda for a padrão do Tipo anterior;
  - erros 422/400 aparecem dentro do popup, que não fecha;
  - Esc ou Cancelar fecham sem salvar.

  Estilo com as classes atuais (`input`, `btn-primary`, `btn-ghost`, `muted-sm`).
- [X] T035 [US1] Reescrever `WEB/features/app-settings/app-settings.component.ts` e `.html`:
  - `providers: [{ provide: AiConfigApi, useClass: HttpAiConfigApi }]`;
  - abas Texto | Imagem | Transcrição | Voz | Vídeo;
  - por aba, um grid `<table>` com Ativa (interruptor), Nome, Tipo · Modelo, Chave (`key_hint`),
    URL (host) e ações Testar · Editar · Excluir, além do botão "+ Nova configuração", que abre o
    popup;
  - o interruptor chama `setActive` e substitui a lista pela resposta (FR-019/020);
  - estado vazio "Nenhuma configuração de <tipo>. Clique em Nova configuração.";
  - remover todo o código antigo (seções, `apiKeys`, `EMPTY`, `defaults`).
- [X] T036 [US1] Em `PC/services/ai_config_service.py` e `PC/routers/ai_configs.py`, implementar
  `POST /admin/ai-configs/text/{id}/test`:
  - monta `build_text_provider(to_ai_config(row))` da linha **salva** (não só a ativa);
  - envia "Responda apenas: ok" com `max_tokens=200`;
  - retorna `TextTestOut(response, model, elapsed_ms)`;
  - exceção do fornecedor → 502 com a mensagem dele.
- [X] T037 [US1] No grid (`app-settings.component`), o Testar da aba Texto chama `testText` e
  mostra, abaixo da linha, "✓ <model> · <ms> ms — <response>" ou "⚠ <erro>".
- [X] T038 [US1] Remover de `WEB/core/services/admin.service.ts` `getAppSettings`,
  `updateAppSettings`, `testText`, `testImage` e os tipos `AppSettings*`, `ApiKey*`,
  `ImageTestOut` e `TextTestOut`. Ajustar os imports que quebrarem.

**Checkpoint**: MVP. O texto é configurável e trocável pela tela.

---

## Phase 4: User Story 2 - Cadastrar e ativar uma IA de imagem (P2)

**Goal**: aba Imagem com Testar; Seedream, OpenAI e MiniMax configuráveis.

**Independent Test**: quickstart §3, cenários 9–10.

- [X] T039 [US2] Implementar `POST /admin/ai-configs/image/{id}/test` em
  `PC/services/ai_config_service.py` e `PC/routers/ai_configs.py`:
  - `build_image_provider(to_ai_config(row))`;
  - prompt "Simple manga-style ink drawing of a cat sitting on a windowsill", `aspect_ratio="1:1"`,
    `quality="low"` se `kind=="openai"`, senão `"standard"`;
  - retorna `ImageTestOut(image=url or data-URI, model, elapsed_ms)`; erro → 502.
- [X] T040 [US2] No grid, o Testar da aba Imagem mostra a imagem (`max-width:256px`) com modelo e
  ms, ou o erro, em `WEB/features/app-settings/app-settings.component.html`.

**Checkpoint**: Texto e Imagem funcionando de forma independente.

---

## Phase 5: User Story 4 - Gerenciar configurações cadastradas (P2)

**Goal**: editar, desativar e excluir com as regras da spec.

**Independent Test**: quickstart §3, cenários 5–7.

- [X] T041 [US4] Em `WEB/features/app-settings/app-settings.component.*`:
  - Editar abre o popup com a linha;
  - Excluir fica desabilitado na linha ativa, com `title="Desative antes de excluir"`;
  - nas demais, Excluir abre um `<dialog>` de confirmação (sem `confirm()`) e chama `remove`;
  - um erro 409 aparece como aviso.
- [X] T042 [US4] Em `WEB/features/app-settings/app-settings.component.html`, mostrar acima do grid,
  quando nenhuma linha estiver ativa: "Nenhuma IA de <tipo> ativa. As funções de <tipo> ficam
  indisponíveis."
- [X] T043 [US4] Conferir que o interceptor ou os toasts atuais do web mostram o `detail` do 400
  `NoActiveConfig` nas telas de geração (sinopse, retrato, ditado). Ajustar só se uma delas engolir
  a mensagem (FR-011).

---

## Phase 6: User Story 3 - Cadastrar e ativar uma IA de transcrição (P3)

**Goal**: aba Transcrição com idioma e Testar por microfone.

**Independent Test**: quickstart §3, cenário 11.

- [X] T044 [US3] Implementar `POST /admin/ai-configs/transcription/{id}/test`
  (`multipart/form-data`, campo `file`) em `PC/services/ai_config_service.py` e
  `PC/routers/ai_configs.py`: `OpenAISpeechToText(to_ai_config(row)).transcribe(...)` →
  `TranscriptionTestOut(text, model, elapsed_ms)`; erro → 502.
- [X] T045 [US3] Em `WEB/core/services/dictation.service.ts`, expor a gravação crua (ex.:
  `recordBlob(): Promise<Blob>` com start/stop), sem mudar o ditado atual. No grid da aba
  Transcrição, Testar grava, para, chama `testTranscription(id, blob)` e mostra o texto.

---

## Phase 7: Voz e Vídeo (FR-016)

**Purpose**: abas Voz e Vídeo com Testar. A spec não tem história própria; o requisito é o
FR-016.

- [X] T046 Implementar `POST /admin/ai-configs/voice/{id}/test` em
  `PC/services/ai_config_service.py` e `PC/routers/ai_configs.py`: sintetiza "Olá, este é um teste
  de voz." com `MinimaxVoiceClient` da linha → `VoiceTestOut(audio="data:audio/mpeg;base64,...",
  model, elapsed_ms)`.
- [X] T047 Implementar `POST /admin/ai-configs/video/{id}/test` no mesmo serviço e router:
  - `GET {base_url}/v1/query/video_generation?task_id=0` com a chave da linha;
  - HTTP 401 ou `base_resp.status_code == 1004` → 502 "Chave inválida";
  - qualquer outra resposta → `VideoTestOut(status="ok", model, elapsed_ms)` (research R6).
- [X] T048 No grid, o Testar de Voz toca o áudio num `<audio controls>` e o de Vídeo mostra
  "✓ Conexão OK" ou o erro, em `WEB/features/app-settings/app-settings.component.html`.

---

## Phase 8: Polish & Cross-Cutting

- [X] T049 [P] Atualizar `sumi-api/.env.example`:
  - remover `OPENAI_API_KEY`, `AI_PROVIDER`, `AI_TEXT_*`, `AI_IMAGE_*`, `STT_*`, `BYTEPLUS_*`,
    `SEEDREAM_MODEL`, `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`, `MINIMAX_BASE_URL`,
    `MINIMAX_*_MODEL` e o bloco ComfyUI;
  - manter `*_PAYLOAD_LOG`;
  - comentar que as IAs são cadastradas em Configurações do sistema e que o `.env` só é lido uma
    vez, pela migração.
- [X] T050 [P] Atualizar `README.md` e `sumi-api/ARCHITECTURE.md`: seção de IA com os cinco
  cadastros, tipos, `registry.py`, adaptadores e a remoção do ComfyUI e do `app_settings`.
- [X] T051 Rodar a varredura SC-006 (quickstart §4) em `sumi-api/src`. Ela deve voltar vazia;
  corrigir o que aparecer.
- [X] T052 Rodar `uv run ruff check .` e `uv run mypy src` em `sumi-api/` e `npx ng build` em
  `sumi-web/`, e corrigir os erros.
- [ ] T053 Executar a quickstart §3 inteira (cenários 1–13) e registrar os resultados.

---

## Dependencies & Execution Order

- **Fase 1** → **Fase 2** (bloqueante: migração, adaptadores e consumidores entram juntos).
- **Fase 3 (US1)** depende da Fase 2. Ela cria a tela usada por todas as outras.
- **Fases 4, 5, 6 e 7** dependem da Fase 3 (tela) e são independentes entre si.
- **Fase 8** vem depois de todas.

Dentro da Fase 2:
- T002–T006 → T007 → T008;
- T009 → T010–T017 → T018;
- T018 → T019–T029;
- T020 → T021 → T022;
- T030 e T031 por último.

## Parallel Opportunities

- T002–T006 (cinco modelos, arquivos distintos).
- T012 e T013 (adaptadores novos ou independentes), depois do T009.
- T020 (schemas) em paralelo com T011–T017.
- T024–T028 (cada consumidor num arquivo), depois do T018.
- T032 e T033 (front) em paralelo com o backend da Fase 2, porque só dependem do contrato.
- Fases 4, 5, 6 e 7 em paralelo depois da Fase 3. Atenção: todas tocam
  `ai_config_service.py`, `ai_configs.py` e `app-settings.component.html`, então coordenar os
  merges.
- T049 e T050.

## Implementation Strategy

1. **MVP** = Fases 1–3: backend novo inteiro e a tela com Texto, o que resolve o caso
   ByteDance/Anthropic.
2. Depois Imagem (Fase 4) e Gerenciar (Fase 5), que são as de uso diário.
3. Transcrição, Voz e Vídeo (Fases 6–7).
4. Polish (Fase 8), com a varredura SC-006 como critério de pronto.
