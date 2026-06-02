# Discussão — Ambientação na imagem, aviso de personagem órfão e evals

- **Data:** 2026-06-02
- **Status:** Discussão + **harness de eval (estágio roteiro) implementado** em 2026-06-02.
  Pontos 1 e 2 seguem como backlog.
- **Escopo:** levantamento de causa raiz, propostas e o harness de evals já funcionando.

> **Implementado (estágios roteiro + imagem):** `sumi-api/evals/` (`cases.json`, `judge.py`,
> `README.md`) + `sumi-api/scripts/eval_run.py`. Juiz local (Ollama) por padrão,
> `--judge remote` para gpt-4o. Dois estágios:
> - `roteiro` (texto): juiz `qwen2.5:14b` nota o JSON. Validado — feudal coerente 5/5 (passa);
>   mock "escola japonesa" (o bug do Ponto 2) 0/0 com anacronismos (reprova).
> - `image` (visão): gera o quadro de estabelecimento com `gpt-image-1` e juiz `qwen2.5vl:7b`
>   avalia o PNG. Validado — screenshot moderno vs. briefing feudal → 0/0, reprova listando
>   "prédios modernos, interface de computador". PNGs em `evals/reports/images/`.
>
> Detalhes de uso em `sumi-api/evals/README.md`.

> **Evolução do estágio image (2026-06-02):**
> - **`image_prompt` opcional** por caso: prompt específico que **isola o `gpt-image-1`** do
>   gerador de roteiro (localiza o item 3 da causa raiz — se o modelo de imagem ignora a época
>   mesmo com prompt explícito).
> - **Amostragem N** (`--samples`, padrão 3): gera N imagens por caso, juiz avalia cada uma,
>   caso passa por **maioria estrita**; relatório mostra a **taxa** (revela instabilidade do
>   gerador, ex.: 2/3).
> - **Estágio `calib`**: calibração do juiz com PNGs versionados em `evals/fixtures/` (veredito
>   esperado). Não chama `gpt-image-1` nem exige `.env` (local). É o "teste do teste".
> - **Correção de gate**: o eixo de personagens só conta quando o briefing espera personagem
>   (planos de estabelecimento sem personagem não são mais reprovados injustamente).
> - **Vieses do juiz 7B descobertos e corrigidos no system prompt**: (1) *ecoava a lista de
>   anacronismos proibidos* como se estivessem na imagem; (2) *penalizava cor* ("cores vibrantes"
>   = anacronismo). Regras adicionadas: listar só o que realmente aparece + ignorar a paleta de
>   cores. `judge_image` agora detecta PNG/JPEG por magic bytes.
> - **Calibração 2/2 nas duas direções**: positivo = `ukiyo-e-samurai.jpg` (The Met Open Access,
>   CC0, objeto 843990, nishiki-e ~1820s) passa; negativo = `modern-ui.png` (screenshot) reprova
>   contra briefing feudal. Decisão do usuário: positivo via ukiyo-e de domínio público.

---

## Contexto

Três temas levantados a partir do uso real do produto:

1. Avisar, no botão "Avançar → Roteiro", quando a *Ideia inicial* cita personagens que não
   existem em *Personagens*.
2. A imagem gerada não respeita a ambientação do roteiro (roteiro de **Japão Feudal** gerou
   uma imagem de **universidade / prédio moderno**).
3. Montar **testes de avaliação (evals)** estilo LLM-as-judge, disparados manualmente pelo dev
   para economizar token.

---

## Ponto 1 — Aviso de personagem citado na Ideia sem correspondente em Personagens

### Decisão de produto
Deve ser um **aviso não-bloqueante**. A IA pode legitimamente "promover" um nome citado na
ideia a personagem de cena — bloquear seria errado.

### O que o código já faz
`sumi-api/src/prompt_clinica/ai/roteiro.py` (`generate_roteiro`, ~L47–55) já envia para a IA:
- a **premissa inteira** (texto livre da ideia), e
- a **lista de personagens cadastrados** (`character_names`).

### O problema real: detecção
Como saber que "Kenji" na ideia é um personagem, e não um lugar ou início de frase?

