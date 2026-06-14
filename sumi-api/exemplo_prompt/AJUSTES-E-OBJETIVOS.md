# Ajustes e Objetivos — Estilos no banco + "Gerar por Atributos"

> Documento de execução. As decisões abaixo estão **fixadas** — implementar sem pedir confirmação.
> Complementa `SPEC-estilos-no-banco.md` (análise). Referências de prompt em `exemplo_prompt/<estilo>/README.md`.
>
> **Status: IMPLEMENTADO** (migration aplicada no banco local em 2026-06-14). Ver §9.

## 1. Objetivo

1. Mover os estilos visuais (incluindo o **prompt completo**) de `styles.py` para uma **tabela no banco** (`visual_styles`).
2. Cada estilo passa a ser um **prompt próprio com placeholders**, não mais um fragmento adjetival num template genérico.
3. Enxugar a tela **Gerar com IA / Por Atributos** para alimentar só os placeholders que importam.

## 2. Decisões fixadas (confirmadas pelo usuário)

- **Cabelo:** permanece **campo de texto livre** (sem dropdown).
- **Removidos da tela Por Atributos:** `archetype` (arquétipo), `outfit` (figurino), `personality` (personalidade), `quirk` (marca).
- **Novo campo:** um único **texto livre extra** ("Detalhes adicionais"). No envio à LLM ele entra **depois** do prompt montado pelo template do estilo.

## 3. Defaults assumidos para os pontos em aberto

Assumidos para não travar a execução. Para mudar, editar este arquivo antes de eu rodar.

- **`body_type` (tipo físico):** **removido** da tela Por Atributos. Retrato é close-up; corpo não aparece. Coluna `characters.body_type` permanece (cadastro manual).
- **`skin_tone` (cor da pele):** **removido** da tela Por Atributos. A etnia já carrega o tom; coluna permanece no banco.
- **`age` (idade):** vira **dropdown de faixa etária** (`age_range`: Criança / Adolescente / Jovem adulto / Adulto / Meia-idade / Idoso). Necessário porque `{faixa_etaria}` precisa de uma frase ("young adult"), não de um número.
- **`eyes` (olhos):** **removido** como campo próprio; detalhes de olhos vão no texto livre extra.
- **manga `{caracteristicas}` / `{expressao}`:** os templates deixam de expor esses placeholders. A descrição padrão de rosto/expressão fica **embutida no texto do estilo**; especificidades vêm pelo texto livre extra.
- **ComfyUI / Stable Diffusion:** **fora de escopo** nesta entrega. Mantém-se o caminho atual sem alteração; o prompt por estilo é só para o MiniMax. (Se um dia voltar, cada estilo precisará de variante em tags danbooru.)

## 4. Tela "Por Atributos" — layout final

Campos que ficam:
- `gender` (dropdown) → `{sexo}`
- `age_range` (dropdown, novo) → `{faixa_etaria}`
- `ethnicity` (dropdown) → `{etinia}`
- `cabelo` (texto livre) → `{cabelo}`
- **Detalhes adicionais** (texto livre, novo) → anexado **após** o prompt

Cor: segue vindo de `color_mode` do projeto → `{paleta_cor}` (wording por estilo, §6).

Campos removidos da tela: `body_type`, `skin_tone`, `eyes`, `archetype`, `outfit`, `personality`, `quirk`.

## 5. Tabela `visual_styles`

| Coluna            | Tipo          | Notas |
| ----------------- | ------------- | ----- |
| `id`              | `String` PK   | `manga-pb`, `anime-90s`, `dark-fantasy` |
| `label`           | `String`      | rótulo PT |
| `note`            | `String`      | descrição curta |
| `prompt_template` | `Text`        | prompt completo com `{placeholders}` |
| `color_wording`   | `JSONB`       | `color_mode → texto de {paleta_cor}`; `{}` se monocromático |
| `aspect_ratio`    | `String`      | default `1:1` |
| `resolution`      | `String`      | default `2K` |
| `enabled`         | `Boolean`     | default `true` |
| `sort_order`      | `Integer`     | ordem na tela |
| `created_at` / `updated_at` | `DateTime` | |

- Placeholders válidos (conjunto fixo): `{sexo}`, `{faixa_etaria}`, `{etinia}`, `{cabelo}`, `{paleta_cor}`. O render preenche só os presentes no template.
- Seed inicial: 3 estilos a partir dos READMEs em `exemplo_prompt/` (`manga_pb`, `anime_retro_90`, `dark_fantasy_semi_realista`).
- `_LEGACY_ALIASES` (`classic-shoujo`→`anime-90s`, `modern-line`→`webtoon`, `ink-heavy`→`dark-fantasy`): preservar a resolução de ids antigos gravados em personagens/projetos.
- Modelo SQLAlchemy em `models/visual_style.py` + import em `all_models.py` + migration Alembic + seed.

## 6. Montagem do prompt (MiniMax)

