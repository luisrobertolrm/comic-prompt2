# Research: Cadastro de configurações de IA por tipo

Decisões tomadas a partir da leitura do código atual (`sumi-api/src/prompt_clinica/ai/`,
`services/app_settings_service.py`, `sumi-web/.../features/app-settings/`).

## R1. Uma tabela por tipo, linhas com os mesmos campos

- **Decision**: cinco tabelas (`ai_text_config`, `ai_image_config`, `ai_transcription_config`,
  `ai_voice_config`, `ai_video_config`). Todas têm as mesmas colunas, e `ai_transcription_config`
  tem também `language`. Cada tabela tem um modelo SQLAlchemy explícito, sem mixin nem classe
  base.
- **Rationale**: é o pedido do usuário. Modelos explícitos seguem o Princípio IV (cinco classes
  curtas e repetidas são mais legíveis que uma hierarquia).
- **Alternatives considered**: tabela única com coluna `ai_type`. Seria mais simples no banco,
  mas o usuário pediu tabelas separadas, e a coluna `language` só existe na transcrição.

## R2. Garantia de "no máximo uma ativa"

- **Decision**: índice único parcial no Postgres (`CREATE UNIQUE INDEX … (active) WHERE active`)
  em cada tabela. No serviço, ativar uma configuração faz, na mesma transação,
  `UPDATE … SET active = false WHERE active` e depois ativa a escolhida.
- **Rationale**: o banco garante a regra mesmo com duas requisições simultâneas, e o serviço
  produz a troca automática (FR-003).
- **Alternatives considered**: guardar `active_id` numa tabela de roteamento. Isso exige mais uma
  tabela e um join, sem ganho.

## R3. Valores do campo Tipo (`kind`) por tipo de IA

| Tipo de IA | Valores | Adaptador |
|---|---|---|
| Texto | `openai`, `anthropic` | SDK `openai` com `base_url`; `httpx` para `POST {url}/v1/messages` |
| Imagem | `openai`, `seedream`, `minimax` | SDK `openai` `images.generate`; `SeedreamProvider`; `MinimaxImageClient` |
| Transcrição | `openai` | SDK `openai` `audio.transcriptions` com `base_url` |
| Voz | `minimax` | `MinimaxVoiceClient` |
| Vídeo | `minimax` | `MinimaxVideoClient` |

- **Decision (imagem)**: `seedream` é um valor próprio do Tipo, e a spec FR-005 foi atualizada.
  O Seedream usa a rota `/images/generations`, mas o payload é diferente do da OpenAI: tamanhos
  2K por proporção, até 10 imagens de referência no campo `image` e `watermark`. O adaptador
  OpenAI não envia referências, e retratos e painéis dependem delas. O cadastro continua com os
  mesmos campos; o Tipo só escolhe o adaptador.
- **Decision (texto MiniMax)**: o MiniMax de texto passa a ser `openai` com URL
  `https://api.minimax.io/v1`, já que o próprio `MinimaxTextClient` chama
  `/v1/chat/completions`. A remoção dos blocos `<think>…</think>` (hoje em `minimax/text.py`)
  vai para o adaptador OpenAI-compatível. Ela não faz mal a nenhum outro fornecedor e também
  serve a DeepSeek-R1 e aos modelos de raciocínio do Ollama.
- **Decision (Anthropic)**: chamada direta com `httpx` (headers `x-api-key` e
  `anthropic-version: 2023-06-01`), sem SDK novo. O projeto já usa `httpx` para MiniMax e
  Seedream (Princípio II; nenhuma dependência nova de stack). A mensagem `system` vai no campo
  `system`, como a API exige. `json_mode` vira uma instrução no system prompt, porque a API não
  tem `response_format`.
- **Decision (`max_tokens`)**: o adaptador OpenAI-compatível envia `max_completion_tokens` só
  quando o host é `api.openai.com`; para os demais (BytePlus, MiniMax, Ollama), `max_tokens`.
  Isso substitui a regra atual baseada em `openai-local`.

## R4. Onde a configuração ativa é lida em tempo de execução

