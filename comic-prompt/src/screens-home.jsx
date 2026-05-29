// src/screens-home.jsx — Home (projects list) + Library (characters)
const { useState: useStateH, useMemo: useMemoH } = React;

function Home({ go }) {
  const [view, setView] = useStateH("grid");
  const [filter, setFilter] = useStateH("Todos");
  const projects = window.MOCK_PROJECTS;
  const filtered = projects.filter(p =>
    filter === "Todos" ? true : p.status === filter
  );
  const statuses = ["Todos", "Rascunho", "Roteiro", "Em revisão", "Concluído"];

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="SEUS PROJETOS"
        title="Onde sua próxima história começa."
        lede="Continue um capítulo em andamento ou inicie uma nova HQ. A IA vai te guiar pelo roteiro, propor os quadros e manter a coerência visual."
        actions={
          <Button kind="accent" icon="plus" onClick={() => go("new")} style={{ whiteSpace: "nowrap" }}>
            Nova HQ
          </Button>
        }
      />

      {/* Filters */}
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 18 }}>
        <div className="row" style={{ flexWrap: "wrap" }}>
          {statuses.map(s => (
            <Chip key={s} active={filter === s} onClick={() => setFilter(s)}>{s}</Chip>
          ))}
        </div>
        <div className="row">
          <IconButton name={view === "grid" ? "list" : "grid"}
                      title="Alternar visualização"
                      onClick={() => setView(view === "grid" ? "list" : "grid")} />
        </div>
      </div>

      {view === "grid"
        ? <ProjectGrid projects={filtered} go={go} />
        : <ProjectList projects={filtered} go={go} />}

      <div style={{ marginTop: 40 }}>
        <div className="section-eyebrow" style={{ marginBottom: 14 }}>BIBLIOTECA — PERSONAGENS RECENTES</div>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))",
          gap: 12,
        }}>
          {window.MOCK_CHARS.map(c => (
            <CharacterMiniCard key={c.id} char={c} />
          ))}
          <button className="card card-pad"
            style={{
              border: "1px dashed var(--rule)",
              background: "var(--paper-2)",
              color: "var(--ink-3)",
              display: "grid", placeItems: "center",
              cursor: "pointer", minHeight: 130,
            }}
            onClick={() => go("library")}>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 22, marginBottom: 4 }}>+</div>
              <div style={{ fontSize: 12 }}>Ver biblioteca completa</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

function ProjectGrid({ projects, go }) {
  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
      gap: 18,
    }}>
      {projects.map(p => <ProjectCard key={p.id} project={p} go={go} />)}
      <NewProjectTile go={go} />
    </div>
  );
}

function NewProjectTile({ go }) {
  return (
    <button onClick={() => go("new")}
      style={{
        border: "1.5px dashed var(--ink-4)",
        borderRadius: "var(--r-lg)",
        background: "var(--paper-2)",
        padding: 22,
        cursor: "pointer",
        textAlign: "left",
        display: "flex", flexDirection: "column", gap: 12,
        minHeight: 310,
      }}>
      <div style={{
        aspectRatio: "4/3",
        background: "var(--paper-3)",
        border: "1.5px solid var(--ink-4)",
        borderStyle: "dashed",
        display: "grid", placeItems: "center",
        color: "var(--ink-3)",
        fontFamily: "var(--mono)", fontSize: 11,
        letterSpacing: "0.15em",
      }}>
        PÁGINA EM BRANCO
      </div>
      <div>
        <h3 style={{ fontSize: 18, marginBottom: 4 }}>Começar uma nova história</h3>
        <div className="muted text-sm">Diga uma ideia. A IA propõe o roteiro.</div>
      </div>
    </button>
  );
}

