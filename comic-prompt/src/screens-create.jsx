// src/screens-create.jsx — New project (idea + genre) + Characters (manual + AI + library)
const { useState: useStateC, useMemo: useMemoC } = React;

/* ────────────────────────────────────────────────────────────────────
   1) NEW PROJECT — Ideia inicial + Gênero + Estilo visual
   ──────────────────────────────────────────────────────────────────── */
function NewProject({ go, draft, setDraft }) {
  const [idea, setIdea] = useStateC(draft.idea || "");
  const [genre, setGenre] = useStateC(draft.genre || "Shojo");
  const [tone, setTone] = useStateC(draft.tone || "Doce e melancólico");
  const [pages, setPages] = useStateC(draft.pages || 4);
  const [style, setStyle] = useStateC(draft.style || "classic-shoujo");

  const tones = ["Doce e melancólico", "Tenso", "Cômico", "Mistério leve", "Reflexivo", "Heróico"];

  const next = () => {
    setDraft({ ...draft, idea, genre, tone, pages, style });
    go("characters");
  };

  const examples = [
    "Uma estudante recebe uma carta anônima debaixo da carteira no último dia de aula.",
    "Um gato preto guia uma garota tímida até um portão que ela nunca tinha visto.",
    "Dois rivais de clube esquecem o jogo quando começa a chover.",
  ];

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="ETAPA 1 DE 5"
        title="Conte a primeira faísca."
        lede="Não precisa ser detalhada. Uma ideia em uma frase é suficiente — a IA vai te ajudar a expandir, propor cenas e sugerir personagens."
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 24, alignItems: "start" }}>
        <Card>
          <div className="col" style={{ gap: 20 }}>
            <Field label="Sua ideia">
              <textarea
                className="textarea serif"
                style={{ fontSize: 19, lineHeight: 1.5, minHeight: 130 }}
                placeholder="Ex: Uma carta dobrada cai do livro emprestado. Quem a colocou ali?"
                value={idea} onChange={e => setIdea(e.target.value)}
              />
              <div className="text-xs muted" style={{ marginTop: 6 }}>
                Sugestões para começar:
              </div>
              <div className="row" style={{ flexWrap: "wrap", marginTop: 4 }}>
                {examples.map(ex => (
                  <Chip key={ex} onClick={() => setIdea(ex)}>{ex}</Chip>
                ))}
              </div>
            </Field>

            <div className="divider dashed"></div>

            <Field label="Gênero">
              <div className="row" style={{ flexWrap: "wrap" }}>
                {window.GENRES.map(g => (
                  <Chip key={g} active={genre === g} onClick={() => setGenre(g)}>{g}</Chip>
                ))}
              </div>
            </Field>

            <Field label="Tom emocional">
              <div className="row" style={{ flexWrap: "wrap" }}>
                {tones.map(t => (
                  <Chip key={t} active={tone === t} onClick={() => setTone(t)}>{t}</Chip>
                ))}
              </div>
            </Field>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
              <Field label="Páginas" hint="A IA distribuirá os quadros entre as páginas.">
                <div className="row">
                  <IconButton name="x" onClick={() => setPages(Math.max(1, pages - 1))} />
                  <div style={{
                    width: 56, height: 38, display: "grid", placeItems: "center",
                    border: "1px solid var(--rule)", borderRadius: "var(--r-sm)",
                    fontFamily: "var(--serif)", fontSize: 22, background: "var(--paper-3)",
                  }}>{pages}</div>
                  <IconButton name="plus" onClick={() => setPages(Math.min(20, pages + 1))} />
                  <div className="text-xs muted" style={{ marginLeft: 8 }}>
                    ≈ {pages * 3}–{pages * 4} quadros
                  </div>
                </div>
              </Field>

              <Field label="Idioma dos balões">
                <select className="select" defaultValue="pt-BR">
                  <option value="pt-BR">Português (BR)</option>
                  <option value="ja">日本語</option>
                  <option value="en">English</option>
                  <option value="es">Español</option>
                </select>
              </Field>
            </div>
          </div>
        </Card>

        {/* Right column: style + how it works */}
        <div className="col" style={{ gap: 18 }}>
          <Card>
            <div className="section-eyebrow" style={{ marginBottom: 10 }}>ESTILO VISUAL</div>
            <div className="col" style={{ gap: 10 }}>
              {window.STYLES.map(s => (
                <button key={s.id}
                  onClick={() => setStyle(s.id)}
                  style={{
                    textAlign: "left",
                    border: style === s.id ? "1.5px solid var(--ink)" : "1px solid var(--rule)",
                    background: style === s.id ? "var(--accent-soft)" : "var(--paper-3)",
                    borderRadius: "var(--r-sm)",
                    padding: 10, cursor: "pointer",
                  }}>
                  <div style={{ fontFamily: "var(--serif)", fontSize: 14 }}>{s.label}</div>
                  <div className="text-xs muted">{s.note}</div>
                </button>
              ))}
            </div>
          </Card>

          <Card>
            <div className="section-eyebrow" style={{ marginBottom: 10 }}>COMO FUNCIONA</div>
            <ol style={{
              margin: 0, paddingLeft: 18,
              color: "var(--ink-2)", fontSize: 13, lineHeight: 1.7,
            }}>
              <li>Você dá a ideia inicial.</li>
              <li>Cadastra (ou gera) os personagens.</li>
              <li>A IA propõe o roteiro e os quadros.</li>
              <li>Você revisa <em>quadro a quadro</em> e ajusta.</li>
              <li>Exporta como página de mangá.</li>
            </ol>
          </Card>
        </div>
      </div>

      {/* Footer actions */}
      <div className="row" style={{ marginTop: 28, justifyContent: "space-between" }}>
        <Button kind="ghost" icon="back" onClick={() => go("home")}>Cancelar</Button>
        <Button kind="primary" iconRight="arr_r" onClick={next} disabled={!idea.trim()}>
          Avançar — personagens
        </Button>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────
   2) CHARACTERS — manual + library + AI generation
   ──────────────────────────────────────────────────────────────────── */
