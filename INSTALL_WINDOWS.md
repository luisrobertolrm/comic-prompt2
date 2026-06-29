# Instalação no Windows — Sumi

Guia para rodar a aplicação completa (API FastAPI + app Angular + PostgreSQL) em
uma máquina Windows. A app inteira roda em **um único container**; o Postgres sobe
em outro. Tudo via Docker Desktop, sem instalar Python/Node na máquina.

> Se a máquina for Linux, use o mesmo `docker-compose.yml` — os passos são equivalentes.

---

## 1. Pré-requisitos

- **Windows 10/11** com virtualização habilitada na BIOS.
- **Docker Desktop** — https://www.docker.com/products/docker-desktop/
  - Na instalação, deixe marcado **"Use WSL 2 based engine"** (padrão).
  - Depois de instalar, **abra o Docker Desktop** e espere o ícone ficar verde
    ("Engine running"). Ele precisa estar rodando para os comandos funcionarem.
- **Git** (para clonar o repositório) — https://git-scm.com/download/win

Para confirmar que o Docker está pronto, abra o **PowerShell** e rode:

```powershell
docker version
```

Se aparecerem as versões de Client **e** Server, está tudo certo.

---

## 2. Obter o código

```powershell
git clone https://github.com/luisrobertolrm/comic-prompt2.git
cd comic-prompt2
```

> Se já tiver a pasta, só entre nela com `cd comic-prompt2`.

---

## 3. Arquitetura das stacks

O Postgres é uma **stack separada** (em `postgres/`), independente da sumi. Isso
permite gerenciá-lo sozinho e **reutilizá-lo em outras aplicações**. As duas stacks
se enxergam por uma rede Docker compartilhada chamada `shared-db`.

```
shared-db (rede)
├── postgres/   → container 'postgres'  (porta 5432 no host)
└── (raiz)      → container 'api' da sumi  (porta 8000 no host)
```

## 4. Configurar os `.env`

São **dois** arquivos `.env` (nenhum vai para o Git). Há modelos prontos.

**Postgres** (`postgres/.env`):
```powershell
Copy-Item postgres\.env.example postgres\.env
notepad postgres\.env
```
| Variável            | O que colocar                          |
|---------------------|----------------------------------------|
| `POSTGRES_PASSWORD` | Uma senha forte para o banco.          |

**Sumi** (`.env` na raiz):
```powershell
Copy-Item .env.production.example .env
notepad .env
```
| Variável            | O que colocar                                                        |
|---------------------|----------------------------------------------------------------------|
| `POSTGRES_PASSWORD` | **A mesma senha** definida em `postgres\.env`.                       |
| `JWT_SECRET_KEY`    | Uma string aleatória (veja abaixo como gerar).                       |
| `OPENAI_API_KEY`    | Sua chave da OpenAI (provider padrão). Ou configure outro provider.  |

> ⚠️ `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB` precisam ser **iguais**
> nos dois `.env` — é como a sumi autentica no Postgres.

Para gerar o `JWT_SECRET_KEY`, rode no PowerShell:

```powershell
-join ((1..64) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })
```

Copie o resultado para a linha `JWT_SECRET_KEY=` no `.env` da raiz.

---

## 5. Instalar e subir

Com o Docker Desktop aberto, rode o script de instalação na raiz do projeto:

```powershell
.\install-windows.ps1
```

O script:
1. confere se o Docker está instalado e rodando;
2. cria a rede `shared-db` (se ainda não existir);
3. cria os dois `.env` a partir dos exemplos, se faltarem (e pede para editar);
4. sobe a stack do Postgres;
5. builda e sobe a sumi, rodando as migrations automaticamente.

> Se preferir fazer manualmente, os comandos equivalentes são:
> ```powershell
> docker network create shared-db
> docker compose -f postgres\docker-compose.yml up -d
> docker compose up -d --build
> ```
> As migrations (`alembic upgrade head`) rodam no start da sumi.

