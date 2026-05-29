// src/screens-editor.jsx — Editor visual (page layout) + Final/Export
const { useState: useStateE, useMemo: useMemoE, useRef: useRefE } = React;

/* ────────────────────────────────────────────────────────────────────
   5) EDITOR — Arrumar a página, arrastar balões
   ──────────────────────────────────────────────────────────────────── */
function Editor({ go, draft, setDraft }) {
  const [panels, setPanels] = useStateE(
    draft.panels && draft.panels.length ? draft.panels : window.MOCK_PANELS.map(p => ({ ...p }))
  );
  const [pageLayout, setPageLayout] = useStateE("manga-vertical"); // manga-vertical | grid | dynamic
  const [selectedPanel, setSelectedPanel] = useStateE(panels[0]?.id);
  const [draggingBubble, setDraggingBubble] = useStateE(null);
  const stageRef = useRefE(null);

  const sel = panels.find(p => p.id === selectedPanel) || panels[0];

  const updateBubble = (panelId, idx, patch) => {
    setPanels(ps => ps.map(p => p.id !== panelId ? p
      : { ...p, bubbles: p.bubbles.map((b, i) => i === idx ? { ...b, ...patch } : b) }
    ));
  };

  /* Stage rendering: arrange panels by layout */
  const layoutDef = LAYOUTS[pageLayout];

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="EDITOR VISUAL"
        title="Componha a página."
        lede="Arraste os balões para reposicionar. Troque o layout da página. Reordene os quadros sem refazer o roteiro."
        actions={
          <div className="row">
            <Button kind="ghost" onClick={() => go("review")}>Revisão</Button>
            <Button kind="primary" iconRight="arr_r" onClick={() => { setDraft({...draft, panels}); go("final"); }}>
              Finalizar
            </Button>
          </div>
        }
      />

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) 300px", gap: 22 }}>
        {/* Stage */}
        <div>
          {/* Layout switch */}
          <div className="row" style={{ marginBottom: 14, gap: 6, flexWrap: "wrap" }}>
            <div className="text-xs muted" style={{ marginRight: 6 }}>LAYOUT DA PÁGINA</div>
            {Object.entries(LAYOUTS).map(([id, l]) => (
              <Chip key={id} active={pageLayout === id} onClick={() => setPageLayout(id)}>
                {l.label}
              </Chip>
            ))}
          </div>

          {/* Page */}
          <div ref={stageRef}
            style={{
              background: "var(--paper-3)",
              border: "1.5px solid var(--ink-2)",
              padding: 22,
              boxShadow: "var(--shadow-2)",
              display: "grid",
              gap: layoutDef.gap,
              gridTemplateColumns: layoutDef.cols,
              gridTemplateRows: layoutDef.rows,
              aspectRatio: layoutDef.aspect,
              maxHeight: 800,
              position: "relative",
            }}>
            {panels.slice(0, layoutDef.slots.length).map((p, i) => {
              const slot = layoutDef.slots[i];
              return (
                <EditorPanel
                  key={p.id}
                  panel={p}
                  selected={selectedPanel === p.id}
                  onSelect={() => setSelectedPanel(p.id)}
                  gridStyle={slot}
                  onBubbleMove={(idx, x, y) => updateBubble(p.id, idx, { x, y })}
                />
              );
            })}
          </div>

          <div className="text-xs muted" style={{ marginTop: 8, textAlign: "center" }}>
            Página 1 de {Math.max(1, Math.ceil(panels.length / layoutDef.slots.length))} ·
            arraste balões diretamente sobre os quadros
          </div>
        </div>

        {/* Side panel */}
        <div className="col" style={{ gap: 14 }}>
          <Card>
            <div className="section-eyebrow" style={{ marginBottom: 12 }}>QUADROS NA PÁGINA</div>
            <div className="col" style={{ gap: 6 }}>
              {panels.map((p, i) => (
                <button key={p.id}
                  onClick={() => setSelectedPanel(p.id)}
                  style={{
                    display: "flex", alignItems: "center", gap: 10,
                    padding: "6px 8px",
                    background: selectedPanel === p.id ? "var(--accent-soft)" : "transparent",
                    border: selectedPanel === p.id ? "1px solid var(--ink)" : "1px solid transparent",
                    borderRadius: "var(--r-sm)",
                    cursor: "pointer", textAlign: "left",
                  }}>
                  <span style={{
                    width: 22, height: 22, borderRadius: 3,
                    background: "var(--paper-2)",
                    border: "1px solid var(--ink-4)",
                    display: "grid", placeItems: "center",
                    fontFamily: "var(--mono)", fontSize: 10,
                  }}>{String(i + 1).padStart(2, "0")}</span>
                  <span className="text-sm" style={{ flex: 1, color: "var(--ink-2)" }}>{p.label}</span>
                  {p.status === "approved" && (
                    <span style={{
                      width: 7, height: 7, borderRadius: "50%",
                      background: "var(--mint)",
                    }}></span>
                  )}
                </button>
              ))}
            </div>
          </Card>

          {sel && (
            <Card>
              <div className="section-eyebrow" style={{ marginBottom: 10 }}>QUADRO SELECIONADO</div>
              <div className="text-sm" style={{ marginBottom: 8, color: "var(--ink-2)" }}>{sel.caption}</div>
              <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
                <span className="chip muted">{sel.framing}</span>
                <span className="chip muted">{sel.aspect}</span>
              </div>
              <div className="divider dashed" style={{ margin: "14px 0" }}></div>
              <div className="row" style={{ justifyContent: "space-between" }}>
                <span className="text-xs muted">{sel.bubbles.length} balão(ões)</span>
                <Button kind="ghost" size="sm" icon="edit" onClick={() => go("review")}>
                  Editar quadro
                </Button>
              </div>
            </Card>
          )}

          <Card>
            <div className="section-eyebrow" style={{ marginBottom: 10 }}>SENTIDO DE LEITURA</div>
            <div className="row">
              <Chip active>Ocidental →</Chip>
              <Chip>Mangá ←</Chip>
              <Chip>Vertical ↓</Chip>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