function CharactersScreen({ go, draft, setDraft }) {
  const [tab, setTab] = useStateC("library");  // library | manual | ai
  const [selected, setSelected] = useStateC(draft.chars || ["yumi", "ren"]);
  const [aiSheet, setAiSheet] = useStateC(null); // character being generated

  const toggle = (id) => {
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);
  };

  const next = () => {
    setDraft({ ...draft, chars: selected });
    go("script");
  };

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="ETAPA 2 DE 5"
        title="Quem habita essa história?"
        lede="Escolha da biblioteca, crie um cadastro manual, ou peça à IA para gerar um novo personagem a partir de uma descrição."
        actions={
          <div className="row">
            <div className="text-sm muted">
              {selected.length} {selected.length === 1 ? "personagem" : "personagens"} no elenco
            </div>
          </div>
        }
      />

      <div className="row" style={{ marginBottom: 18, borderBottom: "1px solid var(--rule)" }}>
        {[
          { id: "library", label: "Biblioteca", icon: "book" },
          { id: "manual",  label: "Criar manualmente", icon: "edit" },
          { id: "ai",      label: "Gerar com IA", icon: "spark" },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{
              padding: "10px 14px",
              background: "transparent", border: "none",
              cursor: "pointer",
              color: tab === t.id ? "var(--ink)" : "var(--ink-3)",
              fontWeight: tab === t.id ? 600 : 400,
              fontSize: 13,
              borderBottom: tab === t.id ? "2px solid var(--ink)" : "2px solid transparent",
              marginBottom: -1,
              display: "flex", alignItems: "center", gap: 7,
            }}>
            <Icon name={t.icon} size={14} /> {t.label}
          </button>
        ))}
      </div>

      {tab === "library" && (
        <LibraryGrid selected={selected} onToggle={toggle} />
      )}
      {tab === "manual" && (
        <ManualForm onCreate={(c) => { window.MOCK_CHARS.push(c); setSelected(s => [...s, c.id]); setTab("library"); }} />
      )}
      {tab === "ai" && (
        <AIGenerate onConfirm={(c) => { window.MOCK_CHARS.push(c); setSelected(s => [...s, c.id]); setTab("library"); }} />
      )}

      <div className="row" style={{ marginTop: 28, justifyContent: "space-between" }}>
        <Button kind="ghost" icon="back" onClick={() => go("new")}>Voltar</Button>
        <div className="row">
          <Button kind="default" onClick={() => go("script")}>Pular — IA decide depois</Button>
          <Button kind="primary" iconRight="arr_r" onClick={next} disabled={selected.length === 0}>
            Avançar — roteiro
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ── Library grid ───────────────────────────────────────────────── */
function LibraryGrid({ selected, onToggle }) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
      gap: 14,
    }}>
      {window.MOCK_CHARS.map(c => (
        <CharacterCard key={c.id} char={c}
          selected={selected.includes(c.id)}
          onToggle={() => onToggle(c.id)} />
      ))}
    </div>
  );
}

