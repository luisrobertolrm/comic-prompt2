# SPEC — Estilos no banco + "Gerar por Atributos" baseado em prompt por estilo

> Documento de trabalho para coordenar entre sessões do Claude. Estado: **proposta, aguardando decisões** (ver §7).
> Referências: prompts de exemplo em `sumi-api/exemplo_prompt/<estilo>/README.md`.

## 1. Objetivo

Hoje a geração de retrato monta **um template genérico** e injeta o estilo como um fragmento adjetival (`styles.py`). Os prompts de exemplo (manga_pb, anime_retro_90, dark_fantasy_semi_realista) mostram um modelo diferente: **cada estilo é um prompt completo e próprio**, com placeholders nomeados.

Queremos:
1. Migrar os estilos (incluindo o **prompt completo**) de `styles.py` para uma **tabela no banco**.
2. Ajustar a tela **Gerar com IA / Por atributos** para alimentar os placeholders desses prompts.
3. Decidir quais campos da tela permanecem, quais saem e quais viram estruturados.

## 2. Como funciona hoje (baseline)

### Backend
- `styles.py` — dict Python `STYLES` (3 estilos: `webtoon`, `dark-fantasy`, `anime-90s`). Cada um tem `description` com slot `{color}`. Cor entra via `colors` (3 modos: `colorido`, `tons-cinza`, `p-e-b`).
- `character_options.py` — catálogo `GROUPS` de atributos (gender, age_range, body_type, skin_tone, ethnicity, archetype, hair_color, hair_style, eye_color, outfit, accessories, personality). **Só `ethnicity` é consumido pela tela hoje.**
- `character_service.build_portrait_prompt()` monta (caminho MiniMax):
  ```
  {sujeito p/ gender}, cartoon-style '{description com {color}}', {body},{skin},{ethnicity},{texto livre}, character portrait, no text, no speech bubbles.
  ```
- `GET /styles` serve o catálogo a partir de `styles.py`.
- Geração via MiniMax `image-01`, `prompt_optimizer=false`, `aspect_ratio=1:1`. **`resolution` não é enviado hoje.**

### Frontend (`characters-screen.component.ts`, modo `attrs`)
- Dropdowns estruturados: `gender`, `body_type`, `skin_tone`, `ethnicity`.
- Campos livres `aiAttrs`: `archetype`, `age`, `hair`, `eyes`, `outfit`, `personality`, `quirk` → concatenados em texto e jogados no prompt.

## 3. O que os prompts de exemplo pedem

| Placeholder       | Significado          | manga_pb | anime_90 | dark_fantasy |
| ----------------- | -------------------- | :------: | :------: | :----------: |
| `{sexo}`          | gênero               |    ✓     |    ✓     |      ✓       |
| `{faixa_etaria}`  | faixa etária         |    ✓     |    ✓     |      ✓       |
| `{etinia}`        | etnia                |    ✓     |    ✓     |      ✓       |
| `{cabelo}`        | cabelo (cor+estilo)  |    ✓     |    ✓     |      ✓       |
| `{caracteristicas}` | traços do rosto    |    ✓     |    —     |      —       |
| `{expressao}`     | expressão            |    ✓     |    —     |      —       |
| `{paleta_cor}`    | paleta de cor        |    —*    |    ✓     |      ✓       |

\* manga_pb é monocromático por definição (não tem slot de cor).
Parâmetros fixos de todos: `aspect_ratio: 1:1`, `resolution: 2K`.

**Observação-chave:** olhos, iluminação e composição já vêm **embutidos** no texto de cada estilo (ex.: "Large expressive anime eyes"). Os placeholders variam por estilo — manga expõe `caracteristicas`/`expressao`; os outros não.

## 4. De/Para: campos da tela × placeholders

| Campo da tela hoje | Tipo hoje        | Vira placeholder?         | Recomendação |
| ------------------ | ---------------- | ------------------------- | ------------ |
| `gender`           | dropdown         | `{sexo}`                  | **Mantém** |
| `ethnicity`        | dropdown         | `{etinia}`                | **Mantém** |
| `age` (aiAttrs)    | texto livre (nº) | `{faixa_etaria}`          | **Vira dropdown** `age_range` (catálogo já existe) |
| `hair` (aiAttrs)   | texto livre      | `{cabelo}`                | Dropdown `hair_color`+`hair_style` **ou** manter livre (decisão §7) |
| `eyes` (aiAttrs)   | texto livre      | parte de `{caracteristicas}` | Manga: alimenta caracteristicas. Outros: **redundante** (olhos já no template) |
| `personality`      | texto livre      | `{expressao}`             | Manga: alimenta expressao; mapear de `personality` |
| `color_mode` (projeto) | dropdown 3 modos | `{paleta_cor}`        | Mapear p/ wording por estilo (§5) |
| `body_type`        | dropdown         | — (nenhum)                | **Sai da tela** — retrato close-up não mostra corpo |
| `skin_tone`        | dropdown         | — (etnia/`smooth skin`)   | Opcional: dobrar em `caracteristicas` ou **sair** (§7) |
| `archetype`        | texto livre      | — (narrativo)             | **Sai** do prompt (pode seguir como metadado do personagem) |
| `outfit`           | texto livre      | — (só gola aparece)       | **Sai** da tela de retrato |
| `quirk`            | texto livre      | — (narrativo)             | **Sai** do prompt |