const LAYOUTS = {
  "manga-vertical": {
    label: "Mangá vertical",
    cols: "1fr",
    rows: "1.1fr 0.9fr 1fr 1.1fr",
    gap: "10px",
    aspect: "5/8",
    slots: [
      { gridColumn: "1", gridRow: "1" },
      { gridColumn: "1", gridRow: "2" },
      { gridColumn: "1", gridRow: "3" },
      { gridColumn: "1", gridRow: "4" },
    ],
  },
  "grid": {
    label: "Grade ocidental",
    cols: "1fr 1fr",
    rows: "1fr 1fr 1fr",
    gap: "10px",
    aspect: "5/7",
    slots: [
      { gridColumn: "1 / span 2", gridRow: "1" },
      { gridColumn: "1", gridRow: "2" },
      { gridColumn: "2", gridRow: "2" },
      { gridColumn: "1", gridRow: "3" },
      { gridColumn: "2", gridRow: "3" },
    ],
  },
  "dynamic": {
    label: "Dinâmico mangá",
    cols: "2fr 1fr 1.4fr",
    rows: "1.2fr 1fr 1fr",
    gap: "10px",
    aspect: "5/7",
    slots: [
      { gridColumn: "1 / span 2", gridRow: "1" },
      { gridColumn: "3", gridRow: "1 / span 2" },
      { gridColumn: "1", gridRow: "2 / span 2" },
      { gridColumn: "2", gridRow: "2" },
      { gridColumn: "2 / span 2", gridRow: "3" },
    ],
  },
};

