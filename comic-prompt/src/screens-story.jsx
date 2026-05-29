// src/screens-story.jsx — Script proposal + Panel-by-panel review
const { useState: useStateS, useEffect: useEffectS, useMemo: useMemoS } = React;

/* ────────────────────────────────────────────────────────────────────
   3) SCRIPT — IA propõe roteiro (lista de quadros)
   ──────────────────────────────────────────────────────────────────── */
function Script({ go, draft, setDraft }) {
  const [generating, setGenerating] = useStateS(false);
  const [panels, setPanels] = useStateS(draft.panels || []);

  useEffectS(() => {
    if (panels.length === 0) {
      setGenerating(true);
      const t = setTimeout(() => {
        setPanels(window.MOCK_PANELS.map(p => ({ ...p })));
        setGenerating(false);
      }, 1400);
      return () => clearTimeout(t);
    }
  }, []);

  const regenerate = () => {
    setGenerating(true);
    setPanels([]);
    setTimeout(() => {
      setPanels(window.MOCK_PANELS.map(p => ({ ...p })));
      setGenerating(false);
    }, 1400);
  };

  const next = () => {
    setDraft({ ...draft, panels });
    go("review");
  };

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="ETAPA 3 DE 5"
        title="A IA propôs um roteiro."
        lede="Aqui está o storyboard sugerido. Você pode reescrever a sinopse, regerar tudo, ou seguir para revisar quadro por quadro."
        actions={
          <div className="row">
            <Button kind="ghost" icon="refresh" onClick={regenerate} disabled={generating}>
              Regerar tudo
            </Button>
          </div>
        }
      />

      {/* Synopsis card */}
      <Card style={{ marginBottom: 22 }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1px 280px", gap: 22 }}>
          <div>
            <div className="section-eyebrow" style={{ marginBottom: 8 }}>SINOPSE PROPOSTA</div>
            <p style={{
              fontFamily: "var(--serif)", fontSize: 18, lineHeight: 1.55,
              color: "var(--ink)", margin: 0,
            }}>
              {draft.idea ||
              "No último entardecer do semestre, Yumi encontra uma carta dobrada no livro emprestado. Quando finalmente decide ler até o fim, descobre quem nunca esqueceu dela — e precisa decidir se a coragem cabe num único “sim”."}
            </p>
            <div className="row" style={{ marginTop: 12, gap: 6, flexWrap: "wrap" }}>
              <span className="chip">{draft.genre || "Shojo"}</span>
              <span className="chip">{draft.tone || "Doce e melancólico"}</span>
              <span className="chip">{(draft.pages || 4)} páginas</span>
              <span className="chip">{panels.length || 7} quadros</span>
            </div>
          </div>
          <div style={{ background: "var(--rule)" }}></div>
          <div>
            <div className="section-eyebrow" style={{ marginBottom: 8 }}>ELENCO</div>
            <div className="col" style={{ gap: 8 }}>
              {(draft.chars || ["yumi", "ren"]).map(id => {
                const c = window.MOCK_CHARS.find(x => x.id === id);
                if (!c) return null;
                return (
                  <div key={id} className="row" style={{ gap: 10 }}>
                    <Avatar name={c.name} size={32} />
                    <div>
                      <div style={{ fontFamily: "var(--serif)", fontSize: 14 }}>{c.name}</div>
                      <div className="text-xs muted">{c.role}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Card>

      {/* Storyboard */}
      <div className="section-eyebrow" style={{ marginBottom: 12 }}>
        STORYBOARD · {panels.length} QUADROS
      </div>

      {generating && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
          gap: 16,
        }}>
          {[0,1,2,3,4,5].map(i => (
            <div key={i} style={{
              aspectRatio: "4/3",
              background: "var(--paper-2)",
              border: "1px dashed var(--rule)",
              borderRadius: 2,
              display: "grid", placeItems: "center",
              color: "var(--ink-3)", fontFamily: "var(--mono)", fontSize: 11,
              position: "relative", overflow: "hidden",
            }}>
              <div style={{
                position: "absolute", inset: 0,
                background: "linear-gradient(110deg, transparent 35%, rgba(255,250,236,0.55) 50%, transparent 65%)",
                animation: "shimmer 1.4s linear infinite",
              }}></div>
              <div>QUADRO {String(i + 1).padStart(2, "0")} · gerando…</div>
            </div>
          ))}
        </div>
      )}

      {!generating && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 16,
        }}>
          {panels.map(p => (
            <StoryboardCard key={p.id} panel={p}
              onClick={() => { setDraft({ ...draft, panels, currentPanel: p.id }); go("review"); }} />
          ))}
        </div>
      )}

      <div className="row" style={{ marginTop: 28, justifyContent: "space-between" }}>
        <Button kind="ghost" icon="back" onClick={() => go("characters")}>Voltar</Button>
        <Button kind="primary" iconRight="arr_r" onClick={next} disabled={generating || panels.length === 0}>
          Revisar quadro a quadro
        </Button>
      </div>
    </div>
  );
}