```
prompt_final = prompt_template.format_map(slots) + (", " + detalhes_extra  se houver)
```
- `slots`: `{sexo}`, `{faixa_etaria}`, `{etinia}`, `{cabelo}` dos atributos selecionados; `{paleta_cor}` resolvido por `color_wording[color_mode]`.
- `manga-pb` ignora `{paleta_cor}` (template já monocromático).
- Mapa de cor padrão (ajustável por estilo no `color_wording`):
  | color_mode   | `{paleta_cor}` |
  | ------------ | -------------- |
  | `colorido`   | `Warm color palette` |
  | `tons-cinza` | `Black and white monochrome` |
  | `p-e-b`      | `high contrast black and white ink, no gray tones` |
- Enviar `aspect_ratio` e `resolution` ao `image-01`. **Verificar na implementação** se `image-01` aceita `resolution`/`2K`; se não, mapear para `width`/`height` equivalente. Não bloquear: se não suportar, manter só `aspect_ratio` e registrar no doc.

## 7. Passos de execução

1. **Modelo + migration**: `models/visual_style.py`, registrar em `all_models.py`, migration Alembic, seed dos 3 estilos.
2. **Backend `styles.py`**: passar a ler da tabela (cache em memória); manter `resolve`/aliases. `prompt_fragment`/`render` substituídos por render de template.
3. **`character_service.build_portrait_prompt`**: usar `prompt_template` do estilo + slots + texto livre extra ao final. Caminho ComfyUI inalterado.
4. **`GET /styles`**: ler da tabela.
5. **Schema/Router**: `PortraitRequest` ganha campo `extra` (texto livre); `age_range` passa a ser enviado.
6. **Frontend `characters-screen`**: remover campos (§4), adicionar dropdown `age_range` e campo "Detalhes adicionais"; enviar os novos campos.
7. **Provider**: enviar `aspect_ratio`/`resolution` (conforme §6).
8. **Limpeza**: remover `portrait_debug.log` e logs/prints temporários de depuração.

## 8. Fora de escopo

- Caminho ComfyUI / Stable Diffusion (tags danbooru).
- Dropar colunas `body_type` / `skin_tone` de `characters` (permanecem).
- Editor de estilos na UI (a tabela é populada via seed/migration por enquanto).

## 9. Status de execução (2026-06-14)

Feito:
- `models/visual_style.py` (tabela `visual_styles`) + registro em `all_models.py`.
- Migration `c9d0e1f2a3b4_add_visual_styles_table.py` com seed dos **3 estilos** dos
  prompts de referência (`manga-pb`, `anime-90s`, `dark-fantasy`). **Aplicada no banco local** (head atual).
  Default = `anime-90s`. O antigo `webtoon` foi removido do catálogo.
- Migration `d0e1f2a3b4c5_migrate_legacy_style_ids.py`: reescreve os ids antigos
  nos dados (`classic-shoujo`/`modern-line`/`webtoon` → `anime-90s`, `ink-heavy` →
  `dark-fantasy`) e troca o `server_default` de `characters.style`/`projects.style`
  para `anime-90s`. Os **aliases foram removidos do código** (`_LEGACY_ALIASES = {}`);
  o banco fica só com os 3 ids reais. **Aplicada no banco local.**
- `styles.py`: lê da tabela com cache em memória (`all_styles`/`reload_cache`),
  `render_prompt` por template + slots, `resolve`/aliases preservados,
  validadores `StyleId`/`ColorModeId`. `COLOR_MODES` continua em código (rótulos).
- `character_service.py`: `build_portrait_prompt`/`build_portrait_prompts`/`generate_portrait`
  usam o template do estilo + slots (`_SEXO`/`_FAIXA`/`_ETNIA`) + texto livre ao final.
  Removidos `body_type`/`skin_tone` do fluxo MiniMax. `print`/`portrait_debug.log` removidos.
- `schemas/character.py` `PortraitRequest`: campos `age_range`, `hair`, `extra`; `prompt` só p/ raw.
- `routers/characters.py` e `routers/styles.py` adaptados.
- Frontend: `character.service.generatePortrait` recebe objeto; `characters-screen`
  (TS+HTML) com Gênero/Faixa etária/Etnia/Cabelo + "Detalhes adicionais"; removidos
  tipo físico, cor da pele, arquétipo, idade(número), olhos, figurino, personalidade, quirk.
- Verificado: backend importa, `ng build` passa, render dos 4 estilos OK no banco.

Deferido (com motivo):
- **`resolution: 2K` no provider:** não enviado. O `image-01` recebe só `aspect_ratio`
  (default `1:1`, que é o de todos os estilos). Falta confirmar se o `image-01` aceita
  `resolution`/`width`/`height` antes de adicionar — não bloqueia a geração atual.
- **Painéis (comic):** continuam com descritor de estilo próprio em
  `styles.prompt_fragment` (`_PANEL_STYLE`/`_PANEL_COLOR`), fora da tabela. Funciona,
  mas é um segundo lugar com texto de estilo — candidato a unificar no futuro.
- **ComfyUI/Stable Diffusion:** caminho degradado (sem fragmentos de estilo por estilo);
  só relevante se `AI_PROVIDER=comfyui`. MiniMax (ativo) não é afetado.
