# sumi-api — Mapa da Arquitetura

## Estrutura de pastas

```
sumi-api/
├── alembic/                    # Migrations (env.py lê DATABASE_URL do .env)
│   └── versions/
├── models/                     # Modelos ORM (fora do pacote principal por design)
│   ├── base.py                 # DeclarativeBase
│   ├── all_models.py           # Importa todos os modelos (usado pelo Alembic)
│   ├── user.py, user_settings.py
│   ├── project.py, panel.py, project_character.py, project_scenario.py
│   ├── character.py, scenario.py, temp_portrait.py, visual_style.py
│   ├── series.py, series_project.py
│   ├── narration_voice.py, youtube_metadata.py, recomendacao.py
├── src/prompt_clinica/         # Pacote principal da API
│   ├── main.py                 # Entrypoint FastAPI — routers, CORS, handler global de erro, SPA estática
│   ├── config.py               # Settings (dataclass frozen) — lê variáveis do .env
│   ├── database.py             # Engine SQLAlchemy + SessionLocal + get_db()
│   ├── deps.py                 # Dependências de autenticação (usuário atual, admin)
│   ├── storage.py              # StorageBackend: LocalStorage | S3 (bucket compatível)
│   ├── styles.py, character_options.py, scenario_options.py   # catálogos fixos
│   ├── routers/                # Camada HTTP
│   ├── schemas/                # Pydantic (entrada/saída)
│   ├── services/               # Regras de negócio
│   ├── ai/                     # Integração com IA
│   │   ├── base.py             # Protocolos AIProvider (text / image), SpeechToText, TextToSpeech
│   │   ├── registry.py         # AIConfig, config ativa por tipo (banco) e fábricas de adaptadores
│   │   ├── types.py            # TextRequest/Response, ImageRequest/Response
│   │   ├── providers/          # openai (compatível), anthropic, seedream, minimax
│   │   ├── speech.py           # OpenAISpeechToText (transcrição)
│   │   ├── minimax/            # clientes MiniMax: imagem, voz (TTS), vídeo
│   │   ├── roteiro.py          # premissa → outline → quadros (prompt chaining)
│   │   ├── synopsis.py         # sinopse do projeto
│   │   └── youtube_metadata.py # título/descrição/tags para publicação
│   └── utils/security.py       # bcrypt + JWT
├── evals/                      # Avaliação LLM-as-judge (manual)
├── scripts/                    # Testes manuais dos providers de IA
├── tests/                      # pytest (apenas conftest.py por enquanto)
├── .env.example
├── alembic.ini
└── pyproject.toml / uv.lock
```

### Camadas

`routers` → `services` → (`ai`, `models` via SQLAlchemy, `storage`). Routers não acessam o provedor de IA diretamente; services não conhecem HTTP além de `HTTPException`.

O `_paths.py` adiciona `models/` ao `sys.path` em runtime para que os modelos sejam importáveis pela API e pelo Alembic sem fazer parte do pacote `prompt_clinica`.

---

## ORM — SQLAlchemy

```python
engine = create_engine(settings.database_url, echo=settings.is_development, pool_pre_ping=True)
```

A sessão é injetada via `Depends(get_db)` nos routers. IDs são UUIDs.

---

## Tarefas em segundo plano

Gerações demoradas usam `BackgroundTasks` do FastAPI com estado do job em um dicionário em memória; o frontend consulta o status por polling:

| Job | Disparo | Consulta |
|---|---|---|
| Retratos de personagem | `POST /characters/generate-portrait` | `GET /characters/portrait-job/{job_id}` |
| Imagem de cenário | `POST /scenarios/generate-scene` | `GET /scenarios/scene-job/{job_id}` |
| Vídeo (motion comic) | `POST /projects/{id}/export/video` | `GET /projects/{id}/export/video/{job_id}` |

Como o estado é em memória, jobs em andamento se perdem se o processo reiniciar e a API deve rodar com **uma única réplica/worker**.

---

## Swagger UI / ReDoc

Disponível **apenas em `APP_ENV=development`** (`/docs` e `/redoc`). Em produção ambas as URLs são desabilitadas em `main.py`, e o handler global devolve `"Erro interno no servidor."` sem detalhes da exceção.

---

## Endpoints registrados