function CharacterCard({ char, selected, onToggle }) {
  return (
    <div
      onClick={onToggle}
      style={{
        background: "var(--paper-3)",
        border: selected ? "1.5px solid var(--ink)" : "1px solid var(--rule)",
        borderRadius: "var(--r-lg)",
        padding: 16,
        cursor: "pointer",
        boxShadow: selected ? "var(--shadow-2)" : "var(--shadow-1)",
        position: "relative",
        display: "flex", flexDirection: "column", gap: 10,
      }}>
      {selected && (
        <div style={{
          position: "absolute", top: 10, right: 10,
          background: "var(--accent)", color: "var(--ink)",
          width: 22, height: 22, borderRadius: "50%",
          border: "1.5px solid var(--ink)",
          display: "grid", placeItems: "center",
        }}>
          <Icon name="check" size={12} stroke={2.4} />
        </div>
      )}
      <div className="row" style={{ gap: 12 }}>
        <Avatar name={char.name} size={52} />
        <div style={{ minWidth: 0 }}>
          <div style={{ fontFamily: "var(--serif)", fontSize: 17, lineHeight: 1.1 }}>{char.name}</div>
          <div className="text-xs muted">{char.role} · {char.age} anos</div>
        </div>
      </div>
      <div className="text-sm" style={{ color: "var(--ink-2)", lineHeight: 1.45 }}>
        {char.summary}
      </div>
      <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
        {char.traits.map(t => (
          <span key={t} className="chip muted text-xs">{t}</span>
        ))}
      </div>
      {!char.approved && (
        <div style={{
          fontFamily: "var(--mono)", fontSize: 10, letterSpacing: "0.1em",
          color: "var(--ink-3)",
          borderTop: "1px dashed var(--rule)", paddingTop: 8,
        }}>RASCUNHO · AGUARDA APROVAÇÃO</div>
      )}
    </div>
  );
}