- **Decision**: um módulo `ai/registry.py` com `get_active(ai_type) -> AIConfig | None`, que lê
  do banco a linha ativa (`AIConfig` é um dataclass com kind, base_url, api_key decifrada, model e
  language). O singleton `ai` continua sendo o ponto de uso de texto e imagem e passa a se montar
  a partir de `get_active("text")` e `get_active("image")`. O cache é invalidado (`ai.swap(None)`)
  a cada escrita no cadastro.
  - Transcrição, voz e vídeo leem `get_active(...)` a cada chamada. São chamadas raras, e um
    SELECT por chave primária custa pouco.
- **Rationale**: atende o FR-009 (vale na hora) com o mesmo mecanismo de recarga que já existe.
  Os consumidores (`synopsis`, `roteiro`, `panel_service`…) não mudam.
- **Alternatives considered**: ler do banco a cada `ai.text()`. Funciona, mas recria o cliente
  HTTP a cada chamada sem necessidade.

## R5. Abstrações (Princípio III)

- `AIProvider` (texto e imagem) já existe em `ai/base.py` e continua.
- Novos `Protocol`s, cada um com uma única implementação, o que a constituição permite:
  - `SpeechToText.transcribe(audio, filename) -> str`, implementado pelo adaptador OpenAI;
  - `TextToSpeech.synthesize(text, voice_id) -> bytes`, implementado pelo MiniMax.
  Os consumidores (`routers/speech.py`, `routers/voice.py`, `services/video_service.py`) recebem
  a implementação por uma fábrica `build_speech_to_text()` / `build_text_to_speech()` a partir da
  config ativa, injetada via `Depends` nos routers.
- Vídeo: o `MinimaxVideoClient` **não tem consumidor hoje** (o vídeo do projeto é montado com
  ffmpeg, usando narração e imagens). Só o teste da configuração o usa; não se cria protocolo
  para um uso que não existe (Princípio IV).

## R6. Testes por tipo

| Tipo | Teste |
|---|---|
| Texto | Envia "Responda apenas: ok" e devolve resposta, modelo e ms |
| Imagem | Gera um gato em tinta, 1:1, e devolve a imagem, modelo e ms (a mesma de hoje) |
| Transcrição | A tela grava áudio e envia em multipart; devolve o texto |
| Voz | Sintetiza "Olá, este é um teste de voz." e devolve o áudio em data URI |
| Vídeo | `GET /v1/query/video_generation?task_id=0`. Erro de autenticação (HTTP 401 ou `status_code` 1004) = falha; qualquer outra resposta = conexão OK. Não gera vídeo. |

O teste usa a configuração **salva** (por id), e não só a ativa, para permitir testar antes de
ativar.

## R7. Conversão dos dados atuais (FR-014)

- **Decision**: uma migração Alembic cria as cinco tabelas, converte os dados atuais e remove a
  tabela `app_settings`.
  - Fonte: o valor efetivo de hoje, ou seja, a coluna do `app_settings` se estiver preenchida,
    senão a variável do `.env` (lida com `python-dotenv`, como o `config.py`).
  - As chaves vindas do `app_settings` já estão cifradas e são copiadas como estão. As do `.env`
    são cifradas com `utils/crypto.encrypt`.
  - Cria uma linha por fornecedor **que tenha chave**, e a marca ativa quando era o provider em
    uso:
    - Texto: `OpenAI` (openai, `https://api.openai.com/v1`, `AI_TEXT_MODEL`) e
      `MiniMax` (openai, `https://api.minimax.io/v1`, `MINIMAX_TEXT_MODEL`).
    - Imagem: `OpenAI` (openai, `AI_IMAGE_MODEL`), `Seedream` (seedream, `BYTEPLUS_BASE_URL`,
      `SEEDREAM_MODEL`) e `MiniMax` (minimax, `MINIMAX_BASE_URL`, `MINIMAX_IMAGE_MODEL`).
    - Transcrição: `OpenAI` (openai, `STT_MODEL`, `STT_LANGUAGE`), ativa se houver chave.
    - Voz e Vídeo: `MiniMax` (`MINIMAX_VOICE_MODEL` / `MINIMAX_VIDEO_MODEL`), ativas se houver
      chave.
  - `downgrade` recria `app_settings` vazia e remove as cinco tabelas. As chaves voltam a vir do
    `.env`, e não há perda, porque o `.env` não é alterado.
