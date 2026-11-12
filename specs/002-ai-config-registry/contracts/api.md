# Contrato da API: `/admin/ai-configs`

Todas as rotas exigem administrador (`get_current_admin`). Os erros usam o formato atual da API
(`{"detail": "..."}`).

`{ai_type}` ∈ `text` | `image` | `transcription` | `voice` | `video`. Qualquer outro valor → 404.

## Tipos

```jsonc
// AIConfigOut
{
  "id": 3,
  "name": "BytePlus produção",
  "kind": "openai",
  "base_url": "https://ark.ap-southeast.bytepluses.com/api/v3",
  "model": "seed-1-6-250615",
  "language": "",          // só relevante em transcription; "" nos demais
  "key_hint": "…ab12",     // "" se sem chave; a chave nunca é retornada
  "active": true,
  "updated_at": "2026-11-12T14:00:00Z"
}

// AIConfigIn (criar)
{
  "name": "BytePlus produção",
  "kind": "openai",
  "base_url": "https://ark.ap-southeast.bytepluses.com/api/v3",
  "api_key": "…",
  "model": "seed-1-6-250615",
  "language": "",
  "active": false
}

// AIConfigUpdate (editar): igual ao AIConfigIn, mas "api_key": null mantém a atual
```

## Rotas

| Método | Rota | Corpo | Resposta | Erros |
|---|---|---|---|---|
| GET | `/admin/ai-configs/{ai_type}` | — | `AIConfigOut[]`, a ativa primeiro e depois por nome | 404 tipo inválido |
| POST | `/admin/ai-configs/{ai_type}` | `AIConfigIn` | `201 AIConfigOut` | 422 `kind`/URL inválidos |
| PUT | `/admin/ai-configs/{ai_type}/{id}` | `AIConfigUpdate` | `AIConfigOut` | 404, 422 |
| PATCH | `/admin/ai-configs/{ai_type}/{id}/active` | `{"active": true}` | `AIConfigOut[]`, a lista inteira, para o grid refletir a troca (FR-020) | 404 |
| DELETE | `/admin/ai-configs/{ai_type}/{id}` | — | `204` | 404; 409 se ativa |
| POST | `/admin/ai-configs/{ai_type}/{id}/test` | ver abaixo | ver abaixo | 404; 502 erro do fornecedor (`detail` com a mensagem dele) |

Com `active: true`, POST e PUT também desativam a anterior do mesmo tipo (FR-019).

## Teste por tipo

| `ai_type` | Corpo | Resposta 200 |
|---|---|---|
| `text` | — | `{"response": "ok", "model": "...", "elapsed_ms": 812}` |
| `image` | — | `{"image": "<url ou data-URI>", "model": "...", "elapsed_ms": 9400}` |
| `transcription` | `multipart/form-data` com `file` (áudio) | `{"text": "...", "model": "...", "elapsed_ms": 1300}` |
| `voice` | — | `{"audio": "data:audio/mpeg;base64,...", "model": "...", "elapsed_ms": 2100}` |
| `video` | — | `{"status": "ok", "model": "...", "elapsed_ms": 350}`, só a conexão (research R6) |

## Rotas removidas

- `GET/PUT /admin/app-settings`
- `POST /admin/app-settings/test-image`

## Rotas mantidas, com fonte adaptada

- `GET /health/ai`: provider e modelo da config de Texto ativa. Sem ativa:
  `{"status": "error", "detail": "Nenhuma IA de texto ativa."}`.
- `POST /speech/transcribe`, `POST /voice/...`, `POST /image-test`: mesmo contrato; usam a config
  ativa do tipo. Sem ativa → 400 com a mensagem do FR-011.

## Mensagem quando não há configuração ativa (FR-011)

`400 {"detail": "Nenhuma IA de <texto|imagem|transcrição|voz|vídeo> ativa. Configure em Configurações do sistema."}`