/* ── Manual form ────────────────────────────────────────────────── */
function ManualForm({ onCreate }) {
  const [form, setForm] = useStateC({
    name: "", role: "", age: 16, height: "", summary: "", outfit: "",
    traits: "",
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const create = () => {
    if (!form.name.trim()) return;
    onCreate({
      id: form.name.toLowerCase().replace(/\s+/g, "-") + "-" + Date.now().toString(36).slice(-4),
      name: form.name, role: form.role, age: +form.age, height: form.height,
      summary: form.summary,
      traits: form.traits.split(",").map(s => s.trim()).filter(Boolean),
      outfit: form.outfit,
      palette: ["#F4D6D7", "#E5A6A8"],
      approved: true,
    });
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 24, alignItems: "start" }}>
      <Card>
        <div className="col" style={{ gap: 16 }}>
          <Field label="Nome do personagem">
            <input className="input serif" value={form.name}
              placeholder="Ex: Aiko Tanaka"
              onChange={e => set("name", e.target.value)} />
          </Field>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            <Field label="Papel">
              <input className="input" value={form.role}
                placeholder="Protagonista"
                onChange={e => set("role", e.target.value)} />
            </Field>
            <Field label="Idade">
              <input className="input" type="number" value={form.age}
                onChange={e => set("age", e.target.value)} />
            </Field>
            <Field label="Altura">
              <input className="input" value={form.height}
                placeholder="1.60 m"
                onChange={e => set("height", e.target.value)} />
            </Field>
          </div>
          <Field label="Descrição visual" hint="Cabelo, olhos, expressão, marca registrada — a IA usa para manter a coerência entre quadros.">
            <textarea className="textarea" value={form.summary}
              placeholder="Olhos grandes castanho-âmbar, franja reta, sempre carrega um caderno surrado..."
              onChange={e => set("summary", e.target.value)} />
          </Field>
          <Field label="Figurino padrão">
            <input className="input" value={form.outfit}
              placeholder="Uniforme escolar, meia-calça preta"
              onChange={e => set("outfit", e.target.value)} />
          </Field>
          <Field label="Traços de personalidade" hint="Separe por vírgula. A IA usa para escrever os balões.">
            <input className="input" value={form.traits}
              placeholder="curiosa, sarcástica, leal"
              onChange={e => set("traits", e.target.value)} />
          </Field>
        </div>
      </Card>

      <Card>
        <div className="section-eyebrow" style={{ marginBottom: 10 }}>PRÉVIA</div>
        <div className="col" style={{ alignItems: "center", gap: 10 }}>
          <Avatar name={form.name || "?"} size={88} />
          <div style={{ fontFamily: "var(--serif)", fontSize: 18 }}>
            {form.name || "Novo personagem"}
          </div>
          <div className="text-xs muted" style={{ textAlign: "center" }}>
            {form.role || "—"} {form.age && `· ${form.age} anos`}
          </div>
        </div>
        <div className="divider dashed" style={{ margin: "16px 0" }}></div>
        <Button kind="primary" icon="check" onClick={create} disabled={!form.name.trim()}
          style={{ width: "100%", justifyContent: "center" }}>
          Adicionar ao elenco
        </Button>
        <div className="text-xs muted" style={{ marginTop: 10, textAlign: "center" }}>
          Você pode editar depois.
        </div>
      </Card>
    </div>
  );
}

