# Sumi — HQ com IA

> Produza quadrinhos completos a partir de uma faísca de ideia, com IA guiando cada etapa — do roteiro à narração em vídeo.

---

## Visão geral do sistema

**Sumi** é uma plataforma de criação de histórias em quadrinhos assistida por inteligência artificial. O usuário parte de uma frase inicial e, etapa a etapa, a IA propõe personagens, roteiro, quadros e balões. O sistema mantém a **coerência visual dos personagens** entre quadros e projetos, e ao final gera tanto páginas para leitura quanto um **motion comic narrado** com vozes por personagem.

### Fluxo de criação

```
Ideia → Personagens → Roteiro → Revisão quadro a quadro → Editor visual → Exportar
                                                                       ↓
                                                              Vídeo narrado (motion comic)
```

| Etapa | O que acontece |
|---|---|
| **1 · Ideia** | Usuário descreve a premissa em linguagem natural; define gênero, tom emocional, nº de páginas e estilo visual |
| **2 · Personagens** | Seleciona da biblioteca, cria manualmente ou pede à IA 4 retratos candidatos a partir de uma descrição textual |
| **3 · Roteiro** | A IA propõe o storyboard completo: um card por quadro com caption, personagem, enquadramento e prompt visual |
| **4 · Revisão** | Cada quadro é aprovado, regerado ou editado individualmente (caption, balões, tipo de balão, prompt visual) |
| **5 · Editor visual** | Layout da página ajustado com grade dinâmica; balões arrastáveis sobre os quadros |
| **6 · Finalizar** | Exportação em PDF, PNG, EPUB e link de leitura compartilhável |
| **7 · Vídeo** | Motion comic narrado: cada quadro vira uma cena, narrador + voz por personagem, trilha sonora |

### Recursos-chave

- **Biblioteca de personagens reutilizáveis** — ficha visual (aparência, figurino, paleta) e personalidade são preservadas em todas as HQs do usuário.
- **Consistência visual via IA** — o prompt de cada quadro é construído a partir da ficha do personagem, garantindo coerência entre cenas.
- **Balões tipados** — fala, pensamento e grito; posição e lado configuráveis.
- **Múltiplos estilos de quadro** — Shojo clássico, linha moderna limpa, tinta marcada, minimalista.
- **Múltiplos layouts de página** — Mangá vertical, grade ocidental, dinâmico mangá.
- **Motion comic** — player com timeline de cenas, elenco de voz por personagem, transições (corte, fade, zoom Ken Burns, deslize), exportação de vídeo.
- **Multilíngue** — balões em PT-BR, japonês, inglês ou espanhol.

---

## Arquitetura do projeto

O sistema é dividido em dois projetos independentes que convivem no mesmo repositório:

```
comic-prompt/                   ← raiz do repositório
├── sumi-api/                   ← backend Python (FastAPI + SQLAlchemy)
│   ├── sumi/                   ← pacote Python principal
│   │   ├── core/               ← entidades de domínio e ORM
│   │   ├── infra/              ← banco, LLMs, serviços externos
│   │   ├── services/           ← regras de negócio
│   │   └── api/                ← endpoints HTTP (FastAPI)
│   ├── tests/
│   ├── alembic/                ← migrations
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── .env.example
│   └── Dockerfile
├── sumi-web/                   ← frontend Angular
│   ├── src/
│   │   └── app/
│   │       ├── core/           ← guards, interceptors, auth
│   │       ├── shared/         ← componentes, pipes, diretivas reutilizáveis
│   │       ├── features/       ← módulos de feature (projects, characters, editor, video)
│   │       └── layout/         ← shell, sidebar, topbar
│   ├── angular.json
│   ├── package.json
│   └── Dockerfile
├── comic-prompt/               ← protótipo HTML/React (referência visual)
├── docker-compose.yml
└── README.md
```



> **Por que separados?** O Angular tem toolchain próprio (`npm`, `ng`), ciclo de build independente e pode ser hospedado em CDN. Manter os dois na raiz do mesmo repositório (monorepo simples) facilita PRs que afetam os dois lados sem precisar de submódulos.