function EditorPanel({ panel, selected, onSelect, gridStyle, onBubbleMove }) {
  return (
    <div
      onClick={onSelect}
      style={{
        ...gridStyle,
        background: "var(--paper-3)",
        border: selected ? "2px solid var(--ink)" : "1.5px solid var(--ink)",
        boxShadow: selected ? "0 0 0 4px var(--accent-soft)" : "var(--shadow-panel)",
        position: "relative",
        overflow: "hidden",
        cursor: "pointer",
        borderRadius: "var(--panel-radius)",
      }}>
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage:
          panel.tone === "diag"
            ? "repeating-linear-gradient(45deg, rgba(30,24,18,0.18) 0 1px, transparent 1px 6px)"
          : panel.tone === "dense"
            ? "radial-gradient(circle, rgba(30,24,18,0.22) 0.7px, transparent 1px)"
            : "radial-gradient(circle, rgba(30,24,18,0.18) 0.6px, transparent 1px)",
        backgroundSize: panel.tone === "dense" ? "4px 4px" : "6px 6px",
        opacity: 0.5,
      }}></div>

      {panel.character && (
        <div style={{
          position: "absolute", left: "50%", top: "55%", transform: "translate(-50%, -50%)",
        }}>
          <PanelCharacter name={panel.character} />
        </div>
      )}

      {panel.bubbles.map((b, i) => (
        <DraggableBubble key={i} bubble={b}
          onMove={(x, y) => onBubbleMove(i, x, y)} />
      ))}

      <div className="panel-meta">{String(panel.index).padStart(2, "0")} · {panel.label}</div>
    </div>
  );
}

