# Spec — Quadros animados no vídeo (image-to-video)

Status: proposta · 2026-09-26

## 1. Objetivo

Permitir que o vídeo final use **clipes animados gerados a partir das imagens dos quadros**,
sem alterar o fluxo atual (quadro estático + balões + narração TTS). A animação é opcional,
por quadro, e ativada por um check na tela de Vídeo.

## 2. Como funciona hoje

`services/video_service.render()` — por quadro, em ordem:

1. Sintetiza os beats (caption + balões) via `MinimaxVoiceClient` → `audio_NNN.mp3`.
2. `_compose_frame()` desenha um PNG 1920x1080: imagem do quadro recortada (cover) em `_panel_rect(aspect)` + balões.
3. `_panel_clip()` gera um clipe com a imagem estática durante a duração do áudio (ou `SILENT_DUR`).
4. `_concat_clips()` reencoda tudo em `videos/{project_id}/{guid}.mp4` e grava em `project.video_url`.

Disparo: `POST /projects/{id}/export/video` → job em memória (`_video_jobs`) → polling pelo front.

Já existe `ai/minimax/video.py::MinimaxVideoClient.generate(prompt, first_frame_image=...)`
(Hailuo, image-to-video), **mas nada no app o usa**.

## 3. Decisão principal: animar em etapa separada do render

A animação **não** roda dentro de `render()`. Ela é gerada antes, quadro a quadro, e fica salva:

- Gerar um clipe de IA leva minutos (H3 local) ou custa dinheiro (API Hailuo). Se isso ficasse
  dentro do render, qualquer ajuste de balão ou voz regeraria todos os clipes.
- Permite revisar cada clipe e refazer só o que ficou ruim.
- Se o processo cair no meio (o job fica em memória), o que já foi animado não se perde.

O render só **consome** o clipe salvo quando o check está marcado. Sem check, ou quadro sem
clipe → comportamento de hoje, idêntico.

## 4. Escopo

### 4.1 Banco

Migration Alembic: `panels.motion_url String(500) NULL`.

Invalidação: quando `panel.image_url` muda (regerar ou trocar a imagem), `motion_url` volta a
`NULL` e o arquivo antigo é apagado. O ponto de alteração fica em `panel_service` (onde a imagem é gravada).

### 4.2 Cliente de vídeo (IA)

`VIDEO_PROVIDER=minimax|comfyui` (env). Uma função devolve bytes do .mp4:

```python
def animate(image_png: bytes, prompt: str) -> bytes
```

- **minimax**: usa o `MinimaxVideoClient.generate` já existente, passando a imagem como
  data-URI base64 (o storage local não é público) e baixando o `download_url`.
- **comfyui (H3 local)**: workflow exportado pelo Paulo em formato *API* do ComfyUI, versionado em
  `sumi-api/workflows/h3_i2v.json`. O Sumi:
  1. envia a imagem por `POST /upload/image`;
  2. substitui no JSON o nome da imagem, o prompt e o seed (IDs dos nós configurados por env);
  3. `POST /prompt` → poll em `/history/{id}` → `GET /view` do arquivo de vídeo de saída.

  Mesmo padrão do `ComfyUIProvider.image()`, com timeout maior (ex.: 15 min).

