# Análise do pipeline e atuação da IA

> Mapeamento das telas do fluxo de criação, onde a IA atua hoje e como o texto
> narrado do Vídeo é montado. Base para decidir melhorias (notadamente a
> diferença entre premissa crua e conteúdo trabalhado por IA).

## Fluxo geral

```
Ideia → Personagens → Roteiro → Revisão → Editor → Finalizar → Vídeo
```

## Objetivo de cada tela

### Roteiro (`script`) — visão macro do storyboard
- "Etapa 3 de 5". Ao entrar, se o projeto ainda não tem quadros, dispara
  `generate()` automaticamente (`script.component.ts:43`).
- Mostra um grid de quadros (label, imagem, caption, status `REVISAR`/`OK`) e o
  card **"SINOPSE PROPOSTA"**.
- Ações: **Regerar tudo** e **Gerar todas as imagens**.
- ⚠️ A "sinopse" exibida é o `project.premise` cru (`script.component.html:37`).
  Não existe sinopse trabalhada por IA — é o mesmo texto da tela Ideia.

### Revisão (`review`) — refino fino, quadro a quadro
- Navega um quadro por vez. Edita `caption`, `framing` e os balões (texto, tipo,
  posição via drag); insere/apaga/reordena quadros (`review.component.ts:91-232`).
- **Regenera imagem** e **regenera balões** por quadro (ambos via IA).
- Salva alterações com debounce.

### Editor (`editor`) — diagramação de página (mise en page)
- **Não usa IA.**
- Escolhe layout de página (`manga-vertical` etc.), direção de leitura,
  paginação, e permite arrastar balões para posicioná-los na página.
- Monta os quadros aprovados em páginas.

### Finalizar (`final`) — preview e entrada de export
- Preview estático das páginas montadas + contagem de aprovados + navegação.
- **Sem narração e sem IA.**

### Vídeo (`video`) — player de motion comic
- Reproduz os quadros como motion comic com narração TTS do navegador.
- Modal de metadados YouTube (gerado por IA) e export ZIP.

## Onde a IA atua hoje (além de personagens/retratos)

São **4 pontos**, todos via OpenAI — texto em GPT (`gpt-4o-mini` pela docstring)
e imagem em `gpt-image-1`:

| # | Onde | Função | Entrada → Saída |
|---|------|--------|-----------------|
| 1 | Roteiro (regerar tudo) | `generate_roteiro` (`ai/roteiro.py`) | premise, gênero, tom, páginas, personagens → `title` criativo + `panels[]` (label, aspect, tone, character_name, **caption** = direção de cena PT, framing, **prompt** EN p/ imagem, **bubbles**) |
| 2 | Revisão (regerar balões) | `generate_bubbles` (`services/panel_service.py:302`) | label, framing, personagem, caption do quadro → array de balões |
| 3 | Roteiro/Revisão (gerar imagem) | `generate_image` / `generate_all_images` (`services/panel_service.py:194,361`) | `panel.prompt`/`caption` → PNG via `gpt-image-1`, salvo no storage |
| 4 | Vídeo (modal YouTube) | `generate_youtube_metadata` (`ai/youtube_metadata.py`) | título, premise, gênero, personagens, cenas → título/descrição/tags YouTube |

Detalhe: no `generate_roteiro` a IA devolve um `title` criativo que **é** salvo
em `project.title` (`panel_service.py:175-177`). Mas **não há geração de
sinopse** — por isso a tela Roteiro só consegue exibir a premissa crua.

## Texto narrado em Finalizar e Vídeo

### Finalizar
Não tem narração. Apenas preview de páginas + contagem de aprovados. Nenhum
texto falado, nenhuma IA.

### Vídeo — a narração é montada no cliente, sem IA
A função `buildBeats()` (`video.component.ts:62`) percorre os quadros e, para
cada um, cria "beats":
- um beat de **narração** com `text = panel.caption` e locutor **"Narrador"**;
- um beat para **cada balão** (`panel.bubbles`), com o personagem como locutor.

A duração de cada beat é estimada por contagem de palavras. A "voz" é **TTS do
navegador** (`SpeechSynthesisUtterance`, `lang=pt-BR`), com `pitch`/`rate`
ajustados conforme a voz escolhida na UI (`video.component.ts:198-228`).
**Não há geração de áudio por IA nem TTS de servidor** — é a Web Speech API.

### De onde vem o texto narrado (o usuário nunca digitou)

```
Ideia (você digita só a premissa)
   │
   ▼
Roteiro → generate_roteiro (IA) gera, por quadro:
   • caption  → direção de cena em PT
   • bubbles  → diálogos
   │  (persistidos em panels.caption / panels.bubbles_json)
   ▼
Vídeo → buildBeats() recicla, sem nova chamada:
   • caption  → fala do "Narrador"
   • bubbles  → fala do personagem
   ▼
TTS do navegador lê em voz alta
```

⚠️ **Ponto de atenção:** o `caption` foi gerado como **instrução técnica de
enquadramento/cena** ("Plano geral de abertura. Ambiente estabelecido."), não
como texto pensado para ser narrado. Hoje o vídeo "lê" a direção de cena em voz
alta. **A narração não existe como conceito próprio** — o vídeo apenas recicla a
direção de cena. Se a intenção é um motion comic narrável, é provável que se
precise de um texto de narração dedicado (gerado por IA), distinto do `caption`.

## Pontos em aberto (decisões de produto)

1. **Sinopse da tela Roteiro:** hoje = `premise` cru. Avaliar campo `synopsis`
   trabalhado por IA, distinto da premissa da Ideia.
2. **Narração do Vídeo:** hoje = `caption` (direção técnica). Avaliar um texto de
   narração próprio por quadro, separado da direção de cena.