function ProjectCard({ project, go }) {
  const accent = `var(--${project.cover.accent})`;
  const accentSoft = `var(--${project.cover.accent}-soft)`;
  const chars = project.chars.map(id => window.MOCK_CHARS.find(c => c.id === id)).filter(Boolean);
  return (
    <div className="card card-pad"
      style={{ display: "flex", flexDirection: "column", gap: 14, cursor: "pointer" }}
      onClick={() => go("review")}>
      {/* Cover plate */}
      <div style={{
        position: "relative",
        aspectRatio: "4/3",
        background: accentSoft,
        border: "1.5px solid var(--ink)",
        borderRadius: 2,
        overflow: "hidden",
        boxShadow: "var(--panel-shadow)",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          backgroundImage: project.cover.tone === "diag"
            ? "repeating-linear-gradient(45deg, rgba(30,24,18,0.18) 0 1px, transparent 1px 6px)"
            : project.cover.tone === "dense"
            ? "radial-gradient(circle, rgba(30,24,18,0.22) 0.7px, transparent 1px)"
            : "radial-gradient(circle, rgba(30,24,18,0.18) 0.6px, transparent 1px)",
          backgroundSize: project.cover.tone === "dense" ? "5px 5px" : "7px 7px",
          opacity: 0.55,
        }}></div>
        <div style={{
          position: "absolute", left: 10, top: 10,
          padding: "3px 8px", border: "1px solid var(--ink)",
          background: "var(--paper-3)", fontFamily: "var(--mono)",
          fontSize: 10, letterSpacing: "0.1em",
        }}>{project.genre.toUpperCase()}</div>
        <div style={{
          position: "absolute", right: 10, top: 10,
          padding: "3px 8px", background: accent, fontFamily: "var(--mono)",
          fontSize: 10, letterSpacing: "0.1em",
          border: "1px solid var(--ink)",
        }}>{project.pages} pg</div>
        <h2 style={{
          position: "absolute", left: 14, right: 14, bottom: 12,
          fontSize: 22, color: "var(--ink)", lineHeight: 1.05,
          textShadow: "0 1px 0 var(--paper-3)",
        }}>{project.title}</h2>
      </div>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div className="col" style={{ gap: 2 }}>
          <div className="text-sm">{project.subtitle}</div>
          <div className="text-xs muted">{project.status} · {project.updated}</div>
        </div>
        <div style={{ display: "flex" }}>
          {chars.slice(0, 3).map((c, i) => (
            <div key={c.id} style={{ marginLeft: i === 0 ? 0 : -8 }}>
              <Avatar name={c.name} size={26} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ProjectList({ projects, go }) {
  return (
    <div className="card" style={{ padding: 0, overflow: "hidden" }}>
      {projects.map((p, i) => {
        const chars = p.chars.map(id => window.MOCK_CHARS.find(c => c.id === id)).filter(Boolean);
        return (
          <div key={p.id}
            onClick={() => go("review")}
            style={{
              display: "grid",
              gridTemplateColumns: "60px 1fr 160px 120px 120px 40px",
              gap: 14, alignItems: "center",
              padding: "14px 18px",
              borderTop: i === 0 ? "none" : "1px solid var(--rule)",
              cursor: "pointer",
            }}>
            <div style={{
              width: 50, height: 50, borderRadius: 2,
              background: `var(--${p.cover.accent}-soft)`,
              border: "1.5px solid var(--ink)",
            }}></div>
            <div>
              <div style={{ fontFamily: "var(--serif)", fontSize: 17 }}>{p.title}</div>
              <div className="text-xs muted">{p.subtitle}</div>
            </div>
            <div className="text-sm">{p.genre}</div>
            <div className="text-sm muted">{p.status}</div>
            <div style={{ display: "flex" }}>
              {chars.slice(0, 3).map((c, i) => (
                <div key={c.id} style={{ marginLeft: i === 0 ? 0 : -8 }}>
                  <Avatar name={c.name} size={24} />
                </div>
              ))}
            </div>
            <Icon name="arr_r" size={16} style={{ color: "var(--ink-3)" }} />
          </div>
        );
      })}
    </div>
  );
}

function CharacterMiniCard({ char }) {
  return (
    <div className="card card-pad" style={{ display: "flex", gap: 12, alignItems: "center" }}>
      <Avatar name={char.name} size={44} />
      <div style={{ minWidth: 0 }}>
        <div style={{ fontFamily: "var(--serif)", fontSize: 15, lineHeight: 1.1 }}>{char.name}</div>
        <div className="text-xs muted" style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{char.role}</div>
      </div>
    </div>
  );
}

Object.assign(window, { Home, ProjectCard, CharacterMiniCard });
