# Evals — harness LLM-as-judge

Testes de avaliação disparados **manualmente pelo dev** (nunca no `pytest`/CI, para não
queimar token). Medem se o roteiro gerado respeita a **ambientação** e os **personagens** do
briefing — é a ferramenta que comprova, com número, se a ambientação melhorou.

## Estágios

- **`roteiro`** (texto, barato) — gera o roteiro com o gerador real do produto
  (`generate_roteiro`, OpenAI) e um juiz LLM nota o JSON contra o briefing.
- **`image`** (visão, caro) — para cada caso define o prompt base: o `image_prompt` do caso
  (prompt específico, **isola o `gpt-image-1`** do roteiro) ou, na ausência, o quadro de
  estabelecimento do roteiro gerado. Gera **N imagens** (`--samples`, padrão 3) com
  `gpt-image-1` e o juiz de visão (`qwen2.5vl:7b`) avalia cada uma. O caso passa por **maioria
  estrita** das amostras; o relatório mostra a **taxa** (ex.: 2/3). PNGs em
  `evals/reports/images/` (`<caso>_<k>.png`).
- **`portrait`** (visão, caro) — testa a aderência do retrato de personagem aos atributos
  dos dropdowns (estilo visual, tipo físico, cor da pele). Usa o **`build_portrait_prompt`
  real do produto** (mesmo prompt que a tela "Gerar com IA" monta) e o provider de imagem
  real. O juiz de visão dá nota por eixo (estilo/corpo/pele); o caso passa por **maioria
  estrita** das amostras, exigindo cada eixo especificado ≥ 3 e nenhuma violação visível.
  Casos em `portrait_cases.json`; PNGs em `evals/reports/portraits/`.
- **`calib`** (visão, barato) — roda o juiz de visão sobre PNGs versionados em
  `evals/fixtures/`, cada um com veredito esperado, e mede a **taxa de acerto do juiz**. Não
  chama `gpt-image-1` e **não precisa de `.env`** no modo local. É o "teste do teste".

## Juiz local vs. remoto

O juiz roda **local** por padrão (Ollama, grátis); `--judge remote` usa gpt-4o como aferição.
O Ollama expõe API compatível com OpenAI, então só muda `base_url`/`model`/`api_key`.

| Modo | base_url | modelo texto | modelo visão |
|---|---|---|---|
| `local` (padrão) | `http://localhost:11434/v1` | `qwen2.5:14b` | `qwen2.5vl:7b` |
| `remote` | OpenAI | `gpt-4o` | `gpt-4o` |

## Como rodar

```bash
cd sumi-api
uv run python scripts/eval_run.py                      # estágio roteiro, juiz local
uv run python scripts/eval_run.py --stage image        # gera N imagens + juiz de visão
uv run python scripts/eval_run.py --stage image --samples 2
uv run python scripts/eval_run.py --stage portrait     # aderência estilo/corpo/pele do retrato
uv run python scripts/eval_run.py --stage calib        # calibra o juiz (sem .env)
uv run python scripts/eval_run.py --judge remote       # juiz gpt-4o
```

Pré-requisitos:
- **Gerador (SUT), estágios `roteiro`/`image`:** precisa de `DATABASE_URL`, `JWT_SECRET_KEY` e
  `OPENAI_API_KEY` no `.env` (o gerador é a parte do produto sob teste).
- **Juiz local:** `ollama serve` rodando com `qwen2.5:14b` e `qwen2.5vl:7b` baixados.
- **`calib` local** não precisa de `.env` (só do juiz local).

## Arquivos

- `cases.json` — casos (premissa + atributos esperados + anacronismos proibidos +
  `image_prompt` opcional para isolar o gerador de imagem).
- `portrait_cases.json` — casos do estágio `portrait`: valores dos dropdowns (style,
  gender, body_type, skin_tone, color_mode) + expectativas por eixo (estilo/corpo/pele).
- `judge.py` — juiz desacoplado (só importa `openai`; testável contra o Ollama sem subir o app).
- `fixtures/` — imagens versionadas + `fixtures.json` (veredito esperado) para o estágio
  `calib`. Positivo: `ukiyo-e-samurai.jpg` (The Met Open Access, CC0 — objeto 843990, gravura
  nishiki-e, ~1820s). Negativo: `modern-ui.png` (screenshot do próprio app).
- `../scripts/eval_run.py` — CLI orquestrador.
- `reports/` — relatórios `.md` + `images/` gerados por execução (não versionados).

## Critério de aprovação

`passed = ambientacao_score ≥ 3 E (personagens_score ≥ 3 OU briefing não espera personagem)
E sem anacronismos`. O limiar é determinístico (calculado no código); o juiz fornece scores +
lista de anacronismos + justificativa. O eixo de personagens **só conta quando o briefing
espera personagem** (planos de estabelecimento sem personagem não são penalizados por isso).
No estágio de imagem (P&B, sem texto), o juiz só penaliza etnia/idade se claramente perceptível.

## Notas sobre o juiz local

O `qwen2.5vl:7b` mostrou dois vieses que o system prompt do juiz já corrige:
- **Eco da lista de proibidos** — repetia itens da lista de "anacronismos proibidos" como se
  estivessem na imagem. Corrigido: a regra manda listar SÓ o que realmente aparece.
- **Penalizar cor** — tratava "cores vibrantes" como anacronismo. Corrigido: a regra manda
  ignorar a paleta de cores.

Com isso a calibração passa nas duas direções (positivo ukiyo-e feudal / negativo UI-como-feudal).
Ainda assim o 7B é mais fraco que o gpt-4o em nuance — use `--judge remote` para aferição forte.
O `judge_image` detecta PNG/JPEG pelos magic bytes, então fixtures podem ser `.png` ou `.jpg`.