function StoryboardCard({ panel, onClick }) {
  const statusColor = panel.status === "approved" ? "var(--mint)" : "var(--peach-soft)";
  return (
    <div onClick={onClick}
      style={{
        cursor: "pointer",
        display: "flex", flexDirection: "column", gap: 10,
      }}>
      <MangaPanel
        index={panel.index}
        label={panel.label}
        aspect={panel.aspect}
        tone={panel.tone}
        character={panel.character}
        bubbles={panel.bubbles}
        sfx={panel.sfx}
      />
      <div className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ minWidth: 0 }}>
          <div className="text-sm" style={{ color: "var(--ink-2)" }}>{panel.caption}</div>
        </div>
        <span style={{
          padding: "2px 7px",
          background: statusColor,
          border: "1px solid var(--ink)",
          fontFamily: "var(--mono)", fontSize: 9, letterSpacing: "0.1em",
          flexShrink: 0,
        }}>{panel.status === "approved" ? "OK" : "REVISAR"}</span>
      </div>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────
   4) REVIEW — Um quadro por vez, foco total
   ──────────────────────────────────────────────────────────────────── */
function Review({ go, draft, setDraft }) {
  const [panels, setPanels] = useStateS(
    draft.panels && draft.panels.length ? draft.panels : window.MOCK_PANELS.map(p => ({ ...p }))
  );
  const initialIdx = useMemoS(() => {
    if (draft.currentPanel) {
      const i = panels.findIndex(p => p.id === draft.currentPanel);
      return Math.max(0, i);
    }
    return 0;
  }, []);
  const [idx, setIdx] = useStateS(initialIdx);
  const [drawer, setDrawer] = useStateS(null); // null | 'prompt' | 'framing'
  const [regenAnim, setRegenAnim] = useStateS(false);

  const cur = panels[idx];

  const setCur = (patch) => {
    setPanels(ps => ps.map((p, i) => i === idx ? { ...p, ...patch } : p));
  };

  const approve = () => {
    setCur({ status: "approved" });
    if (idx < panels.length - 1) setIdx(idx + 1);
  };

  const regen = () => {
    setRegenAnim(true);
    setTimeout(() => {
      setCur({ tone: cur.tone === "diag" ? "dots" : cur.tone === "dots" ? "dense" : "diag" });
      setRegenAnim(false);
    }, 900);
  };

  const remove = () => {
    if (panels.length <= 1) return;
    const newPanels = panels.filter((_, i) => i !== idx).map((p, i) => ({ ...p, index: i + 1 }));
    setPanels(newPanels);
    setIdx(Math.min(idx, newPanels.length - 1));
  };

  const insert = () => {
    const newPanel = {
      id: "new-" + Date.now().toString(36),
      index: idx + 2,
      label: "Novo",
      aspect: "4-3",
      tone: "dots",
      character: null,
      caption: "Quadro novo · descreva o que acontece aqui.",
      framing: "Plano médio",
      bubbles: [],
      prompt: "",
      status: "pending",
    };
    const newPanels = [...panels.slice(0, idx + 1), newPanel, ...panels.slice(idx + 1)]
      .map((p, i) => ({ ...p, index: i + 1 }));
    setPanels(newPanels);
    setIdx(idx + 1);
  };

  const move = (dir) => {
    const j = idx + dir;
    if (j < 0 || j >= panels.length) return;
    const copy = panels.slice();
    [copy[idx], copy[j]] = [copy[j], copy[idx]];
    const reindexed = copy.map((p, i) => ({ ...p, index: i + 1 }));
    setPanels(reindexed);
    setIdx(j);
  };

  useEffectS(() => {
    const onKey = (e) => {
      if (e.key === "ArrowRight") setIdx(i => Math.min(panels.length - 1, i + 1));
      else if (e.key === "ArrowLeft") setIdx(i => Math.max(0, i - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [panels.length]);

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="ETAPA 4 DE 5 — REVISÃO QUADRO A QUADRO"
        title={`Quadro ${String(cur.index).padStart(2, "0")} · ${cur.label}`}
        lede="Use ← → no teclado para navegar. Cada quadro pode ser aprovado, ajustado ou regerado individualmente."
        actions={
          <div className="row">
            <Button kind="ghost" onClick={() => go("script")}>Ver storyboard</Button>
            <Button kind="default" onClick={() => go("editor")}>Editor visual</Button>
          </div>
        }
      />

      {/* progress strip */}
      <ProgressStrip panels={panels} current={idx} onJump={setIdx} />

      <div style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 1.4fr) minmax(320px, 1fr)",
        gap: 24,
        marginTop: 22,
      }}>
        {/* Big panel */}
        <div>
          <div style={{ position: "relative" }}>
            <div style={{
              filter: regenAnim ? "blur(6px)" : "none",
              transition: "filter .3s",
            }}>
              <MangaPanel
                index={cur.index}
                label={cur.label}
                aspect={cur.aspect}
                tone={cur.tone}
                character={cur.character}
                bubbles={cur.bubbles}
                sfx={cur.sfx}
                style={{ maxHeight: 560 }}
              />
            </div>
            {regenAnim && (
              <div style={{
                position: "absolute", inset: 0,
                display: "grid", placeItems: "center",
                fontFamily: "var(--mono)", fontSize: 12,
                color: "var(--ink-2)", letterSpacing: "0.08em",
              }}>REGERANDO QUADRO…</div>
            )}
          </div>

          {/* Nav */}
          <div className="row" style={{ marginTop: 14, justifyContent: "space-between" }}>
            <Button kind="ghost" icon="arr_l" onClick={() => setIdx(Math.max(0, idx - 1))} disabled={idx === 0}>
              Anterior
            </Button>
            <div className="row">
              <IconButton name="trash" title="Excluir quadro" onClick={remove} />
              <IconButton name="move" title="Mover para a esquerda" onClick={() => move(-1)} />
              <IconButton name="move" title="Mover para a direita" onClick={() => move(1)} style={{ transform: "scaleX(-1)" }} />
              <IconButton name="plus" title="Inserir quadro depois deste" onClick={insert} />
            </div>
            <Button kind="ghost" iconRight="arr_r" onClick={() => setIdx(Math.min(panels.length - 1, idx + 1))} disabled={idx === panels.length - 1}>
              Próximo
            </Button>
          </div>
        </div>

        {/* Side: details */}
        <div className="col" style={{ gap: 14 }}>
          {/* Status / actions */}
          <Card style={{ background: cur.status === "approved" ? "var(--mint-soft)" : "var(--paper-3)" }}>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
              <div className="section-eyebrow">STATUS</div>
              <span style={{
                padding: "3px 10px",
                background: cur.status === "approved" ? "var(--mint)" : "var(--peach-soft)",
                border: "1px solid var(--ink)",
                fontFamily: "var(--mono)", fontSize: 10, letterSpacing: "0.12em",
              }}>{cur.status === "approved" ? "APROVADO" : "AGUARDA APROVAÇÃO"}</span>
            </div>
            <div className="row" style={{ gap: 8 }}>
              <Button kind="accent" icon="check" onClick={approve}
                style={{ flex: 1, justifyContent: "center" }}>
                Aprovar e avançar
              </Button>
              <Button kind="default" icon="refresh" onClick={regen}>
                Regerar
              </Button>
            </div>
          </Card>

          {/* Director caption */}
          <Card>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
              <div className="section-eyebrow">DIREÇÃO DA CENA</div>
              <button className="btn btn-ghost btn-sm" onClick={() => setDrawer(drawer === "framing" ? null : "framing")}>
                {cur.framing}
              </button>
            </div>
            <textarea className="textarea"
              value={cur.caption}
              onChange={e => setCur({ caption: e.target.value })}
              style={{ minHeight: 70 }}
            />

            {drawer === "framing" && (
              <div style={{
                marginTop: 12, padding: 12,
                background: "var(--paper-2)",
                border: "1px solid var(--rule)",
                borderRadius: "var(--r-sm)",
              }}>
                <div className="text-xs muted" style={{ marginBottom: 6 }}>Enquadramento</div>
                <div className="row" style={{ flexWrap: "wrap" }}>
                  {window.FRAMINGS.map(f => (
                    <Chip key={f} active={cur.framing === f}
                      onClick={() => { setCur({ framing: f }); setDrawer(null); }}>
                      {f}
                    </Chip>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Bubbles editor */}
          <Card>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
              <div className="section-eyebrow">BALÕES</div>
              <button className="btn btn-ghost btn-sm" onClick={() => {
                setCur({ bubbles: [...cur.bubbles, { text: "Novo balão", x: 8, y: 12, side: "left", kind: "say" }] });
              }}>
                <Icon name="plus" size={12} /> Adicionar
              </button>
            </div>
            {cur.bubbles.length === 0 && (
              <EmptyHint>Sem balões. A IA pode escrever um — ou adicione manualmente.</EmptyHint>
            )}
            <div className="col" style={{ gap: 10 }}>
              {cur.bubbles.map((b, i) => (
                <BubbleEditor key={i} bubble={b}
                  onChange={(nb) => {
                    const arr = cur.bubbles.slice();
                    arr[i] = nb;
                    setCur({ bubbles: arr });
                  }}
                  onRemove={() => {
                    const arr = cur.bubbles.filter((_, j) => j !== i);
                    setCur({ bubbles: arr });
                  }} />
              ))}
            </div>
          </Card>

          {/* Prompt */}
          <Card>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
              <div className="section-eyebrow">PROMPT VISUAL</div>
              <Icon name="wand" size={13} style={{ color: "var(--ink-3)" }} />
            </div>
            <textarea className="textarea mono"
              style={{ minHeight: 90, fontSize: 12, lineHeight: 1.55 }}
              value={cur.prompt}
              onChange={e => setCur({ prompt: e.target.value })}
            />
            <div className="text-xs muted" style={{ marginTop: 6 }}>
              Este texto é enviado ao gerador de imagem. Edite para refinar o resultado.
            </div>
          </Card>
        </div>
      </div>

      <div className="row" style={{ marginTop: 28, justifyContent: "space-between" }}>
        <Button kind="ghost" icon="back" onClick={() => go("script")}>Voltar ao roteiro</Button>
        <div className="row">
          <Button kind="default" onClick={() => { setDraft({ ...draft, panels }); go("editor"); }}>
            Editor visual
          </Button>
          <Button kind="primary" iconRight="arr_r" onClick={() => { setDraft({ ...draft, panels }); go("final"); }}>
            Finalizar HQ
          </Button>
        </div>
      </div>
    </div>
  );
}

function ProgressStrip({ panels, current, onJump }) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: `repeat(${panels.length}, 1fr)`,
      gap: 6,
      background: "var(--paper-3)",
      border: "1px solid var(--rule)",
      borderRadius: "var(--r-sm)",
      padding: 8,
    }}>
      {panels.map((p, i) => (
        <button key={p.id}
          onClick={() => onJump(i)}
          title={`${p.label}`}
          style={{
            border: "1px solid",
            borderColor: i === current ? "var(--ink)" : "var(--rule)",
            background: p.status === "approved" ? "var(--mint-soft)" : "var(--paper-2)",
            padding: "8px 6px",
            cursor: "pointer",
            display: "flex", flexDirection: "column", alignItems: "center", gap: 3,
            borderRadius: 4,
            position: "relative",
          }}>
          <span style={{
            fontFamily: "var(--mono)", fontSize: 10, letterSpacing: "0.06em",
            color: i === current ? "var(--ink)" : "var(--ink-3)",
            fontWeight: i === current ? 700 : 400,
          }}>{String(i + 1).padStart(2, "0")}</span>
          <span style={{
            width: 6, height: 6, borderRadius: "50%",
            background: p.status === "approved" ? "var(--mint)" : "var(--ink-4)",
          }}></span>
        </button>
      ))}
    </div>
  );
}

function BubbleEditor({ bubble, onChange, onRemove }) {
  return (
    <div style={{
      border: "1px solid var(--rule)",
      borderRadius: "var(--r-sm)",
      padding: 10,
      background: "var(--paper-2)",
    }}>
      <div className="row" style={{ gap: 6, marginBottom: 8 }}>
        <select className="select" style={{ width: "auto", padding: "4px 8px", fontSize: 12 }}
          value={bubble.kind || "say"}
          onChange={e => onChange({ ...bubble, kind: e.target.value })}>
          <option value="say">Fala</option>
          <option value="thought">Pensamento</option>
          <option value="shout">Grito</option>
        </select>
        <select className="select" style={{ width: "auto", padding: "4px 8px", fontSize: 12 }}
          value={bubble.side || "left"}
          onChange={e => onChange({ ...bubble, side: e.target.value })}>
          <option value="left">Esquerda</option>
          <option value="right">Direita</option>
        </select>
        <div className="spacer"></div>
        <IconButton name="trash" onClick={onRemove} title="Remover balão" />
      </div>
      <input className="input" value={bubble.text}
        onChange={e => onChange({ ...bubble, text: e.target.value })} />
    </div>
  );
}

Object.assign(window, { Script, Review });
