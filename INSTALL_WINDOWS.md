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

## 3. Configurar o `.env`

A aplicação lê chaves e segredos de um arquivo `.env` (que **não** vai para o Git).
Há um modelo pronto:

```powershell
Copy-Item .env.production.example .env
notepad .env
```

Preencha no mínimo:

| Variável            | O que colocar                                                        |
|---------------------|----------------------------------------------------------------------|
| `POSTGRES_PASSWORD` | Uma senha forte para o banco.                                        |
| `JWT_SECRET_KEY`    | Uma string aleatória (veja abaixo como gerar).                       |
| `OPENAI_API_KEY`    | Sua chave da OpenAI (provider padrão). Ou configure outro provider.  |

Para gerar o `JWT_SECRET_KEY`, rode no PowerShell:

```powershell
-join ((1..64) | ForEach-Object { '{0:x}' -f (Get-Random -Max 16) })
```

Copie o resultado para a linha `JWT_SECRET_KEY=` no `.env`.

> O resto das variáveis tem valores padrão sensatos. Só preencha provedores de IA
> extras (Seedream, MiniMax) se for usá-los.

---

## 4. Instalar e subir

Com o Docker Desktop aberto, rode o script de instalação na raiz do projeto:

```powershell
.\install-windows.ps1
```

O script:
1. confere se o Docker está instalado e rodando;
2. cria o `.env` a partir do exemplo, se ainda não existir (e pede para você editar);
3. builda a imagem e sobe os containers;
4. roda as migrations do banco automaticamente.

> Se preferir fazer manualmente, o comando equivalente é:
> ```powershell
> docker compose up -d --build
> ```
> As migrations (`alembic upgrade head`) já rodam no start, definido no `docker-compose.yml`.

O **primeiro build demora** alguns minutos (baixa imagens, compila o Angular e
instala as dependências Python). Builds seguintes usam cache e são rápidos.

---

## 5. Acessar a aplicação

Quando os containers subirem:

- **App:** http://localhost:8000/
- **API (Swagger):** http://localhost:8000/docs

Crie um usuário pela tela de cadastro e comece a usar.

> Para mudar a porta, edite `APP_PORT` no `.env` (ex.: `APP_PORT=9000` → http://localhost:9000/).

---

## 6. Comandos do dia a dia

Todos rodados na raiz do projeto:

```powershell
docker compose ps              # ver status dos containers
docker compose logs -f api     # acompanhar os logs da API (Ctrl+C para sair)
docker compose stop            # parar (dados preservados)
docker compose start           # subir de novo
docker compose down            # remover containers (dados preservados nos volumes)
docker compose up -d --build   # atualizar após um git pull
```

**Persistência:** o banco e as imagens geradas ficam em *volumes* do Docker
(`pgdata` e `images`). Eles sobrevivem a `stop`/`down` e a rebuilds.
Só são apagados com:

```powershell
docker compose down -v         # ATENÇÃO: apaga banco + imagens geradas
```

---

## 7. Atualizar para uma versão nova

```powershell
git pull
docker compose up -d --build
```

As migrations novas rodam sozinhas no start.

---

## 8. Problemas comuns

| Sintoma | Causa / solução |
|---|---|
| `error during connect ... docker daemon` | Docker Desktop não está aberto. Abra-o e espere ficar verde. |
| `port 8000 is already allocated` | Algo já usa a porta 8000. Mude `APP_PORT` no `.env` e suba de novo. |
| API reinicia em loop nos logs | Faltou preencher `.env` (ex.: `JWT_SECRET_KEY` vazio). Edite e rode `docker compose up -d`. |
| Build falha em `npm` na primeira vez | Rede instável ao baixar dependências. Rode o comando de novo. |
| Imagens somem após reiniciar | Você usou `down -v`. Use só `down`/`stop` para preservar os volumes. |

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