| Router | Endpoints |
|---|---|
| `health.py` | `GET /health`, `/health/ai`, `/health/storage`, `/health/storage/config` |
| `auth.py` | `POST /auth/register`, `/auth/login`, `/auth/password-reset/request` |
| `admin.py` | `GET /admin/users/pending`, `POST /admin/users/{id}/approve`, `DELETE /admin/users/{id}` |
| `projects.py` | CRUD `/projects`; `synopsis/generate`; `characters`/`scenarios` (PUT); `panels` (listar, gerar roteiro, criar, ordenar, apagar, gerar imagens); `export/panels`; `export/video` (+ job); `youtube-metadata` (GET/PUT/generate) |
| `panels.py` | `PATCH`/`DELETE /panels/{id}`, `POST /panels/{id}/generate`, `/image`, `/bubbles/generate` |
| `characters.py` | `GET`/`POST /characters`, `PATCH /characters/{id}`, `POST /characters/delete-unused`, `generate-portrait` (+ job) |
| `scenarios.py` | `GET`/`POST /scenarios`, `PATCH /scenarios/{id}`, `POST /scenarios/delete-unused`, `generate-scene` (+ job) |
| `series.py` | CRUD `/series`, `PUT /series/{id}/projects` |
| `voice.py` | CRUD `/voice`, `POST /voice/test` |
| `public.py` | `GET /public/projects`, `GET /public/projects/{id}`, `POST /public/projects/{id}/reaction` (sem login) |
| `backup.py` | `GET /projects/{id}/backup` (.zip), `POST /projects/import` |
| `settings.py` | `GET`/`PUT /settings`, `GET /settings/local-ai/models` |
| `storage.py` | `GET /storage/{key}` — serve arquivos do storage |
| `styles.py`, `character_options.py`, `scenario_options.py` | Catálogos para os dropdowns |
| `image_test.py` | `POST /image-test` — bancada de teste de prompts de imagem |

---

## Migrations — Alembic

Rode sempre a partir de `sumi-api/` (o `env.py` coloca `src/` e `models/` no `sys.path`).

```bash
alembic revision --autogenerate -m "descricao_da_mudanca"   # após alterar models/
alembic upgrade head
alembic downgrade -1
alembic current
alembic history
```

Em produção o `docker-compose.yml` executa `alembic upgrade head` antes de iniciar o Uvicorn.

---

## Configuração de IA

Provedores, URLs, chaves e modelos de IA **não são variáveis de ambiente**. Eles ficam em cinco tabelas, uma por tipo (`ai_text_config`, `ai_image_config`, `ai_transcription_config`, `ai_voice_config`, `ai_video_config`), editadas na tela **Configurações do sistema** pelas rotas `/admin/ai-configs/{ai_type}` (só admin).

- Colunas comuns: `name`, `kind`, `base_url`, `api_key`, `model`, `active` e `updated_at`. A `api_key` é cifrada com Fernet derivada do `JWT_SECRET_KEY`. `ai_transcription_config` tem também `language`.
- Cada tabela tem no máximo uma linha ativa (índice único parcial `WHERE active`). Ativar uma desativa a anterior.
- `kind` permitido: texto `openai`/`anthropic`; imagem `openai`/`seedream`/`minimax`; transcrição `openai`; voz e vídeo `minimax`.
- `ai/registry.py` lê a linha ativa (`get_active`) e monta o adaptador (`build_text_provider`, `build_image_provider`, `build_speech_to_text`, `build_text_to_speech`). Depois de qualquer escrita no cadastro, o singleton `ai` é remontado na próxima chamada.
- Sem configuração ativa, a função responde 400: "Nenhuma IA de <tipo> ativa. Configure em Configurações do sistema."
- A migração `ai_config_tables` converteu a antiga tabela `app_settings` + variáveis de IA do `.env` em registros e removeu `app_settings`. O provider ComfyUI foi removido.

---

## Variáveis de ambiente

Lista completa e comentada em [`.env.example`](.env.example). Principais:

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DATABASE_URL` | Sim | — | Connection string PostgreSQL (`postgresql+psycopg2://...`) |
| `JWT_SECRET_KEY` | Sim | — | Chave de assinatura dos tokens |
| `JWT_EXPIRE_MINUTES` / `JWT_REMEMBER_EXPIRE_MINUTES` | Não | `60` / `43200` | Validade do token normal / “lembrar de mim” |
| `SEEDREAM_PAYLOAD_LOG` / `MINIMAX_PAYLOAD_LOG` | Não | `true` | Grava o payload de cada geração de imagem em `*_payload.log` |
| `STORAGE_BACKEND` | Não | `local` | `local` (pasta/volume `IMAGES_DIR`) ou bucket S3 compatível |
| `IMAGES_DIR` | Não | `static/images` | Pasta do storage local |
| `APP_ENV` | Não | `development` | `development` habilita docs e SQL echo |
| `ROOT_PATH` | Não | vazio | Prefixo quando servido sob sub-path (casa com `BASE_HREF` do Angular) |
| `CORS_ORIGINS` | Não | `http://localhost:4200` | Origens permitidas (vírgula) |

---

## Como executar

```bash
cd sumi-api
uv sync
cp .env.example .env             # configure DATABASE_URL e JWT_SECRET_KEY
uv run alembic upgrade head
uv run python -m prompt_clinica.main    # http://localhost:8000
```
