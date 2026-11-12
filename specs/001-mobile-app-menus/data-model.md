# Data Model: Aplicativo móvel Sumi

O app não tem banco próprio: os modelos espelham os schemas de resposta da API
(`sumi-api/src/prompt_clinica/schemas/`). Campos listados são os que o app usa; nomes em
`snake_case` como no JSON, convertidos para `camelCase` no Dart via `fromJson`.

## AppUser (`schemas/auth.py::UserOut`)

| Campo | Tipo | Notas |
|---|---|---|
| id | string (uuid) | |
| name | string | |
| email | string? | |
| plan | string | exibido no menu |
| group | string | não usado para navegação: o app não tem telas de admin |
| approved | bool | conta pendente de aprovação não consegue logar (erro da API vira toast) |

Persistido no secure storage junto com `access_token` (R4).

## Project (`ProjectOut` / `ProjectDetailOut`)

| Campo | Tipo | Notas |
|---|---|---|
| id | uuid | |
| title, subtitle | string | |
| genre, tone, style, color_mode | string | |
| status | string | filtro de status no Início/Projetos |
| pages | int | 1–20 |
| cover_accent, cover_tone | string | cor e padrão da capa |
| narrator_voice_id | uuid? | |
| video_url | string? | presente quando o vídeo foi gerado |
| updated_at | datetime | |
| premise, synopsis | string? | só no detalhe |
| characters, scenarios | lista | só no detalhe |

**Criação** (`ProjectCreate`): title, premise, genre, tone obrigatórios; pages 1–20 (padrão 4).

## ProductionStep (derivado no app — R6)

Enum: `idea, characters, scenarios, script, review, editor, finalize, video`.

Regra: **só se pula para uma etapa se todas as anteriores já foram feitas**. Uma etapa conta
como feita pela evidência abaixo; a etapa de abertura é a seguinte à última feita (avaliando de
baixo para cima, a primeira condição verdadeira vence):

```text
video_url != null                                  → video
quadros existem e todos têm image_url              → editor     (Revisão feita)
quadros existem                                    → review     (Roteiro feito)
projeto tem cenários                               → script     (Cenários feita)
projeto tem personagens                            → scenarios  (Personagens feita)
projeto existe                                     → characters (Ideia feita)
sem projeto                                        → idea
```

O projeto é criado no servidor ao concluir a Ideia (como no web). Etapas concluídas = todas antes
da etapa de abertura; na barra de etapas só elas e a atual são tocáveis — não se avança para uma
etapa futura sem passar pela anterior. Editor e Finalizar não têm evidência própria nos dados:
voltar a eles é sempre permitido depois da Revisão.

## Panel (`PanelOut`)

| Campo | Tipo | Notas |
|---|---|---|
| id, project_id | string | |
| index_order | int | ordem; alterável via `PUT /projects/{id}/panels/order` |
| label, caption, framing, prompt | string | |
| aspect | string | ex.: `4-3` |
| tone | string | |
| character_name | string? | |
| status | string | `pending`, ... |
| image_url | string? | |
| bubbles | lista de Bubble | |

## Bubble

| Campo | Tipo | Notas |
|---|---|---|
| kind | enum | `say`, `thought`, `shout`, `whisper`, `narration` (padrão `say`) |
| text | string | |
| side | enum | `left`, `right` |
| tail | enum | `none`, `left`, `right` |
| x, y | int | posição em % do quadro (0–100); padrão 8 / 12 |

Salvo via `PATCH /panels/{id}` com a lista completa de `bubbles`.

## Character (`CharacterOut` / `CharacterCreate`)

| Campo | Tipo | Notas |
|---|---|---|
| id | uuid | |
| name, role | string | `role` é o filtro da Biblioteca |
| gender, body_type, skin_tone, ethnicity, outfit | string? | |
| age | int? | |
| height, summary | string? | |
| traits | lista de string | |
| image_url | string? | retrato |
| approved | bool | `false` = RASCUNHO |

## PortraitJob / SceneJob / VideoJob

| Campo | Tipo | Notas |
|---|---|---|
| job_id | string | |
| status | `pending` \| `running` \| `done` \| `error` | polling até `done`/`error` |
| portraits / scene / video_url | conforme o job | resultado |
| progress | int | só VideoJob, 0–100 |
| detail | string | mensagem de erro |

## Scenario (`ScenarioOut`)

| Campo | Tipo | Notas |
|---|---|---|
| id | uuid | |
| name, kind, style | string | |
| summary, location_type, time_of_day, weather, atmosphere, details | string? | |
| approved | bool | |
| image_url | string? | gerada por job (`scene-job`) |

## Series (`SeriesOut`)

| Campo | Tipo | Notas |
|---|---|---|
| id | uuid | |
| name | string | obrigatório |
| description | string? | |
| project_ids | lista de uuid | atualizado por `PUT /series/{id}/projects` |
| updated_at | datetime | |

## Voice (`VoiceOut`)

| Campo | Tipo | Notas |
|---|---|---|
| id | uuid | |
| name | string | ex.: "Menina alegre" |
| voice_id | string | id da voz no catálogo |
| age_start, age_end | int? | faixa etária |
| sex | string? | |
| details | string? | descrição livre |

`POST /voice/test` devolve o áudio em bytes (não JSON).