- **Rationale**: atende o SC-003 sem recadastro, e o `.env` deixa de ser lido depois (FR-015).

## R8. O que sai do código (FR-021/022)

Removidos ou adaptados:

- `ai/__init__.py`: `env_ai_config`, `_overrides`, `current_config`, `minimax_config` e
  `configure` saem. `_build_provider(name, cfg)` vira `build_text_provider(AIConfig)` /
  `build_image_provider(AIConfig)`.
- `ai/minimax/config.py`: os `field(default_factory=_env(...))` de chave, URL, group_id e modelos
  viram campos obrigatórios ou constantes. Ficam só os parâmetros técnicos fixos (sample_rate,
  duração, voice_id padrão). `group_id` sai; o `MinimaxTextClient` sai, coberto pelo adaptador
  OpenAI-compatível.
- `ai/providers/seedream_provider.py`: recebe `base_url`, `api_key` e `model` pelo construtor e
  para de ler `settings`.
- `config.py`: saem `openai_api_key`, `ai_provider`, `ai_text_*`, `ai_image_*`, `stt_*`,
  `byteplus_*` e `seedream_model`.
- `ai/speech.py`: vira o adaptador `OpenAISpeechToText(AIConfig)`.
- `routers/voice.py` e `services/video_service.py`: passam a usar `TextToSpeech` montado da config
  de Voz ativa.
- `routers/image_test.py` (playground do payload MiniMax): usa a config de Imagem ativa e
  responde 400 se ela não for `minimax`.
- `routers/health.py` (`/health/ai`): usa a config de Texto ativa para nome e modelo.
- `models/app_settings.py`, `schemas/app_settings.py`, `services/app_settings_service.py` e as
  rotas `/admin/app-settings*`: removidos e substituídos por `ai_config_*`.
- `.env.example`, `README.md` e `sumi-api/ARCHITECTURE.md`: as variáveis de IA por fornecedor
  saem, e a documentação aponta para a tela.
- **Mantidos** (não são chave, modelo nem URL): `MINIMAX_PAYLOAD_LOG` e `SEEDREAM_PAYLOAD_LOG`,
  que são flags de log de depuração.

## R9. ComfyUI

- **Decision**: o provider ComfyUI fica fora do cadastro (premissa da spec) e, portanto,
  inacessível. Ele é **removido**, junto com o ramo `ai.name != "comfyui"` em
  `character_service.py` e o prompt SD associado, para não deixar código morto.
- **Alternatives considered**: manter o ComfyUI configurável por `.env`. Isso contraria o FR-022
  e mantém um caminho de configuração paralelo.
- **Ponto de confirmação com o usuário**: se o ComfyUI ainda é usado localmente, a alternativa é
  adicioná-lo como Tipo `comfyui` da Imagem (URL obrigatória, chave vazia), sem campo novo.

## R10. Tela

- **Decision**:
  - Sem Angular Material (o projeto não usa). O popup é o elemento nativo `<dialog>`, com
    `showModal()`, que já traz backdrop, Esc para fechar e foco preso.
  - Uma página com **abas** por tipo de IA (Texto | Imagem | Transcrição | Voz | Vídeo). Cada aba
    mostra um grid (`<table>`) e o botão "Nova configuração".
  - O grid tem um interruptor (checkbox estilizado) para ativar/desativar.
  - O popup traz um checkbox "Ativa".
- **Abstração no front (Princípio III)**: uma classe abstrata `AiConfigApi`, com a implementação
  `HttpAiConfigApi` registrada por `providers` na rota `app-settings`. O componente injeta
  `AiConfigApi`.
- O catálogo de Tipos e URLs padrão por tipo de IA fica numa constante no front (`ai-kinds.ts`).
  O backend valida o `kind` com a sua própria lista, curta e explícita.