| Abordagem | Prós | Contras |
|---|---|---|
| Heurística (palavra capitalizada) | barata, no front | falsos positivos em PT (início de frase, topônimos como "Japão Feudal") |
| IA extrai nomes próprios de pessoas | confiável | chamada extra |

### Proposta recomendada (caminho mais simples)
Aproveitar a chamada de IA que **já acontece** no "Avançar → Roteiro": fazer o
`generate_roteiro` devolver no JSON um campo extra (ex.: `personagens_novos: [...]`) com os
nomes que a IA usou e que **não** estavam na lista cadastrada.

- Custo adicional ≈ zero.
- O aviso aparece **depois** de gerar, mostrando exatamente o que a IA inventou — mais útil do
  que adivinhar antes.

---

## Ponto 2 — Imagem ignora a ambientação (Japão Feudal → prédio moderno)

### Esclarecimento técnico importante
`gpt-image-1` **não aceita System Message**. É um modelo de imagem; recebe apenas um `prompt`
string (ver `sumi-api/src/prompt_clinica/ai/providers/openai_provider.py`, `image()` ~L57–66).
A ideia de "usar um SystemMessage na geração de imagem" **não tem onde encaixar** — a correção
é **injetar a ambientação dentro do próprio prompt** de cada quadro.

### Causa raiz
Em `sumi-api/src/prompt_clinica/services/panel_service.py`, tanto `generate_image` (~L205–210)
quanto `generate_all_images` (~L372–377) montam:

```python
base_prompt = panel.prompt or panel.caption or "manga panel"
img_prompt = (
    "Manga shojo style, black and white screentone, clean ink line art, "
    "no text, no speech bubbles, expressive eyes, high contrast. "
    f"{base_prompt}"
)
```

O prompt da imagem usa **apenas** o `panel.prompt` daquele quadro isolado — **nenhum contexto
global de época/lugar**. O quadro de estabelecimento vira "um prédio qualquer".

### Agravante: fallback mock temático
Se `generate_roteiro` falha, o serviço cai em `_MOCK_TEMPLATES` (`panel_service.py` ~L171–173),
cujo **primeiro** quadro é literalmente:

```python
"prompt": "Wide establishing shot of a Japanese school setting, ..."
```

Ou seja: independentemente do tema, o fallback gera **escola japonesa shojo**. Isso explica bem
o "universidade / prédio moderno". **Conferir nos logs** se apareceu
`generate_roteiro falhou ... usando fallback mock` — se sim, o problema nesse caso foi o mock,
não a IA "errando" a ambientação.

### A peça que falta no modelo
`Project` (`sumi-api/models/project.py`, L26–37) tem `genre`, `tone`, `style`, `premise`,
`synopsis` — mas **nenhum campo de ambientação visual**.

### Proposta recomendada
1. A IA do roteiro passa a retornar também um **`setting` / guia visual global**
   (ex.: *"feudal Japan, traditional wooden architecture, kimono, no modern elements"*),
   persistido no `Project`.
2. `generate_image` / `generate_all_images` fazem **prepend** desse `setting` em **todo**
   `img_prompt`. Assim cada quadro — e cada regeneração individual — herda a época, sem depender
   da IA repetir "feudal" em todos os ~15 prompts.
3. **Corrigir o fallback mock** para não ser temático (escola japonesa), ou não cair em mock
   temático silenciosamente.

> ⚠️ Campo novo no `Project` exige **migration Alembic manual no deploy** (Alembic não roda
> automático no deploy deste projeto).

---

## Ponto 3 — Evals com LLM-as-judge (disparados pelo dev)

Padrão de **avaliação de LLM**: um conjunto de prompts curados é passado para a IA e a resposta
é avaliada por outra IA (ou por votação). Roda **só quando o dev dispara** — fora do `pytest`/CI
para não queimar token. É também a **ferramenta que mede se o conserto do Ponto 2 funcionou**
("a ambientação melhorou?" deixa de ser achismo e vira número).

### Dois estágios (juízes diferentes)

**Estágio 1 — roteiro (texto, barato).**
Para cada caso: chama `generate_roteiro` e um **juiz LLM** lê o JSON. Não gera imagem. Rubric:
- a ambientação foi preservada? (ex.: "Brasil, descobrimento" → os `prompt` por quadro falam de
  período colonial, sem anacronismo?)