---

## Backend Python — `sumi-api`

### Stack

| Componente | Tecnologia |
|---|---|
| Framework web | **FastAPI** |
| ORM | **SQLAlchemy 2** (async) |
| Banco de dados | **PostgreSQL** (abstrato via ORM, mas driver configurado para `asyncpg`) |
| Migrations | **Alembic** |
| Validação | **Pydantic v2** |
| LLM | SDK Anthropic (Claude) — chamados na camada `infra` |
| Geração de imagem | API de terceiros (configurável via `infra`) |
| TTS / narração | API de terceiros (configurável via `infra`) |
| Autenticação | JWT via `python-jose` |
| Testes | `pytest` + `httpx` |

### Namespaces

#### `sumi/core/`
Entidades puras de domínio e modelos ORM. Não depende de nenhum outro namespace interno.

```
core/
├── models/
│   ├── project.py          # Project, Page, Panel
│   ├── character.py        # Character, CharacterTrait, CharacterPalette
│   ├── bubble.py           # Bubble, BubbleKind
│   ├── user.py             # User
│   └── __init__.py
├── enums.py                # PanelStatus, BubbleKind, PanelAspect, PanelTone...
├── base.py                 # declarative_base, TimestampMixin
└── __init__.py
```

- Todos os modelos herdam de `base.TimestampMixin` (`created_at`, `updated_at`).
- IDs são UUIDs gerados na aplicação.
- Relacionamentos declarados aqui; queries ficam no `infra`.

#### `sumi/infra/`
Conexão com recursos externos. Depende de `core`. Nunca importado por `api` diretamente — apenas via `services`.

```
infra/
├── database/
│   ├── session.py          # AsyncSessionFactory, get_db (dependency)
│   ├── repositories/       # um repo por aggregate root (ProjectRepo, CharacterRepo…)
│   └── __init__.py
├── migrations/             # pasta gerenciada pelo Alembic
├── llm/
│   ├── claude_client.py    # wrapper do SDK Anthropic com prompt caching
│   ├── prompts/            # arquivos .jinja2 com templates de prompt
│   └── __init__.py
├── image_gen/
│   ├── client.py           # abstração para API de geração de imagem
│   └── __init__.py
├── tts/
│   ├── client.py           # abstração para Text-to-Speech
│   └── __init__.py
└── __init__.py
```

- A connection string do banco **nunca é hardcoded** — lida sempre de `settings.DATABASE_URL`.
- Cada repository expõe métodos async puros; sem lógica de negócio.

#### `sumi/services/`
Regras de negócio. Depende de `core` e `infra`. Retorna `ViewModels` (Pydantic) para a camada `api`.

```
services/
├── project_service.py      # criar, editar, listar projetos
├── character_service.py    # CRUD + geração IA de personagens
├── script_service.py       # proposta de roteiro via LLM
├── panel_service.py        # aprovação, regeneração de quadros
├── video_service.py        # montagem do motion comic
├── export_service.py       # PDF, PNG, EPUB
├── viewmodels/
│   ├── project_vm.py
│   ├── character_vm.py
│   ├── panel_vm.py
│   └── video_vm.py
└── __init__.py
```

#### `sumi/api/`
Endpoints FastAPI. Depende apenas de `services` e `core.enums`. Não acessa banco diretamente.

```
api/
├── main.py                 # cria a instância FastAPI, registra routers, CORS, middleware
├── dependencies.py         # get_current_user, get_db forwarding
├── routers/
│   ├── projects.py         # /projects
│   ├── characters.py       # /characters
│   ├── panels.py           # /panels
│   ├── script.py           # /script/generate
│   ├── video.py            # /video
│   └── auth.py             # /auth/token
└── __init__.py
```

### Banco de dados

O ORM é configurado para PostgreSQL mas abstrai o dialeto. Para trocar de banco basta alterar `DATABASE_URL` no `.env` (SQLAlchemy reconhece o dialeto pelo prefixo da URL).

**Migrations com Alembic:**

```bash
# Criar uma migration
alembic revision --autogenerate -m "add character palette table"

# Aplicar migrations
alembic upgrade head

# Reverter última migration
alembic downgrade -1
```

