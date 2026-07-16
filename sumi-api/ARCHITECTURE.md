# sumi-api — Mapa da Arquitetura

## Estrutura de pastas

```
sumi-api/
├── alembic/                    # Migrations
│   ├── env.py                  # Configuração do Alembic (lê DATABASE_URL do .env)
│   ├── script.py.mako          # Template de migration
│   └── versions/               # Arquivos de migration gerados
├── models/                     # Modelos ORM (fora do pacote principal por design)
│   ├── base.py                 # DeclarativeBase do SQLAlchemy
│   ├── user.py                 # Modelos: User, UserOAuth, UserSession, PasswordResetToken
│   └── all_models.py           # Importa todos os modelos (usado pelo Alembic para detecção)
├── src/prompt_clinica/         # Pacote principal da API
│   ├── main.py                 # Entrypoint FastAPI — registra routers e middleware CORS
│   ├── config.py               # Settings (dataclass frozen) — lê variáveis do .env
│   ├── database.py             # Engine SQLAlchemy + SessionLocal + get_db()
│   ├── _paths.py               # Adiciona models/ ao sys.path em runtime
│   ├── routers/
│   │   ├── auth.py             # Endpoints /auth/*
│   │   └── health.py           # GET /health
│   ├── schemas/
│   │   └── auth.py             # Pydantic schemas: RegisterRequest, LoginRequest, TokenResponse…
│   ├── services/
│   │   └── auth_service.py     # Lógica de negócio: register, login, reset de senha
│   └── utils/
│       └── security.py         # bcrypt (hash/verify) + JWT (create/decode)
├── .env.example                # Variáveis necessárias — copie para .env e preencha
├── alembic.ini                 # Configuração base do Alembic (sqlalchemy.url sobrescrito em env.py)
└── pyproject.toml              # Dependências e configuração de ferramentas (ruff, pyright, pytest)
```

---

## ORM — SQLAlchemy

**Base declarativa:** `models/base.py`

**Modelos:** `models/user.py`

| Tabela                  | Classe                | Descrição                                    |
|-------------------------|-----------------------|----------------------------------------------|
| `users`                 | `User`                | Usuário principal (email/senha + OAuth)      |
| `user_oauth`            | `UserOAuth`           | Provedores OAuth vinculados (guest, Google…) |
| `user_sessions`         | `UserSession`         | Sessões JWT persistidas                      |
| `password_reset_tokens` | `PasswordResetToken`  | Tokens de redefinição de senha               |

O `_paths.py` adiciona `models/` ao `sys.path` em runtime para que os models sejam importáveis tanto pela API quanto pelo Alembic sem fazer parte do pacote `prompt_clinica`.

**Engine e sessão:** `src/prompt_clinica/database.py`

```python
engine = create_engine(settings.database_url, echo=settings.is_development, pool_pre_ping=True)
```

A sessão é injetada via `Depends(get_db)` nos routers.

---

## String de conexão com o banco

**Variável:** `DATABASE_URL` no arquivo `.env` (raiz de `sumi-api/`)

**Exemplo:**
```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/sumi_db
```

**Quem lê:**
- `src/prompt_clinica/config.py` → `Settings.database_url` → usado em `database.py`
- `alembic/env.py` → `os.environ["DATABASE_URL"]` → sobrescreve `sqlalchemy.url` do `alembic.ini`

O `alembic.ini` mantém `sqlalchemy.url` propositalmente em branco; o valor real vem sempre do `.env`.

---

## Swagger UI / ReDoc

Disponível **apenas em `APP_ENV=development`** (padrão):

| Interface | URL                        |
|-----------|----------------------------|
| Swagger   | `http://localhost:8000/docs`  |
| ReDoc     | `http://localhost:8000/redoc` |

Em produção (`APP_ENV=production`) ambas as URLs são desabilitadas automaticamente em `main.py`.

---

## Endpoints registrados

| Método | Path                          | Arquivo                          |
|--------|-------------------------------|----------------------------------|
| GET    | `/health`                     | `routers/health.py`              |
| POST   | `/auth/register`              | `routers/auth.py`                |
| POST   | `/auth/login`                 | `routers/auth.py`                |
| POST   | `/auth/oauth/guest`           | `routers/auth.py`                |
| POST   | `/auth/password-reset/request`| `routers/auth.py`                |

---

## Migrations — Alembic

### Setup inicial (primeira vez)

```bash
cd sumi-api
cp .env.example .env   # preencha DATABASE_URL e JWT_SECRET_KEY
```

### Gerar uma nova migration (após alterar models/)

```bash
alembic revision --autogenerate -m "descricao_da_mudanca"
```

### Aplicar todas as migrations pendentes

```bash
alembic upgrade head
```

### Outros comandos úteis

```bash
alembic downgrade -1          # desfaz a última migration
alembic current               # mostra a revisão atual do banco
alembic history               # lista todas as revisões
```

O `alembic/env.py` cuida de colocar `src/` e `models/` no `sys.path` antes de importar a `Base`, então **rode sempre a partir de `sumi-api/`**.

---

## Variáveis de ambiente

| Variável            | Obrigatória | Padrão                       | Descrição                              |
|---------------------|-------------|------------------------------|----------------------------------------|
| `DATABASE_URL`      | Sim         | —                            | Connection string PostgreSQL           |
| `JWT_SECRET_KEY`    | Sim         | —                            | Chave de assinatura dos tokens JWT     |
| `GOOGLE_API_KEY`    | Não         | `""`                         | Gemini / Google AI                     |
| `OPENAI_API_KEY`    | Não         | `""`                         | OpenAI                                 |
| `APP_ENV`           | Não         | `development`                | `development` habilita docs + SQL echo |
| `APP_HOST`          | Não         | `0.0.0.0`                    | Host do uvicorn                        |
| `APP_PORT`          | Não         | `8000`                       | Porta do uvicorn                       |
| `APP_RELOAD`        | Não         | `true`                       | Hot-reload do uvicorn                  |
| `JWT_EXPIRE_MINUTES`| Não         | `60`                         | Validade do token em minutos           |
| `CORS_ORIGINS`      | Não         | `http://localhost:4200`      | Origins permitidas (vírgula-separadas) |

---

## Como executar

```bash
cd sumi-api
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .

cp .env.example .env             # configure DATABASE_URL e JWT_SECRET_KEY

alembic upgrade head             # cria/atualiza as tabelas

python -m prompt_clinica.main    # inicia em http://localhost:8000
```