- os atributos dos personagens sobreviveram? (ex.: "garoto negro perdido" → personagem segue
  negro e criança?)
- caiu no fallback mock? (detectável **sem IA** — se vier "Japanese school", reprova direto)

Usa o `provider.text()` que **já existe**.

**Estágio 2 — imagem (caro).**
Gera o roteiro, escolhe **1 quadro** (o de estabelecimento), gera a imagem e um **juiz com
visão** (ex.: gpt-4o enxergando o PNG) avalia: "esta imagem retrata {Nova York moderna / Brasil
colonial}? há anacronismo? bate com {garoto negro}?". É o único jeito de pegar o "prédio
moderno em vez de Japão feudal", porque o erro só aparece no pixel.

> O `OpenAIProvider` atual só **gera** imagem, **não lê** imagem. O estágio 2 exige uma pequena
> extensão no provider (text com input de imagem). Por isso começar pelo estágio 1.

### Casos-fixture (exemplos do usuário)
Cobrem os dois modos de falha ao mesmo tempo — **lugar/época** e **traço do personagem**:

```yaml
- id: nova-york-garoto
  premise: "Cidade de Nova York, garoto negro perdido na multidão"
  espera: { lugar: "Nova York moderna", personagem: "garoto negro, criança" }
- id: descobrimento-brasil
  premise: "Brasil na época do descobrimento, um índio falando com um português"
  espera: { epoca: "1500, colonial", anacronismo: "nenhum" }
- id: japao-feudal
  premise: "Japão feudal, um samurai..."
  espera: { epoca: "feudal", anacronismo: "nada moderno (prédios, escolas)" }
```

### Votação / self-consistency
"Votar na resposta" = rodar o juiz **N vezes e agregar** (maioria/média) para reduzir variância.
Mais robusto, mas multiplica o custo do juiz. Recomendação: começar **determinístico**
(1 chamada, temperatura 0) e só adicionar votação se o juiz se mostrar instável.

### Forma proposta (caminho mais simples)
- `sumi-api/evals/cases.yaml` + `scripts/eval_run.py`, disparado pelo dev:
  `uv run python scripts/eval_run.py --stage roteiro` (e `--stage image` para o caro).
- **Nunca** entra na suíte `pytest` (não queimar token em CI).
- Saída: tabela no console + `evals/reports/<data>.md` com nota por caso e taxa de aprovação.

### Juiz local (GPU) + fallback remoto por parâmetro

Hardware disponível: **RTX 5060 Ti 16 GB** (Blackwell). Dá para rodar o **juiz** localmente
como baseline grátis e usar o remoto (gpt-4o) só quando quiser aferição forte.

**Insight que simplifica:** o **Ollama expõe API compatível com OpenAI**
(`http://localhost:11434/v1`). Como o projeto já usa o SDK `openai`, alternar local/remoto é
basicamente trocar `base_url` + `model` + `api_key` — o código do juiz não muda. A chamada de
**visão** local também é OpenAI-compatible (`image_url` com base64), o que **elimina** o custo
antes citado de "estender o `OpenAIProvider` para *ler* imagem" no caminho local.

**Modelos que cabem em 16 GB:**

| Papel | Modelo recomendado | VRAM aprox. | Observação |
|---|---|---|---|
| Juiz de texto | Qwen2.5 14B-instruct (Q4_K_M) | ~9 GB | bom em JSON e PT; ponto ótimo |
| Juiz de texto (leve) | Qwen2.5 7B / Llama 3.1 8B | ~5–6 GB | mais rápido, mais contexto |
| Juiz de visão | Qwen2.5-VL 7B | ~6–8 GB | excelente em visão, multilíngue |
| Juiz de visão (alt) | Llama 3.2 Vision 11B | ~9–11 GB | — |

**Parâmetro `--judge local|remote`** seleciona só um trio (resto do juiz idêntico):

| | base_url | model | api_key |
|---|---|---|---|
| `local` | `http://localhost:11434/v1` | `qwen2.5:14b` / `qwen2.5-vl:7b` | dummy |
| `remote` | padrão OpenAI | `gpt-4o` | real |