Prompt de movimento: `panel.prompt` descreve a imagem, não o movimento. Na 1ª versão, usar
`framing + caption` + um sufixo fixo de movimento contido ("subtle motion, slow camera push-in,
consistent character"). Um campo de prompt de movimento editável fica fora do escopo inicial.

### 4.3 API

| Método | Rota | Função |
|---|---|---|
| POST | `/projects/{id}/panels/{pid}/animate` | Gera o clipe de um quadro (job assíncrono) |
| POST | `/projects/{id}/animate` | Anima em fila todos os quadros com imagem e sem `motion_url` |
| GET | `/projects/{id}/animate/{job_id}` | Progresso (mesmo formato do job de vídeo) |
| DELETE | `/projects/{id}/panels/{pid}/motion` | Descarta o clipe (volta ao estático) |

Os jobs seguem o padrão atual (`dict` em memória + `BackgroundTasks`). Como cada quadro grava
seu `motion_url` ao terminar, um job interrompido é retomado chamando `/animate` de novo.

`POST /export/video` passa a aceitar `{ "animated": bool }` (default `false`).

### 4.4 Render (`video_service`)

Quando `animated=true` e `panel.motion_url` existe, `_panel_clip` é trocado por uma variante com ffmpeg:

1. Fundo: o frame PNG de hoje **sem a imagem** (papel + moldura), e um PNG transparente só com os balões.
2. Clipe da IA: `scale`/`crop` (cover) para o tamanho de `_panel_rect(aspect)`, `fps=25`, **sem o áudio** (`-an`).
3. `overlay` do clipe no retângulo do quadro, depois `overlay` dos balões por cima.
4. Duração = duração da narração (como hoje):
   - clipe mais curto que o áudio → congela o último frame (`tpad=stop_mode=clone`);
   - clipe mais longo → corta (`-t dur`).

Para isso, `_compose_frame` ganha a separação fundo/balões. O caminho estático continua igual.

### 4.5 Front (tela Vídeo)

- Check **"Usar quadros animados"**, desabilitado se nenhum quadro tem clipe.
- Na lista de cenas: status por quadro (sem clipe / gerando / pronto), com botões **Animar** e **Refazer**
  e prévia do clipe.
- Botão **"Animar pendentes"**, com progresso.
- O check vai no body de `startVideoExport`.

## 5. Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `sumi-api/alembic/versions/…` | nova coluna `motion_url` |
| `sumi-api/models/panel.py` | campo `motion_url` |
| `sumi-api/src/prompt_clinica/ai/video.py` (novo) | `animate()` + escolha minimax/comfyui |
| `sumi-api/workflows/h3_i2v.json` (novo) | workflow do Paulo (fase 3) |
| `services/video_service.py` | clipe animado + separação fundo/balões + flag `animated` |
| `services/panel_service.py` | invalida `motion_url` ao trocar imagem; job de animação |
| `routers/projects.py` | rotas de animação + body do export |
| `schemas/panel.py` | expor `motion_url` |
| `services/backup_service.py` | decidir se inclui os clipes (ver riscos) |
| `sumi-web/.../video/video.component.ts` + `project.service.ts` + `panel.models.ts` | check, status, botões |

## 6. Fases

1. **Backend + MiniMax (Hailuo).** O cliente já existe e isso valida o fluxo ponta a ponta sem depender da máquina do Paulo.
2. **Front.** Check, status por quadro, animar e refazer.
3. **ComfyUI + H3 local.** Com o workflow exportado pelo Paulo.

## 7. Riscos

| # | Risco | Impacto | Mitigação |
|---|---|---|---|
| R1 | **Deriva do personagem**: rosto, roupa ou estilo mudam durante o clipe (comum em image-to-video, pior em quant int8 podado) | Alto — quebra a consistência que o projeto persegue | Clipes curtos (4–6s), prompt de movimento contido, revisão manual com Refazer, e o estático como fallback por quadro |
| R2 | **Balão desalinhado**: o personagem se move e a cauda do balão aponta para o vazio | Médio | Movimento contido (câmera > personagem); o usuário descarta o clipe do quadro |
| R3 | **Duração**: narração de 12s com clipe de 6s → metade do tempo congelada | Médio | Congelar o último frame (definido); depois, avaliar loop ping-pong ou clipe de 10s |
| R4 | **Tempo e GPU local**: H3 leva minutos por clipe; 20 quadros podem passar de 1h. A mesma GPU atende FLUX, LLM e TTS | Alto na máquina local | Animação separada do render, fila de um quadro por vez, progresso por quadro |
| R5 | **Custo na API Hailuo**: cada Refazer é cobrado | Médio | Animação por quadro (nunca automática no render), confirmação no "Animar pendentes" |
| R6 | **Job em memória**: reiniciar a API perde o progresso | Baixo | `motion_url` por quadro torna a operação retomável |
| R7 | **Workflow ComfyUI frágil**: IDs de nós, custom nodes e versões mudam; o nó de saída de vídeo varia (`SaveVideo`, `VHS_VideoCombine`) e a chave no `/history` também (`videos`/`gifs`/`images`) | Médio | IDs por env, validação na subida com erro claro, workflow versionado no repo |
| R8 | **Rede**: o Sumi roda no CasaOS e o ComfyUI na máquina do Paulo; precisa de acesso (tunnel/VPN) e aguentar uploads e downloads grandes | Médio | `COMFYUI_BASE_URL` separado para vídeo; timeouts longos; o poll já evita o limite de 100s do Cloudflare |
| R9 | **Proporção**: quadros 3-4 e 1-1 contra saída 16:9 do modelo → recorte perde parte da cena | Médio | Enviar a imagem já recortada na proporção do quadro; cover no render |
| R10 | **Imagem regerada com clipe antigo** | Médio | Invalidação em `panel_service` (4.1) |
| R11 | **Storage**: 5–20 MB por clipe; lixo ao apagar quadro ou refazer | Baixo | Apagar o arquivo antigo em refazer/descartar/excluir quadro; backup sem clipes na 1ª versão |
| R12 | **Licença**: H3 sob "MiniMax Community License"; a quant podada int8 é de terceiros, não oficial | Médio se o Sumi for monetizado | Ler a licença antes da fase 3; a fase 1 usa a API oficial |
| R13 | **Áudio nativo do H3** misturado à narração | Baixo | Descartar o áudio do clipe (`-an`) |

## 8. Decisões em aberto

1. Incluir os clipes no backup/export do projeto? (proposta: não, na 1ª versão)
2. Clipe curto com narração longa: congelar o último frame (proposto), fazer loop ou gerar clipe mais longo?
3. Alternativa sem IA: o "Zoom lento" (Ken Burns) já aparece em `TRANSITIONS` no front mas não existe no render. Com `zoompan` no ffmpeg, dá movimento a custo zero e sem risco de deriva. Vale como fase 0 ou como fallback?
4. Prompt de movimento editável por quadro: entra agora ou só depois de ver os resultados?