function DraggableBubble({ bubble, onMove }) {
  const ref = useRefE(null);
  const dragRef = useRefE({ active: false });

  const onDown = (e) => {
    e.stopPropagation();
    const parent = ref.current.parentElement;
    const rect = parent.getBoundingClientRect();
    dragRef.current = { active: true, parentRect: rect };
  };
  const onMoveE = (e) => {
    if (!dragRef.current.active) return;
    const { parentRect } = dragRef.current;
    const x = ((e.clientX - parentRect.left) / parentRect.width) * 100;
    const y = ((e.clientY - parentRect.top) / parentRect.height) * 100;
    onMove(Math.max(0, Math.min(80, x - 8)), Math.max(0, Math.min(85, y - 6)));
  };
  const onUp = () => { dragRef.current.active = false; };

  React.useEffect(() => {
    window.addEventListener("mousemove", onMoveE);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMoveE);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  const cls = "bubble" + (bubble.kind === "thought" ? " thought" : bubble.kind === "shout" ? " shout" : "") + (bubble.side === "right" ? " right" : "");
  return (
    <div ref={ref} className={cls}
      onMouseDown={onDown}
      style={{
        left: bubble.side === "right" ? "auto" : bubble.x + "%",
        right: bubble.side === "right" ? bubble.x + "%" : "auto",
        top: bubble.y + "%",
        cursor: "grab",
        userSelect: "none",
        maxWidth: bubble.width || "55%",
      }}>
      {bubble.text}
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────
   6) FINAL — Visualização final + exportar
   ──────────────────────────────────────────────────────────────────── */
function Final({ go, draft }) {
  const panels = (draft.panels && draft.panels.length ? draft.panels : window.MOCK_PANELS).slice();
  const totalPages = Math.max(1, Math.ceil(panels.length / 4));
  const approved = panels.filter(p => p.status === "approved").length;

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="ETAPA 5 DE 5"
        title="Pronto para o leitor."
        lede="Visualize a HQ completa, exporte como página única ou compartilhe com um link de leitura vertical."
        actions={
          <div className="row">
            <Button kind="ghost" onClick={() => go("editor")}>Voltar ao editor</Button>
            <Button kind="primary" icon="download">Exportar</Button>
          </div>
        }
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", gap: 24, alignItems: "start" }}>
        {/* Final preview */}
        <Card style={{ padding: 0, overflow: "hidden" }}>
          {/* Cover */}
          <div style={{
            position: "relative",
            padding: "48px 32px",
            background: "var(--accent-soft)",
            borderBottom: "1.5px solid var(--ink)",
            backgroundImage: "radial-gradient(circle, rgba(30,24,18,0.18) 0.6px, transparent 1px)",
            backgroundSize: "7px 7px",
          }}>
            <div className="section-eyebrow" style={{ marginBottom: 10 }}>
              {(draft.genre || "Shojo").toUpperCase()} · {panels.length} QUADROS · {totalPages} PÁGINAS
            </div>
            <h1 style={{ fontSize: 44, lineHeight: 1, maxWidth: "14ch", textShadow: "0 1px 0 var(--paper-3)" }}>
              {draft.title || "Carta de Verão"}
            </h1>
            <div className="hand" style={{ fontSize: 24, marginTop: 18, color: "var(--ink-2)" }}>
              uma história de {draft.author || "você"}
            </div>
          </div>

          {/* Pages */}
          <div style={{ padding: 26 }}>
            {Array.from({ length: totalPages }).map((_, pi) => {
              const slice = panels.slice(pi * 4, pi * 4 + 4);
              return (
                <div key={pi} style={{ marginBottom: 26 }}>
                  <div className="row" style={{ justifyContent: "space-between", marginBottom: 10 }}>
                    <div className="section-eyebrow">PÁGINA {String(pi + 1).padStart(2, "0")}</div>
                    <div className="text-xs muted">{slice.length} quadros</div>
                  </div>
                  <div style={{
                    background: "var(--paper-3)",
                    border: "1.5px solid var(--ink-2)",
                    padding: 18,
                    boxShadow: "var(--shadow-1)",
                    display: "grid",
                    gap: 8,
                    gridTemplateColumns: "1fr",
                    aspectRatio: "5/7",
                  }}>
                    {slice.map(p => (
                      <MangaPanel key={p.id}
                        index={p.index}
                        label={p.label}
                        aspect={p.aspect}
                        tone={p.tone}
                        character={p.character}
                        bubbles={p.bubbles}
                        sfx={p.sfx}
                      />
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Side */}
        <div className="col" style={{ gap: 14 }}>
          <Card>
            <div className="section-eyebrow" style={{ marginBottom: 12 }}>RESUMO</div>
            <div className="col" style={{ gap: 8 }}>
              <SummaryRow label="Quadros" value={panels.length} />
              <SummaryRow label="Aprovados" value={`${approved} / ${panels.length}`} />
              <SummaryRow label="Páginas" value={totalPages} />
              <SummaryRow label="Personagens" value={(draft.chars || ["yumi","ren"]).length} />
              <SummaryRow label="Estilo" value={(window.STYLES.find(s => s.id === (draft.style || "classic-shoujo")) || {}).label || "—"} />
            </div>
          </Card>

          <Card>
            <div className="section-eyebrow" style={{ marginBottom: 10 }}>EXPORTAR</div>
            <div className="col" style={{ gap: 8 }}>
              <Button kind="accent" icon="film" onClick={() => go("video")} style={{ width: "100%", justifyContent: "flex-start" }}>
                Gerar vídeo narrado
              </Button>
              <Button kind="default" icon="download" style={{ width: "100%", justifyContent: "flex-start" }}>
                PDF — página única
              </Button>
              <Button kind="default" icon="download" style={{ width: "100%", justifyContent: "flex-start" }}>
                PNG — cada quadro
              </Button>
              <Button kind="default" icon="download" style={{ width: "100%", justifyContent: "flex-start" }}>
                EPUB · leitura vertical
              </Button>
              <Button kind="default" icon="send" style={{ width: "100%", justifyContent: "flex-start" }}>
                Compartilhar link
              </Button>
            </div>
          </Card>

          <Card style={{ background: "var(--mint-soft)" }}>
            <div className="text-sm" style={{ color: "var(--ink-2)" }}>
              <b style={{ fontFamily: "var(--serif)", fontSize: 16 }}>Sua HQ está pronta.</b>
              <div style={{ marginTop: 6 }}>
                Você pode voltar a qualquer etapa para refinar — o progresso fica salvo.
              </div>
            </div>
            <Button kind="primary" onClick={() => go("home")}
              style={{ width: "100%", justifyContent: "center", marginTop: 12 }}>
              Voltar para meus projetos
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}

function SummaryRow({ label, value }) {
  return (
    <div className="row" style={{
      justifyContent: "space-between",
      padding: "4px 0",
      borderBottom: "1px dashed var(--rule)",
    }}>
      <span className="text-sm muted">{label}</span>
      <span className="text-sm" style={{ fontFamily: "var(--serif)", fontSize: 15 }}>{value}</span>
    </div>
  );
}

/* ────────────────────────────────────────────────────────────────────
   7) LIBRARY (full screen)
   ──────────────────────────────────────────────────────────────────── */
function LibraryScreen({ go }) {
  const [q, setQ] = useStateE("");
  const list = window.MOCK_CHARS.filter(c =>
    !q.trim() || c.name.toLowerCase().includes(q.toLowerCase())
  );

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="BIBLIOTECA"
        title="Personagens reutilizáveis."
        lede="Cada personagem mantém ficha visual e personalidade. Eles podem aparecer em várias HQs sem perder a coerência."
        actions={
          <Button kind="accent" icon="plus" onClick={() => go("new")}>Novo personagem</Button>
        }
      />

      <div className="row" style={{ marginBottom: 18 }}>
        <div style={{ position: "relative", flex: 1, maxWidth: 360 }}>
          <Icon name="search" size={14} style={{
            position: "absolute", left: 12, top: "50%", transform: "translateY(-50%)",
            color: "var(--ink-3)",
          }} />
          <input className="input" placeholder="Buscar personagem…"
            style={{ paddingLeft: 34 }}
            value={q} onChange={e => setQ(e.target.value)} />
        </div>
        <div className="spacer"></div>
        <div className="row">
          <Chip active>Todos</Chip>
          <Chip>Protagonistas</Chip>
          <Chip>Coadjuvantes</Chip>
          <Chip>Mascotes</Chip>
        </div>
      </div>

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
        gap: 16,
      }}>
        {list.map(c => (
          <LibraryCard key={c.id} char={c} />
        ))}
      </div>
    </div>
  );
}

function LibraryCard({ char }) {
  return (
    <div className="card card-pad" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{
        aspectRatio: "1/1",
        background: `var(--${{F4D6D7: "blush"}[char.palette?.[0]?.replace("#","")] || "blush"}-soft)`,
        border: "1.5px solid var(--ink)",
        borderRadius: 2,
        position: "relative",
        overflow: "hidden",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          backgroundImage: "radial-gradient(circle, rgba(30,24,18,0.18) 0.6px, transparent 1px)",
          backgroundSize: "6px 6px", opacity: 0.5,
        }}></div>
        <div style={{
          position: "absolute", inset: 0, display: "grid", placeItems: "center",
        }}>
          <Avatar name={char.name} size={120} />
        </div>
        <div className="panel-meta">{char.role.toUpperCase()}</div>
      </div>
      <div>
        <div style={{ fontFamily: "var(--serif)", fontSize: 19, lineHeight: 1.1 }}>{char.name}</div>
        <div className="text-xs muted" style={{ marginTop: 2 }}>{char.age} anos · {char.height}</div>
      </div>
      <p className="text-sm" style={{ color: "var(--ink-2)", lineHeight: 1.45, margin: 0 }}>
        {char.summary}
      </p>
      <div className="row" style={{ flexWrap: "wrap", gap: 6 }}>
        {char.traits.map(t => (
          <span key={t} className="chip muted text-xs">{t}</span>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { Editor, Final, LibraryScreen });
