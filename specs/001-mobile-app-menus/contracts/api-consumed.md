# Contrato: API consumida pelo app

O app **não expõe** API; ele consome a API FastAPI existente, acrescida apenas de `POST /auth/refresh`. Esta tabela é o
contrato que o app assume. Base URL via `--dart-define=API_BASE_URL=...`. Todas as rotas, exceto
`/auth/*` e `/storage/*`, exigem `Authorization: Bearer <access_token>`.

**Sucesso**: JSON direto (sem envelope). **Erro**: `{ "detail": "texto" }` ou, em 422,
`{ "detail": [ { "loc": [...], "msg": "..." } ] }`. **401** → logout e volta ao login.

## Por repositório (abstração no app → rotas)

### AuthRepository
| Método | Rota | Corpo / resposta |
|---|---|---|
| login | `POST /auth/login` | `{ email, password, remember: true }` → `{ access_token, token_type, user }` |
| refresh | `POST /auth/refresh` **(novo)** | sem corpo, `Authorization: Bearer` → `TokenResponse` com token novo de 30 dias |

> Única alteração no `sumi-api`: rota `POST /auth/refresh` em `routers/auth.py`, com
> `Depends(get_current_user)`, devolvendo `TokenResponse(access_token=create_access_token(<mesmo
> subject do login>, settings.jwt_remember_expire_minutes), user=...)`. Não afeta o web.

### ProjectsRepository
| Método | Rota |
|---|---|
| list | `GET /projects` |
| get | `GET /projects/{id}` |
| create | `POST /projects` (`ProjectCreate`) |
| update | `PATCH /projects/{id}` |
| delete | `DELETE /projects/{id}` |
| generateSynopsis | `POST /projects/{id}/synopsis/generate` *(síncrono, longo)* |
| setCharacters | `PUT /projects/{id}/characters` |
| setScenarios | `PUT /projects/{id}/scenarios` |
| exportPanelsZip | `GET /projects/{id}/export/panels` *(bytes)* |
| startVideo / videoJob | `POST /projects/{id}/export/video` → `GET /projects/{id}/export/video/{job_id}` *(polling)* |
| youtubeMetadata get/put/generate | `GET` / `PUT` / `POST …/youtube-metadata[/generate]` |

### PanelsRepository
| Método | Rota |
|---|---|
| list | `GET /projects/{id}/panels` |
| generateAll | `POST /projects/{id}/panels/generate` *(síncrono, longo)* |
| create | `POST /projects/{id}/panels` |
| generateImages | `POST /projects/{id}/panels/generate-images` *(síncrono, longo)* |
| reorder | `PUT /projects/{id}/panels/order` |
| deleteMany | `POST /projects/{id}/panels/delete` |
| update | `PATCH /panels/{panel_id}` (inclui `bubbles`) |
| delete | `DELETE /panels/{panel_id}` |
| generateImage | `POST /panels/{panel_id}/generate` |
| uploadImage | `POST /panels/{panel_id}/image` |
| generateBubbles | `POST /panels/{panel_id}/bubbles/generate` |

### CharactersRepository
| Método | Rota |
|---|---|
| list / create / update | `GET` / `POST /characters` · `PATCH /characters/{id}` |
| options | `GET /character-options` |
| startPortrait / portraitJob | `POST /characters/generate-portrait` → `GET /characters/portrait-job/{job_id}` *(polling)* |
| deleteUnused | `POST /characters/delete-unused` |

### ScenariosRepository
| Método | Rota |
|---|---|
| list / create / update | `GET` / `POST /scenarios` · `PATCH /scenarios/{id}` |
| options | `GET /scenario-options` |
| startScene / sceneJob | `POST /scenarios/generate-scene` → `GET /scenarios/scene-job/{job_id}` *(polling)* |
| deleteUnused | `POST /scenarios/delete-unused` |

### SeriesRepository
| Método | Rota |
|---|---|
| list / get / create / update / delete | `GET /series` · `GET/PATCH/DELETE /series/{id}` · `POST /series` |
| setProjects | `PUT /series/{id}/projects` |

### VoicesRepository
| Método | Rota |
|---|---|
| list / create / update / delete | `GET` / `POST /voice` · `PATCH` / `DELETE /voice/{id}` |
| test | `POST /voice/test` *(bytes de áudio)* |

### StylesRepository
| Método | Rota |
|---|---|
| list | `GET /styles` |

### Arquivos
| Uso | Rota |
|---|---|
| imagens, áudio, vídeo | `GET /storage/{key}` (público) |

## Dados estáticos copiados do web

Não vêm da API e precisam existir no app como constantes Dart (fonte da verdade continua no web):

| Web | App |
|---|---|
| `sumi-web/src/app/core/data/minimax-voices.ts` (catálogo de vozes) | `lib/features/voice_test/minimax_voices.dart` |
| `LAYOUTS` em `features/projects/editor/editor.component.ts` | `lib/features/production/editor/page_layouts.dart` |

## Fora do contrato (não usados pelo app)

`/admin/*`, `/settings*`, `/image-test`, `/public/*`, `/projects/{id}/backup`, `/projects/import`,
`/speech/transcribe`, `/health*`, `/auth/register`, `/auth/password-reset/request`.
