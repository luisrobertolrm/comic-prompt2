# Sumi — HQ com IA

> Produza quadrinhos completos a partir de uma faísca de ideia, com IA guiando cada etapa — do roteiro à narração em vídeo.

Repositório: <https://github.com/luisrobertolrm/comic-prompt2>

---

## Visão geral do sistema

**Sumi** é uma plataforma de criação de histórias em quadrinhos assistida por inteligência artificial. O usuário parte de uma premissa e, etapa a etapa, a IA propõe sinopse, personagens, cenários, roteiro, quadros e balões. O sistema mantém a **coerência visual dos personagens** entre quadros e projetos e, ao final, gera páginas para leitura, um link público na galeria e um **motion comic narrado** em MP4 com voz por personagem.

### Fluxo de criação

```
Ideia → Personagens → Cenários → Roteiro → Revisão → Editor → Finalizar → Vídeo
```

| Etapa | Rota | O que acontece |
|---|---|---|
| **Ideia** | `/projects/new` | Premissa, gênero, tom, nº de páginas, estilo visual, modo de cor; sinopse gerada por IA |
| **Personagens** | `/projects/new/characters` | Biblioteca reutilizável; criação manual ou retratos gerados por IA a partir de atributos (gênero, etnia, tipo físico, tom de pele, estilo) |
| **Cenários** | `/projects/new/scenarios` | Biblioteca de cenários reutilizáveis; imagem de cena gerada por IA |
| **Roteiro** | `/projects/:id/script` | A IA propõe o storyboard: um quadro por beat com legenda, personagens, enquadramento e prompt visual |
| **Revisão** | `/projects/:id/review` | Cada quadro é editado, reordenado, regerado (imagem/balões) ou removido |
| **Editor** | `/projects/:id/editor` | Diagramação da página e balões arrastáveis (sem IA) |
| **Finalizar** | `/projects/:id/final` | Preview das páginas e exportação dos quadros |
| **Vídeo** | `/projects/:id/video` | Motion comic: narração TTS (MiniMax) por personagem, render MP4 com ffmpeg, metadados de YouTube gerados por IA |

### Outros recursos

- **Galeria pública** (`/` e `/p/:id`) — leitura sem login, com vídeo e reações (curtir/não curtir).
- **Séries** — agrupam vários projetos em ordem.
- **Aprovação de usuários** — novos cadastros ficam pendentes até um administrador aprovar (`/admin`).
- **Configurações por usuário** — permite usar uma IA local compatível com a API OpenAI (ex.: Ollama) para o roteiro.
- **Backup** — exportação/importação de um projeto completo em `.zip` (dados + imagens + áudios).
- **Vozes de narração** — cadastro de vozes MiniMax e atribuição ao narrador e a cada personagem.

---

## Arquitetura

Monorepo com dois projetos e uma stack de banco separada:

```
comic-prompt/
├── sumi-api/                 ← backend Python 3.13 (FastAPI + SQLAlchemy 2 + Alembic)
│   ├── src/prompt_clinica/   ← pacote da API (routers, services, schemas, ai, storage)
│   ├── models/               ← modelos ORM (fora do pacote; ver sumi-api/ARCHITECTURE.md)
│   ├── alembic/              ← migrations
│   ├── evals/                ← avaliação LLM-as-judge (manual, fora do CI)
│   └── scripts/              ← scripts de teste manual dos providers de IA
├── sumi-web/                 ← frontend Angular 21 (standalone components)
│   └── src/app/{core,features,shared}
├── sumi-mobile/              ← app Android em Flutter (consome a mesma API; ver sumi-mobile/README.md)
│   └── lib/{core,features,shared}
├── postgres/                 ← stack Docker do PostgreSQL (separada e reutilizável)
├── comic-prompt/             ← protótipo HTML/React (referência visual)
├── docs/                     ← análises e especificações
├── Dockerfile                ← build multi-stage: Angular + API em uma imagem
├── docker-compose.yml        ← stack de produção da Sumi
└── .github/workflows/        ← deploy contínuo (GitHub Actions, runner self-hosted)
```