/* ── AI Generation ──────────────────────────────────────────────── */
function AIGenerate({ onConfirm }) {
  const [mode, setMode] = useStateC("prompt"); // prompt | attrs
  const [prompt, setPrompt] = useStateC("Uma garota tímida de 16 anos, olhos grandes castanho-âmbar com brilho, franja reta, sempre carrega um caderno. Veste uniforme escolar.");
  const [attrs, setAttrs] = useStateC({
    archetype: "protagonista", age: 16, hair: "preto, franja reta",
    eyes: "âmbar, grandes", outfit: "uniforme escolar",
    personality: "tímida, curiosa", quirk: "anota tudo em um caderno",
  });
  const [generating, setGenerating] = useStateC(false);
  const [candidates, setCandidates] = useStateC([]);
  const [picked, setPicked] = useStateC(null);
  const [name, setName] = useStateC("");

  const generate = () => {
    setGenerating(true);
    setCandidates([]);
    setPicked(null);
    setTimeout(() => {
      setGenerating(false);
      // Generate 4 candidate "portraits"
      const tones = ["dots", "diag", "dense", "dots"];
      const palettes = TONE_KEYS;
      setCandidates(tones.map((t, i) => ({
        id: "cand-" + i,
        tone: t,
        palette: palettes[i % palettes.length],
        notes: CANDIDATE_NOTES[i],
      })));
    }, 1200);
  };

  const confirm = () => {
    if (!picked || !name.trim()) return;
    const cand = candidates.find(c => c.id === picked);
    onConfirm({
      id: name.toLowerCase().replace(/\s+/g, "-") + "-" + Date.now().toString(36).slice(-4),
      name,
      role: attrs.archetype,
      age: mode === "attrs" ? attrs.age : 16,
      height: "—",
      summary: mode === "prompt" ? prompt : `${attrs.hair}, ${attrs.eyes}, ${attrs.outfit}.`,
      traits: mode === "prompt"
        ? ["gerado por IA"]
        : attrs.personality.split(",").map(s => s.trim()).filter(Boolean),
      outfit: mode === "attrs" ? attrs.outfit : "",
      palette: ["#F4D6D7", "#E5A6A8"],
      approved: true,
    });
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.1fr)", gap: 24, alignItems: "start" }}>
      {/* LEFT: input */}
      <Card>
        <div className="row" style={{ marginBottom: 16, gap: 0, background: "var(--paper-2)", border: "1px solid var(--rule)", padding: 3, borderRadius: 999 }}>
          {[
            { id: "prompt", label: "Prompt livre" },
            { id: "attrs",  label: "Por atributos" },
          ].map(m => (
            <button key={m.id} onClick={() => setMode(m.id)}
              style={{
                flex: 1, padding: "8px 12px",
                background: mode === m.id ? "var(--paper-3)" : "transparent",
                border: mode === m.id ? "1px solid var(--ink)" : "1px solid transparent",
                borderRadius: 999,
                fontWeight: mode === m.id ? 600 : 400,
                fontSize: 13, cursor: "pointer",
                color: "var(--ink)",
              }}>{m.label}</button>
          ))}
        </div>

        {mode === "prompt" ? (
          <Field label="Descreva o personagem em linguagem natural" hint="Quanto mais detalhe visual, melhor a IA mantém coerência.">
            <textarea className="textarea" style={{ minHeight: 170 }}
              value={prompt} onChange={e => setPrompt(e.target.value)} />
          </Field>
        ) : (
          <div className="col" style={{ gap: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <Field label="Arquétipo">
                <input className="input" value={attrs.archetype}
                  onChange={e => setAttrs({ ...attrs, archetype: e.target.value })} />
              </Field>
              <Field label="Idade">
                <input className="input" type="number" value={attrs.age}
                  onChange={e => setAttrs({ ...attrs, age: +e.target.value })} />
              </Field>
            </div>
            <Field label="Cabelo">
              <input className="input" value={attrs.hair}
                onChange={e => setAttrs({ ...attrs, hair: e.target.value })} />
            </Field>
            <Field label="Olhos">
              <input className="input" value={attrs.eyes}
                onChange={e => setAttrs({ ...attrs, eyes: e.target.value })} />
            </Field>
            <Field label="Figurino">
              <input className="input" value={attrs.outfit}
                onChange={e => setAttrs({ ...attrs, outfit: e.target.value })} />
            </Field>
            <Field label="Personalidade (vírgulas)">
              <input className="input" value={attrs.personality}
                onChange={e => setAttrs({ ...attrs, personality: e.target.value })} />
            </Field>
            <Field label="Marca / quirk">
              <input className="input" value={attrs.quirk}
                onChange={e => setAttrs({ ...attrs, quirk: e.target.value })} />
            </Field>
          </div>
        )}

        <Button kind="accent" icon="spark" onClick={generate} disabled={generating}
          style={{ marginTop: 16, width: "100%", justifyContent: "center" }}>
          {generating ? "Gerando 4 esboços…" : "Gerar 4 retratos"}
        </Button>
        <div className="text-xs muted" style={{ marginTop: 8, textAlign: "center" }}>
          A IA propõe quatro variações. Você confirma a que combina.
        </div>
      </Card>

      {/* RIGHT: candidates */}
      <div>
        <div className="section-eyebrow" style={{ marginBottom: 10 }}>
          {candidates.length ? "ESCOLHA O RETRATO" : "OS RETRATOS APARECEM AQUI"}
        </div>

        {generating && (
          <div style={{
            display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12,
          }}>
            {[0,1,2,3].map(i => (
              <div key={i} style={{
                aspectRatio: "3/4", background: "var(--paper-2)",
                border: "1px dashed var(--rule)", borderRadius: 2,
                display: "grid", placeItems: "center",
                color: "var(--ink-3)", fontFamily: "var(--mono)", fontSize: 11,
                position: "relative", overflow: "hidden",
              }}>
                <div style={{
                  position: "absolute", inset: 0,
                  background: "linear-gradient(110deg, transparent 35%, rgba(255,250,236,0.6) 50%, transparent 65%)",
                  animation: "shimmer 1.4s linear infinite",
                }}></div>
                gerando…
              </div>
            ))}
            <style>{`@keyframes shimmer { 0%{transform: translateX(-100%);} 100%{transform: translateX(100%);} }`}</style>
          </div>
        )}

        {!generating && candidates.length === 0 && (
          <EmptyHint>Escreva a descrição e clique em <b>Gerar 4 retratos</b>.</EmptyHint>
        )}

        {!generating && candidates.length > 0 && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {candidates.map((c, i) => (
                <CandidatePortrait key={c.id} cand={c} idx={i}
                  picked={picked === c.id}
                  onPick={() => setPicked(c.id)} />
              ))}
            </div>

            <div className="row" style={{ marginTop: 14, justifyContent: "space-between" }}>
              <Button kind="ghost" icon="refresh" onClick={generate}>
                Gerar outras 4
              </Button>
              <div className="text-xs muted">Clique em um retrato para selecioná-lo.</div>
            </div>

            {picked && (
              <Card style={{ marginTop: 18 }}>
                <div className="section-eyebrow" style={{ marginBottom: 10 }}>CONFIRMAR PERSONAGEM</div>
                <Field label="Nome">
                  <input className="input serif" value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="Ex: Aiko Tanaka" />
                </Field>
                <div className="row" style={{ marginTop: 14, justifyContent: "flex-end" }}>
                  <Button kind="primary" icon="check" onClick={confirm} disabled={!name.trim()}>
                    Adicionar ao elenco
                  </Button>
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </div>
  );
}

const TONE_KEYS = ["blush", "peach", "mint", "lilac"];
const CANDIDATE_NOTES = [
  "Linha leve · olhos marcantes",
  "Sombras suaves · postura tímida",
  "Olhar direto · mais maturidade",
  "Estilo retrô · screentone denso",
];

function CandidatePortrait({ cand, idx, picked, onPick }) {
  return (
    <button
      onClick={onPick}
      style={{
        cursor: "pointer",
        background: `var(--${cand.palette}-soft)`,
        border: picked ? "2px solid var(--ink)" : "1.5px solid var(--ink)",
        borderRadius: 2,
        padding: 0,
        position: "relative",
        aspectRatio: "3/4",
        boxShadow: picked ? "var(--shadow-2)" : "var(--shadow-panel)",
        overflow: "hidden",
        textAlign: "left",
      }}>
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: cand.tone === "diag"
          ? "repeating-linear-gradient(45deg, rgba(30,24,18,0.2) 0 1px, transparent 1px 6px)"
          : cand.tone === "dense"
          ? "radial-gradient(circle, rgba(30,24,18,0.24) 0.8px, transparent 1px)"
          : "radial-gradient(circle, rgba(30,24,18,0.18) 0.6px, transparent 1px)",
        backgroundSize: cand.tone === "dense" ? "4px 4px" : "7px 7px",
        opacity: 0.5,
      }}></div>
      <div style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", gap: 14,
      }}>
        <div style={{
          width: 110, height: 110, borderRadius: "50%",
          background: `var(--${cand.palette})`,
          border: "1.5px solid var(--ink)",
          display: "grid", placeItems: "center",
          fontFamily: "var(--serif)", fontSize: 48,
        }}>?</div>
        <div style={{
          padding: "3px 9px", background: "var(--paper-3)",
          border: "1px solid var(--ink)",
          fontFamily: "var(--mono)", fontSize: 10, letterSpacing: "0.08em",
        }}>VAR · {String(idx + 1).padStart(2, "0")}</div>
      </div>
      <div style={{
        position: "absolute", bottom: 8, left: 8, right: 8,
        fontFamily: "var(--mono)", fontSize: 10,
        background: "var(--paper-3)",
        border: "1px dashed var(--ink-3)",
        padding: "4px 6px",
      }}>{cand.notes}</div>
      {picked && (
        <div style={{
          position: "absolute", top: 8, right: 8,
          background: "var(--accent)", color: "var(--ink)",
          width: 24, height: 24, borderRadius: "50%",
          border: "1.5px solid var(--ink)",
          display: "grid", placeItems: "center",
        }}>
          <Icon name="check" size={13} stroke={2.4} />
        </div>
      )}
    </button>
  );
}

Object.assign(window, { NewProject, CharactersScreen });
