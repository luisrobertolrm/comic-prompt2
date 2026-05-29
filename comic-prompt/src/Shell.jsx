// src/Shell.jsx — Sidebar + topbar layout
const { useState: useStateSh } = React;

function Shell({ current, go, children, draft, projectTitle, user, onLogout }) {
  const [menuOpen, setMenuOpen] = useStateSh(false);
  const u = user || { name: "Convidada", email: "", plan: "Plano criador" };
  const navItems = [
    { id: "home",    label: "Projetos",   icon: "home"   },
    { id: "library", label: "Biblioteca", icon: "book"   },
  ];

  const creationSteps = [
    { id: "new",        label: "Ideia",       icon: "spark"  },
    { id: "characters", label: "Personagens", icon: "users"  },
    { id: "script",     label: "Roteiro",     icon: "scroll" },
    { id: "review",     label: "Revisão",     icon: "eye"    },
    { id: "editor",     label: "Editor",      icon: "layout" },
    { id: "final",      label: "Finalizar",   icon: "download" },
    { id: "video",      label: "Vídeo",       icon: "film" },
  ];

  const inCreation = creationSteps.some(s => s.id === current);
  const crumbs = (() => {
    if (current === "home")    return [{ label: "Projetos" }];
    if (current === "library") return [{ label: "Biblioteca" }];
    const stepLabels = {
      new: "Nova HQ", characters: "Personagens", script: "Roteiro",
      review: "Revisão", editor: "Editor", final: "Finalizar", video: "Vídeo",
    };
    return [
      { label: "Projetos", click: () => go("home") },
      { label: projectTitle || "Carta de Verão" },
      { label: stepLabels[current] || current },
    ];
  })();

  return (
    <div className="app">
      <aside className="sidebar">
        <Brand />
        <div className="nav-section-label">Atalhos</div>
        {navItems.map(it => (
          <div key={it.id}
            className={"nav-item" + (current === it.id ? " active" : "")}
            onClick={() => go(it.id)}>
            <span className="glyph"><Icon name={it.icon} size={14} /></span>
            {it.label}
          </div>
        ))}

        <div className="nav-section-label">Em produção</div>
        <div style={{
          padding: "10px 10px 12px",
          border: "1px solid var(--rule)",
          background: "var(--paper-3)",
          borderRadius: "var(--r)",
          marginTop: 2,
        }}>
          <div className="text-xs muted" style={{ marginBottom: 6 }}>HQ ATUAL</div>
          <div style={{ fontFamily: "var(--serif)", fontSize: 15, marginBottom: 8 }}>
            {projectTitle || "Carta de Verão"}
          </div>
          <div className="col" style={{ gap: 4 }}>
            {creationSteps.map((s, i) => {
              const isCurrent = current === s.id;
              const stepIdx = creationSteps.findIndex(x => x.id === current);
              const isDone = inCreation && i < stepIdx;
              return (
                <div key={s.id}
                  className={"nav-item" + (isCurrent ? " active" : "")}
                  onClick={() => go(s.id)}
                  style={{ fontSize: 12.5, padding: "5px 8px" }}>
                  <span className="glyph" style={{
                    fontSize: 10,
                    color: isDone ? "var(--accent-ink)" : (isCurrent ? "var(--accent-ink)" : "var(--ink-3)"),
                  }}>
                    {isDone ? "✓" : i + 1}
                  </span>
                  {s.label}
                </div>
              );
            })}
          </div>
        </div>

        <div className="sidebar-foot" style={{ position: "relative" }}>
          <button
            onClick={() => setMenuOpen(o => !o)}
            style={{
              display: "flex", alignItems: "center", gap: 10,
              width: "100%", background: "transparent", border: "none",
              cursor: "pointer", padding: 0, textAlign: "left",
            }}>
            <div className="av">{(u.name || "?")[0].toUpperCase()}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ color: "var(--ink)", fontSize: 13, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{u.name}</div>
              <div style={{ fontSize: 11, color: "var(--ink-3)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {u.email || u.plan}
              </div>
            </div>
            <Icon name={menuOpen ? "back" : "arr_r"} size={14}
              style={{ color: "var(--ink-3)", transform: menuOpen ? "rotate(90deg)" : "rotate(-90deg)", flexShrink: 0 }} />
          </button>

          {menuOpen && (
            <div style={{
              position: "absolute", bottom: "calc(100% + 6px)", left: 0, right: 0,
              background: "var(--paper-3)", border: "1px solid var(--ink)",
              borderRadius: "var(--r)", boxShadow: "var(--shadow-2)",
              padding: 6, zIndex: 50,
            }}>
              <div style={{ padding: "8px 10px", borderBottom: "1px dashed var(--rule)", marginBottom: 4 }}>
                <div style={{ fontFamily: "var(--serif)", fontSize: 14 }}>{u.name}</div>
                <div className="text-xs muted">{u.email}</div>
                <div style={{
                  display: "inline-block", marginTop: 6,
                  padding: "2px 8px", background: "var(--accent-soft)",
                  border: "1px solid var(--accent)", borderRadius: 999,
                  fontFamily: "var(--mono)", fontSize: 9, letterSpacing: "0.08em",
                }}>{(u.plan || "PLANO CRIADOR").toUpperCase()}</div>
              </div>
              <MenuItem icon="users" label="Minha conta" onClick={() => setMenuOpen(false)} />
              <MenuItem icon="star" label="Assinatura" onClick={() => setMenuOpen(false)} />
              <MenuItem icon="back" label="Sair" danger onClick={() => { setMenuOpen(false); onLogout && onLogout(); }} />
            </div>
          )}
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="crumb">
            {crumbs.map((c, i) => (
              <React.Fragment key={i}>
                {i > 0 && <span className="sep">›</span>}
                {c.click ? (
                  <span onClick={c.click} style={{ cursor: "pointer" }}>{c.label}</span>
                ) : (
                  i === crumbs.length - 1 ? <b>{c.label}</b> : <span>{c.label}</span>
                )}
              </React.Fragment>
            ))}
          </div>
          <div className="grow"></div>
          <div className="topbar-actions">
            {inCreation && (
              <div className="text-xs muted hand" style={{ fontSize: 15, color: "var(--accent-ink)", whiteSpace: "nowrap", marginRight: 4 }}>
                rascunho salvo
              </div>
            )}
            <IconButton name="search" title="Buscar" />
            <IconButton name="bubble" title="Ajuda" />
            <div style={{ width: 1, height: 22, background: "var(--rule)", margin: "0 4px" }}></div>
            <button
              onClick={() => go("home")}
              title={`${u.name} · ${u.email}`}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                background: "var(--paper-3)", border: "1px solid var(--rule)",
                borderRadius: 999, padding: "4px 4px 4px 12px", cursor: "pointer",
              }}>
              <span className="text-sm" style={{ color: "var(--ink-2)", whiteSpace: "nowrap" }}>{u.name.split(" ")[0]}</span>
              <span style={{
                width: 26, height: 26, borderRadius: "50%",
                background: "var(--accent-soft)", border: "1px solid var(--ink)",
                display: "grid", placeItems: "center",
                fontFamily: "var(--serif)", fontSize: 13, color: "var(--ink)",
              }}>{(u.name || "?")[0].toUpperCase()}</span>
            </button>
          </div>
        </header>
        <div className="content">{children}</div>
      </main>
    </div>
  );
}

function MenuItem({ icon, label, onClick, danger }) {
  return (
    <button onClick={onClick}
      style={{
        display: "flex", alignItems: "center", gap: 10,
        width: "100%", padding: "8px 10px",
        background: "transparent", border: "none", cursor: "pointer",
        borderRadius: "var(--r-sm)", textAlign: "left",
        color: danger ? "#a8503f" : "var(--ink-2)", fontSize: 13,
      }}
      onMouseEnter={e => e.currentTarget.style.background = "rgba(0,0,0,0.04)"}
      onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
      <Icon name={icon} size={14} style={danger ? { transform: "rotate(180deg)" } : undefined} />
      {label}
    </button>
  );
}

Object.assign(window, { Shell });