Em produção a **API serve o build do Angular** como arquivos estáticos — não há servidor web separado para o frontend.

```
Navegador ──HTTPS──► Contêiner sumi (FastAPI + SPA Angular)
                        ├── routers → services → ai/providers ──► OpenAI / BytePlus Seedream / MiniMax / ComfyUI
                        ├── SQLAlchemy ─────────────────────────► Contêiner PostgreSQL (rede shared-db)
                        └── storage.py ─────────────────────────► Volume Docker (imagens, áudios, vídeos)
```

Detalhes da API (camadas, endpoints, variáveis): [`sumi-api/ARCHITECTURE.md`](sumi-api/ARCHITECTURE.md).

---

## Backend — `sumi-api`

### Stack

| Componente | Tecnologia |
|---|---|
| Framework web | **FastAPI** (Uvicorn) |
| ORM | **SQLAlchemy 2** (síncrono, `psycopg2`) |
| Banco de dados | **PostgreSQL 16** |
| Migrations | **Alembic** |
| Validação | **Pydantic v2** |
| Gerenciador de pacotes | **uv** (`pyproject.toml` + `uv.lock`) |
| LLM (texto) | OpenAI (`gpt-4o-mini` padrão; suporta gpt-5/o-series), MiniMax, ou IA local OpenAI-compatível via LangChain |
| Imagem | OpenAI `gpt-image-1`, BytePlus **Seedream**, MiniMax `image-01`, **ComfyUI** (Stable Diffusion local) |
| Voz (TTS) | MiniMax `speech-2.8-hd` |
| Vídeo | ffmpeg (via `imageio-ffmpeg`) — quadros + áudio → MP4 |
| Autenticação | JWT + bcrypt |
| Qualidade | `ruff`, `pyright` (pytest configurado, sem testes ainda) |

### Provedores de IA

Toda chamada de IA passa pelo contrato `AIProvider` (`src/prompt_clinica/ai/base.py`), com implementações em `ai/providers/`. O provedor é escolhido por variável de ambiente:

```dotenv
AI_PROVIDER=openai          # openai | minimax | comfyui | seedream
AI_TEXT_PROVIDER=           # opcional: sobrescreve só o texto
AI_IMAGE_PROVIDER=          # opcional: sobrescreve só a imagem
```

Gerações demoradas (retratos, cenas, vídeo) rodam em `BackgroundTasks` do FastAPI e o frontend acompanha o job por polling (`/characters/portrait-job/{id}`, `/scenarios/scene-job/{id}`, `/projects/{id}/export/video/{job_id}`). O estado dos jobs fica em memória do processo.

### Geração de imagem — Seedream

Com `AI_IMAGE_PROVIDER=seedream` (BytePlus ModelArk), o `size` enviado à API deve ser uma dimensão concreta. Dimensões recomendadas por razão de aspecto:

| Razão | 2K | 3K | 4K |
|-------|----|----|----|
| 1:1   | 2048×2048 | 3072×3072 | 4096×4096 |
| 3:4   | 1728×2304 | 2592×3456 | 3520×4704 |
| 4:3   | 2304×1728 | 3456×2592 | 4704×3520 |
| 16:9  | 2848×1600 | 4096×2304 | 5504×3040 |
| 9:16  | 1600×2848 | 2304×4096 | 3040×5504 |
| 3:2   | 2496×1664 | 3744×2496 | 4992×3328 |
| 2:3   | 1664×2496 | 2496×3744 | 3328×4992 |
| 21:9  | 3136×1344 | 4704×2016 | 6240×2656 |

A resolução 1K não é suportada.

### Evals

`sumi-api/evals/` contém um harness LLM-as-judge que mede se roteiros e imagens respeitam ambientação, personagens e atributos. Roda **manualmente** (consome tokens) — ver [`sumi-api/evals/README.md`](sumi-api/evals/README.md).

---

## Frontend — `sumi-web`