**Caveats:**
1. **Blackwell (sm_120):** a 5060 Ti exige **Ollama recente** (CUDA 12.8). Versão atual já
   suporta — não usar instalação antiga.
2. **Qualidade:** juiz 7B–14B local é mais fraco que gpt-4o em anacronismo sutil e nuance de
   PT. Por isso: **local = baseline/sinal de regressão (roda à vontade); remote = ground truth
   sob demanda.** Complementares, não concorrentes.
3. **Juiz ≠ gerador.** Rodar o *juiz* local é ótimo. A **geração da imagem avaliada** deve
   continuar sendo a real (`gpt-image-1`) — senão testa-se outro gerador, não o produto.
   Exceção: enquanto se *constrói* o harness, dá para apontar a um gerador local (SDXL/Flux
   cabem nos 16 GB) só para não queimar custo de imagem; a medição "de verdade" usa o real.

**Fluxo natural:** juiz local por padrão → `--judge remote` quando quiser confiança.

### Estado em 2026-06-02: modelos instalados e testados ✅

Ambiente: **Ollama 0.30.0**, RTX 5060 Ti 16 GB (Blackwell) — funcionou sem ajuste.

| Papel | Modelo (tag Ollama) | Tamanho | Teste |
|---|---|---|---|
| Juiz de texto | `qwen2.5:14b` | 9.0 GB | OK — retornou JSON limpo em PT |
| Juiz de visão | `qwen2.5vl:7b` | 6.0 GB | OK — leu PNG (base64) e descreveu em PT |

> ⚠️ Tag correta do modelo de visão é **`qwen2.5vl`** (sem hífen/ponto: não é `qwen2.5-vl`).

Confirmado na prática:
- Endpoint **OpenAI-compatible** ativo em `http://localhost:11434/v1/chat/completions`.
- **Visão via `image_url` com `data:image/png;base64,...`** funciona — o juiz de imagem **não
  precisa** de provider especial; é o mesmo formato OpenAI.
- `temperature: 0` dá resposta determinística (bom para eval estável).
- `api_key` pode ser qualquer string (dummy) no caminho local.

Exemplos de chamada usados no teste:

```bash
# texto
curl -s http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:14b","temperature":0,"messages":[{"role":"user","content":"..."}]}'

# visão (base64 inline)
B64=$(base64 -w0 imagem.png)
curl -s http://localhost:11434/v1/chat/completions -H "Content-Type: application/json" \
  -d "{\"model\":\"qwen2.5vl:7b\",\"temperature\":0,\"messages\":[{\"role\":\"user\",
       \"content\":[{\"type\":\"text\",\"text\":\"...\"},
       {\"type\":\"image_url\",\"image_url\":{\"url\":\"data:image/png;base64,$B64\"}}]}]}"
```

---

## Decisões em aberto (para retomar)

1. **Ponto 2:** começar por `setting` global, corrigir o mock, ou reforçar o prompt do roteiro?
   (recomendação: `setting` global + corrigir mock = resolve a raiz).
2. **Ponto 1:** IA retorna nomes novos no JSON (recomendado) vs. heurística no front.
3. **Evals:** estágio 1 (texto) primeiro vs. já ir ao estágio 2 (visão, precisa estender o
   provider). Juiz determinístico vs. votação.
3b. **Juiz local vs. remoto:** começar com Ollama local (Qwen2.5 14B / Qwen2.5-VL 7B) como
    baseline e expor `--judge remote` para gpt-4o sob demanda.
4. **Ordem geral:** implementar a eval **antes** (captura linha de base ruim) ou **depois** do
   conserto do Ponto 2?

---

## Arquivos relevantes

- `sumi-api/src/prompt_clinica/services/panel_service.py` — montagem do `img_prompt`, fallback
  mock, geração de quadros e imagens.
- `sumi-api/src/prompt_clinica/ai/roteiro.py` — `generate_roteiro` (system prompt + JSON).
- `sumi-api/src/prompt_clinica/ai/providers/openai_provider.py` — `text()` e `image()`.
- `sumi-api/models/project.py` — modelo `Project` (sem campo de ambientação).