### Geração de imagem — Seedream 5.0 lite

Provider de imagem ativo via `AI_IMAGE_PROVIDER=seedream` (BytePlus ModelArk),
modelo `SEEDREAM_MODEL=seedream-5-0-lite`. O `size` enviado à API deve ser uma
dimensão concreta — abaixo as dimensões recomendadas por razão de aspecto e
resolução-alvo.

| Razão | 1K | 2K | 3K | 4K |
|-------|----|----|----|----|
| 1:1   | Not supported | 2048×2048 | 3072×3072 | 4096×4096 |
| 3:4   | Not supported | 1728×2304 | 2592×3456 | 3520×4704 |
| 4:3   | Not supported | 2304×1728 | 3456×2592 | 4704×3520 |
| 16:9  | Not supported | 2848×1600 | 4096×2304 | 5504×3040 |
| 9:16  | Not supported | 1600×2848 | 2304×4096 | 3040×5504 |
| 3:2   | Not supported | 2496×1664 | 3744×2496 | 4992×3328 |
| 2:3   | Not supported | 1664×2496 | 2496×3744 | 3328×4992 |
| 21:9  | Not supported | 3136×1344 | 4704×2016 | 6240×2656 |

**Observações:**
- A coluna **1K não é suportada** para nenhuma razão de aspecto.
- Na imagem original, na coluna **3K** as posições de `3:2` e `2:3` aparecem
  trocadas em relação às outras colunas — lá, `2:3 : 2496×3744` vem antes de
  `3:2 : 3744×2496`. A tabela acima mantém os valores como na imagem, alinhados
  por razão de aspecto.

---

## Frontend Angular — `sumi-web`

O design visual segue **rigorosamente** o protótipo em `comic-prompt/`. Os tokens de design estão documentados abaixo.

### Stack

| Componente | Tecnologia |
|---|---|
| Framework | **Angular 18+** (standalone components) |
| Estilos | **SCSS** com os tokens abaixo, sem framework CSS externo |
| HTTP | `HttpClient` com interceptor de JWT |
| Estado | **NgRx Signals** (ou Akita — a definir) |
| Rotas | Angular Router |
| Formulários | Reactive Forms |
| Build | Angular CLI / esbuild |

### Tokens de design (importados como variáveis SCSS)

```scss
// Paleta papel
--paper:     #F4ECDB;
--paper-2:   #FAF3E2;
--paper-3:   #FFFAEC;

// Tinta
--ink:       #1E1812;
--ink-2:     #4A4034;
--ink-3:     #8A7B6A;
--ink-4:     #B6A790;

// Linhas
--rule:      #E2D5B8;

// Acentos pastel (shojo)
--blush:     #E5A6A8;    --blush-soft:  #F4D6D7;
--peach:     #E7BD8E;    --peach-soft:  #F6DEC2;
--mint:      #A9CDB6;    --mint-soft:   #DBEADF;
--lilac:     #B8A9CE;    --lilac-soft:  #E1D8EC;
--sky:       #A9C0D2;    --sky-soft:    #D8E2EC;

// Tipografia
--serif:     "Shippori Mincho", "Cormorant Garamond", Georgia, serif;
--sans:      "DM Sans", -apple-system, "Segoe UI", system-ui, sans-serif;
--mono:      "JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace;
--hand:      "Caveat", "Bradley Hand", cursive;
```

O layout principal é `sidebar (220px) + main (1fr)`. A topbar tem `56px` de altura e é sticky. O conteúdo tem `padding: 32px 36px 80px` e `max-width: 1200px`.

### Módulos de feature

| Módulo | Rotas | Descrição |
|---|---|---|
| `projects` | `/`, `/library` | Lista de projetos, biblioteca de personagens |
| `create` | `/new`, `/characters` | Wizard de criação (ideia + personagens) |
| `story` | `/script`, `/review` | Roteiro e revisão quadro a quadro |
| `editor` | `/editor` | Editor visual de página |
| `export` | `/final`, `/video` | Exportação e motion comic |

---

## Gerenciamento de secrets e variáveis de ambiente

