# Deploy no Railway — Guia passo a passo

## Visão geral

O Dockerfile faz um build multi-stage:
1. **Stage 1 (frontend)** — compila o Angular e gera `dist/sumi-web/browser/`
2. **Stage 2 (api)** — instala as dependências Python e copia o bundle Angular para `static/app/`

O FastAPI serve a SPA em produção; não há servidor separado para o frontend.

---

## 1. Criar o projeto no Railway

1. Acesse [railway.com](https://railway.com) → **New Project**
2. Escolha **Deploy from GitHub repo** e selecione `comic-prompt2`
3. O Railway detecta o `Dockerfile` automaticamente — **não altere** o build command

---

## 2. Adicionar o banco de dados PostgreSQL

1. No projeto, clique em **+ New** → **Database** → **PostgreSQL**
2. O Railway injeta `DATABASE_URL` automaticamente no serviço da API — **não precisa copiar manualmente**

---

## 3. Configurar variáveis de ambiente

No serviço da API: aba **Variables** → botão **Raw Editor** — cole sem aspas:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
JWT_SECRET_KEY=gere-com-python3-c-import-secrets-print-secrets.token_hex-32
OPENAI_API_KEY=sk-...
AI_PROVIDER=openai
AI_TEXT_MODEL=gpt-4o-mini
AI_IMAGE_MODEL=gpt-image-1
JWT_EXPIRE_MINUTES=60
APP_ENV=production
APP_RELOAD=false
```

> **Importante:** não use aspas em torno dos valores — o Railway interpreta aspas como parte do valor literal.
> `${{Postgres.DATABASE_URL}}` é a sintaxe de referência entre serviços do Railway.
> `PORT` é injetada automaticamente; o `CMD` do Dockerfile já usa `${PORT:-8000}`.

---

## 4. Rodar as migrations

As migrations **não rodam automaticamente** no build.

No serviço `comic-prompt2`: **Settings → Deploy → Add pre-deploy step**:

```sh
alembic upgrade head
```

Isso roda as migrations antes de subir o uvicorn a cada deploy, sem sobrescrever o start command do Dockerfile.

---

## 5. Configurar CORS (pós-deploy)

Após o primeiro deploy, o Railway atribui um domínio público (ex: `sumi-api-production.up.railway.app`).

Como a SPA é servida **pelo próprio FastAPI**, o CORS só importa para chamadas externas. Se não houver frontend externo, a variável pode ficar vazia. Caso contrário:

```env
CORS_ORIGINS=https://seudominio.com,https://outro.com
```

---

## 6. Persistência de imagens geradas

O `IMAGES_DIR` padrão é `static/images/` — **dentro do container**, portanto efêmero. A cada redeploy as imagens são perdidas.

### Opção A — Railway Volume (simples)

1. No serviço: **Settings → Volumes → Add Volume**
2. Mount path: `/app/static/images`
3. Adicione a variável: `IMAGES_DIR=/app/static/images`

### Opção B — Object Storage externo (escalável)

Use S3, Cloudflare R2 ou Google Cloud Storage e adapte o código de geração de imagens.

---

## 7. Checklist pré-deploy

- [ ] `DATABASE_URL` configurada (Railway PostgreSQL)
- [ ] `JWT_SECRET_KEY` definida (string segura)
- [ ] Pelo menos uma chave de IA configurada (`OPENAI_API_KEY` ou `GOOGLE_API_KEY`)
- [ ] Pre-deploy step com `alembic upgrade head` (Settings → Deploy)
- [ ] Volume montado em `/app/static/images` (se quiser persistir imagens)

---

## 8. Verificar o deploy

Após o deploy concluir:

```
GET https://<seu-dominio>.up.railway.app/docs   → Swagger da API
GET https://<seu-dominio>.up.railway.app/       → App Angular
```

Se o Swagger carregar e o Angular abrir, o deploy está completo.