### Impacto de remover campos
- **Não exige dropar colunas** `body_type`/`skin_tone` de `characters` — elas continuam no cadastro manual; só deixam de influenciar a geração destes estilos close-up.
- Hoje há tratamento elaborado de `skin_tone` no caminho **ComfyUI/Stable Diffusion** (`_SD_SKIN`, negativos). Se `skin_tone` sair da geração, esse caminho perde a informação. Decidir se o caminho SD continua relevante (§7).
- `archetype`/`quirk`/`outfit`/`eyes` removidos do prompt = retratos mais consistentes com o estilo (menos ruído), ao custo de menos personalização fina.

## 5. Cor: 3 modos hoje → wording por estilo

A app tem 3 modos (`colorido`, `tons-cinza`, `p-e-b`); os exemplos só citam 2 wordings (`Warm color palette`, `Black and white monochrome`). O wording **depende do estilo** (já é assim em `styles.py`). Mapa proposto (ajustável por estilo na tabela):

| color_mode   | `{paleta_cor}` (exemplo)      |
| ------------ | ----------------------------- |
| `colorido`   | `Warm color palette`          |
| `tons-cinza` | `Black and white monochrome`  |
| `p-e-b`      | `high contrast black and white ink, no gray tones` |

`manga_pb` ignora `{paleta_cor}` (template já é monocromático).

## 6. Modelo de dados proposto

### Tabela `visual_styles`
| Coluna            | Tipo         | Notas |
| ----------------- | ------------ | ----- |
| `id`              | `String` PK  | ex.: `manga-pb`, `anime-90s`, `dark-fantasy` |
| `label`           | `String`     | rótulo PT exibido |
| `note`            | `String`     | descrição curta |
| `prompt_template` | `Text`       | prompt completo com `{placeholders}` |
| `color_wording`   | `JSONB`      | mapa `color_mode → texto de {paleta_cor}`; `{}` se monocromático |
| `aspect_ratio`    | `String`     | default `1:1` |
| `resolution`      | `String`     | default `2K` (ver §7 — suporte do provider) |
| `enabled`         | `Boolean`    | |
| `sort_order`      | `Integer`    | ordem na tela |
| `created_at`/`updated_at` | `DateTime` | |

- Os placeholders são um **conjunto fixo conhecido** (`sexo`, `faixa_etaria`, `etinia`, `cabelo`, `caracteristicas`, `expressao`, `paleta_cor`). O render preenche os que existirem no template e ignora o resto — assim cada estilo usa só os seus.
- `_LEGACY_ALIASES` de `styles.py` (`classic-shoujo`→`anime-90s` etc.) precisa de tratamento na migração de dados (personagens/projetos já gravados).
- Modelo SQLAlchemy em `models/` + import em `all_models.py` + migration Alembic + seed dos 3 estilos a partir dos READMEs de exemplo.

### Render no backend
- Substituir `styles.STYLES`/`resolve`/`render` por leitura da tabela (com cache em memória).
- Novo montador: `prompt_template.format_map(slots)` onde `slots` vem dos atributos do personagem. Substitui o template genérico de `build_portrait_prompt` para estes estilos.
- `GET /styles` passa a ler da tabela.

## 7. Decisões em aberto (precisam do usuário)

1. **Cabelo**: dropdowns estruturados (`hair_color`+`hair_style`) ou manter campo de texto livre?
2. **body_type / skin_tone / archetype / outfit / quirk**: confirmar remoção da tela "Por atributos". Manter algum?
3. **caracteristicas/expressao (manga)**: expor campos extras só quando o estilo é manga, ou ter sempre os campos e deixar vazios nos outros?
4. **Caminho ComfyUI/Stable Diffusion**: ainda é alvo? Se sim, o prompt por estilo precisa de variante em tags danbooru, não só a frase MiniMax.
5. **resolution `2K`**: confirmar se `image-01` (MiniMax) aceita; hoje só mandamos `aspect_ratio`. Pode exigir mapear para `width/height`.

## 8. Plano de implementação (após decisões)

1. Modelo `VisualStyle` + migration + seed dos 3 estilos.
2. `styles.py` passa a ler da tabela (cache); mantém `resolve`/aliases.
3. Backend: novo render por template; `build_portrait_prompt` usa o template do estilo.
4. `GET /styles` da tabela; expor placeholders/slots que cada estilo usa.
5. Frontend: reduzir/estruturar campos do "Por atributos" conforme §4/§7.
6. Enviar `resolution` ao provider (se §7.5 confirmar suporte).
7. Limpar `portrait_debug.log` e logs temporários.