### Configuração

O backend lê todas as configurações de variáveis de ambiente (via `pydantic-settings`). **Nunca commite valores reais no repositório.**

**`sumi-api/.env.example`** — copie para `.env` e preencha:

```dotenv
# ── Banco de dados ──────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://sumi_user:senha_aqui@localhost:5432/sumi_db

# ── Segurança ───────────────────────────────────────────────────────────
SECRET_KEY=gere-uma-chave-aleatória-com-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ── IA — LLM ────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-...

# ── IA — Geração de imagem ──────────────────────────────────────────────
IMAGE_GEN_PROVIDER=openai          # openai | stability | fal
IMAGE_GEN_API_KEY=sk-...

# ── IA — Text-to-Speech ─────────────────────────────────────────────────
TTS_PROVIDER=elevenlabs            # elevenlabs | google | openai
TTS_API_KEY=...

# ── Armazenamento (imagens geradas, vídeos) ─────────────────────────────
STORAGE_BACKEND=local              # local | s3
STORAGE_LOCAL_PATH=./media
# S3_BUCKET=
# S3_REGION=
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=

# ── Aplicação ───────────────────────────────────────────────────────────
ENVIRONMENT=development            # development | staging | production
DEBUG=true
ALLOWED_ORIGINS=http://localhost:4200
```

### Como carregar o `.env` ao rodar o projeto

**Desenvolvimento local (uvicorn):**

```bash
# Opção 1 — uvicorn lê .env automaticamente via pydantic-settings
cd sumi-api
uvicorn sumi.api.main:app --reload

# Opção 2 — passar explicitamente com dotenv
dotenv run -- uvicorn sumi.api.main:app --reload

# Opção 3 — exportar antes de rodar
export $(grep -v '^#' .env | xargs)
uvicorn sumi.api.main:app --reload
```

**Docker Compose (recomendado para ambiente completo):**

```bash
# Sobe banco + api + frontend
docker-compose up --build

# Apenas a api com .env externo
docker-compose run --env-file .env api
```

**`docker-compose.yml` de referência:**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: sumi_user
      POSTGRES_PASSWORD: senha_aqui
      POSTGRES_DB: sumi_db
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: ./sumi-api
    env_file: ./sumi-api/.env
    ports:
      - "8000:8000"
    depends_on:
      - db
    command: uvicorn sumi.api.main:app --host 0.0.0.0 --port 8000 --reload

  web:
    build: ./sumi-web
    ports:
      - "4200:80"
    depends_on:
      - api

volumes:
  pgdata:
```

---

## Primeiros passos (desenvolvimento)

### Backend

```bash
cd sumi-api

# Criar ambiente virtual e instalar dependências
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Configurar banco local
cp .env.example .env
# edite .env com suas credenciais

# Criar banco e aplicar migrations
createdb sumi_db                 # ou use pgAdmin / docker
alembic upgrade head

# Rodar a API
uvicorn sumi.api.main:app --reload
# Docs: http://localhost:8000/docs
```

### Frontend

```bash
cd sumi-web

npm install
ng serve
# App: http://localhost:4200
```

---

## Referência visual

O protótipo interativo em `comic-prompt/` é a fonte da verdade para o design. Abra `comic-prompt/Sumi - HQ com IA.html` em qualquer browser para ver o design system completo com todos os componentes, paletas e fluxos.

Os screenshots em `comic-prompt/screenshots/` mostram os estados principais de cada tela.

---

## Próximos passos planejados

- [ ] Scaffolding do projeto Python (`pyproject.toml`, estrutura de pastas)
- [ ] Scaffolding do projeto Angular (workspace + módulos)
- [ ] Modelos ORM e primeira migration
- [ ] Endpoint `/auth/token` + JWT
- [ ] Endpoint `/script/generate` com integração Claude
- [ ] Endpoint `/characters/generate` com geração de 4 candidatos
- [ ] Endpoint `/panels/{id}/image` com geração de imagem
- [ ] Endpoint `/video/render` com TTS e montagem
- [ ] Deploy (docker-compose produção + variáveis em secrets manager)