| Componente | Tecnologia |
|---|---|
| Framework | **Angular 21** (standalone components, rotas lazy) |
| Estilos | SCSS com os tokens do protótipo, sem framework CSS |
| HTTP | `HttpClient` + `auth.interceptor.ts` (JWT) |
| Rotas | Angular Router com `authGuard` e `adminGuard` |
| Testes | Vitest (`ng test`) |

```
src/app/
├── core/       ← guards, interceptor, services HTTP, models
├── features/   ← auth, gallery, home, library, series, projects/*, settings, admin, shell
└── shared/     ← tag-picker, text-reader, voice-preview-button
```

O design segue o protótipo em `comic-prompt/` (abra `comic-prompt/Sumi - HQ com IA.html`). Tokens principais:

```scss
--paper: #F4ECDB;  --ink: #1E1812;  --rule: #E2D5B8;
--blush: #E5A6A8;  --peach: #E7BD8E;  --mint: #A9CDB6;  --lilac: #B8A9CE;  --sky: #A9C0D2;
--serif: "Shippori Mincho";  --sans: "DM Sans";  --mono: "JetBrains Mono";  --hand: "Caveat";
```

---

## Desenvolvimento local

### Backend

```bash
cd sumi-api
uv sync                          # cria .venv e instala dependências
cp .env.example .env             # preencha DATABASE_URL, JWT_SECRET_KEY e a chave do provider de IA
uv run alembic upgrade head
uv run python -m prompt_clinica.main   # http://localhost:8000  (Swagger em /docs)
```

Verificações: `uv run ruff check` e `uv run pyright`. O `pytest` está configurado no `pyproject.toml`, mas a suíte de testes ainda não foi escrita (`tests/` tem apenas o `conftest.py`).

### Frontend

```bash
cd sumi-web
npm install
npm start                        # http://localhost:4200
```

---

## Implantação

A produção roda em **servidor Linux próprio (Debian / CasaOS) com Docker Compose**. São duas stacks:

1. **`postgres/`** — PostgreSQL 16 com volume persistente e healthcheck, na rede Docker externa `shared-db` (reutilizável por outras aplicações).
2. **Raiz (`docker-compose.yml`)** — a imagem do `Dockerfile` multi-stage (Node 22 compila o Angular; Python 3.13 + uv roda a API). Ao subir, executa `alembic upgrade head` e depois o Uvicorn; imagens/áudios/vídeos ficam no volume `images`; `restart: unless-stopped`.

Instalação inicial: [`install-debian.sh`](install-debian.sh) (Linux) ou [`INSTALL_WINDOWS.md`](INSTALL_WINDOWS.md) / [`install-windows.ps1`](install-windows.ps1). Variáveis de produção: [`.env.production.example`](.env.production.example). Para servir sob um sub-path atrás de proxy reverso, use `BASE_HREF=/sumi/` e `ROOT_PATH=/sumi`.

### Deploy contínuo

[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml): a cada push na `main`, um **runner self-hosted** no servidor faz checkout, sincroniza o código com `rsync` para `/DATA/comic-prompt2` (preservando o `.env`) e executa `docker compose up -d --build`.

---

## Secrets

Nenhum segredo é versionado. Use `sumi-api/.env.example` (dev) e `.env.production.example` (produção) como modelo; os arquivos `.env` estão no `.gitignore`.

---

## Documentação

| Documento | Conteúdo |
|---|---|
| [`sumi-api/ARCHITECTURE.md`](sumi-api/ARCHITECTURE.md) | Camadas da API, endpoints, migrations, variáveis |
| [`sumi-api/evals/README.md`](sumi-api/evals/README.md) | Harness de avaliação de IA |
| [`docs/analise-pipeline-ia.md`](docs/analise-pipeline-ia.md) | Onde a IA atua em cada tela |
| [`docs/auth/`](docs/auth/) | Fluxos de cadastro e login |
| [`INSTALL_WINDOWS.md`](INSTALL_WINDOWS.md) | Instalação com Docker Desktop |
| [`entrega/`](entrega/) | Documento acadêmico da sistematização |