O **primeiro build demora** alguns minutos (baixa imagens, compila o Angular e
instala as dependências Python). Builds seguintes usam cache e são rápidos.

---

## 6. Acessar a aplicação

Quando os containers subirem:

- **App:** http://localhost:8000/
- **API (Swagger):** http://localhost:8000/docs
- **Postgres:** `localhost:5432` (para clientes/outras apps)

Crie um usuário pela tela de cadastro e comece a usar.

> Para mudar a porta, edite `APP_PORT` no `.env` (ex.: `APP_PORT=9000` → http://localhost:9000/).

---

## 7. Comandos do dia a dia

**Sumi** (na raiz do projeto):

```powershell
docker compose ps              # status dos containers da sumi
docker compose logs -f api     # logs da API (Ctrl+C para sair)
docker compose stop            # parar a sumi
docker compose up -d --build   # atualizar após um git pull
docker compose down            # remover o container da sumi (imagens preservadas)
```

**Postgres** (stack separada):

```powershell
docker compose -f postgres\docker-compose.yml ps
docker compose -f postgres\docker-compose.yml stop
docker compose -f postgres\docker-compose.yml up -d
```

**Persistência:** o banco fica no volume `pgdata` (stack do Postgres) e as imagens
no volume `images` (stack da sumi). Sobrevivem a `stop`/`down` e a rebuilds.
Só são apagados com `down -v` **na respectiva stack**:

```powershell
docker compose down -v                                   # apaga imagens geradas (sumi)
docker compose -f postgres\docker-compose.yml down -v    # ATENÇÃO: apaga o BANCO inteiro
```

> Como o Postgres é independente, parar/atualizar a sumi **não derruba o banco**.

---

## 8. Atualizar para uma versão nova

```powershell
git pull
docker compose up -d --build
```

As migrations novas rodam sozinhas no start. (A stack do Postgres só precisa subir
de novo se o `postgres\docker-compose.yml` tiver mudado.)

---

## 9. Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| `error during connect ... docker daemon` | Docker Desktop não está aberto. Abra-o e espere ficar verde. |
| `network shared-db not found` | Rode `docker network create shared-db` antes de subir as stacks. |
| API reinicia em loop / erro de conexão ao banco | O Postgres não subiu, ou a senha difere entre `.env` e `postgres\.env`. Suba a stack do Postgres e confira as senhas. |
| `port 8000 is already allocated` | Algo já usa a porta 8000. Mude `APP_PORT` no `.env` e suba de novo. |
| `port 5432 is already allocated` | Já existe um Postgres na 5432. Mude `POSTGRES_PORT` em `postgres\.env`. |
| Build falha em `npm` na primeira vez | Rede instável ao baixar dependências. Rode o comando de novo. |

Para ver o erro exato:

```powershell
docker compose logs api
```

---

## Apêndice — rodar nativo (sem Docker), modo desenvolvedor

Só para quem vai **desenvolver**. Para apenas usar a app, prefira o Docker acima.

Pré-requisitos: **Python 3.13**, **[uv](https://docs.astral.sh/uv/)**, **Node 22**,
e um **PostgreSQL** acessível.

**Backend** (`sumi-api`):

```powershell
cd sumi-api
uv sync
Copy-Item .env.example .env      # edite DATABASE_URL, JWT_SECRET_KEY, OPENAI_API_KEY
$env:PYTHONPATH = "src"
uv run alembic upgrade head
uv run uvicorn prompt_clinica.main:app --reload
# API em http://localhost:8000
```

**Frontend** (`sumi-web`), em outro terminal:

```powershell
cd sumi-web
npm install
npm start
# App de dev em http://localhost:4200 (proxy para a API na 8000)
```

> No modo nativo o Angular roda separado na 4200. Em produção (Docker) o FastAPI
> serve a SPA já compilada na própria porta 8000.
