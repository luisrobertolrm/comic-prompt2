// src/app.jsx — top-level routing, tweaks, draft state
const { useState: useStateA, useEffect: useEffectA } = React;

const SCREEN_KEY = "sumi__screen";
const DRAFT_KEY  = "sumi__draft";
const USER_KEY   = "sumi__user";

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "paletteHex": "#E5A6A8",
  "panelStyle": "classic"
}/*EDITMODE-END*/;

const PALETTES = {
  "#E5A6A8": { name: "Blush",  accent: "#E5A6A8", soft: "#F4D6D7", ink: "#8C4A55" },
  "#E7BD8E": { name: "Pêssego", accent: "#E7BD8E", soft: "#F6DEC2", ink: "#8A5A2A" },
  "#A9CDB6": { name: "Menta",  accent: "#A9CDB6", soft: "#DBEADF", ink: "#3F6A52" },
  "#B8A9CE": { name: "Lilás",  accent: "#B8A9CE", soft: "#E1D8EC", ink: "#5C4880" },
  "#A9C0D2": { name: "Céu",    accent: "#A9C0D2", soft: "#D8E2EC", ink: "#3F6079" },
};

const PANEL_STYLES = {
  classic: { border: "1.5px solid var(--ink)", shadow: "0 1px 0 rgba(40,28,12,0.10), 4px 4px 0 rgba(40,28,12,0.08)", radius: "2px" },
  modern:  { border: "1px solid var(--ink-2)", shadow: "0 4px 16px rgba(40,28,12,0.08)", radius: "10px" },
  ink:     { border: "2.5px solid var(--ink)", shadow: "0 1px 0 var(--ink), 6px 6px 0 var(--ink)", radius: "0" },
  minimal: { border: "1px solid var(--rule)", shadow: "none", radius: "4px" },
};

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [user, setUser] = useStateA(() => {
    try { return JSON.parse(localStorage.getItem(USER_KEY)) || null; }
    catch { return null; }
  });
  const [screen, setScreen] = useStateA(() => localStorage.getItem(SCREEN_KEY) || "home");
  const [draft, setDraftState] = useStateA(() => {
    try { return JSON.parse(localStorage.getItem(DRAFT_KEY)) || {}; }
    catch { return {}; }
  });

  const go = (s) => {
    setScreen(s);
    localStorage.setItem(SCREEN_KEY, s);
  };
  const setDraft = (d) => {
    setDraftState(d);
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(d)); } catch {}
  };
  const login = (u) => {
    setUser(u);
    try { localStorage.setItem(USER_KEY, JSON.stringify(u)); } catch {}
  };
  const logout = () => {
    setUser(null);
    localStorage.removeItem(USER_KEY);
    setScreen("home");
  };

  // Apply tweaks to CSS variables
  useEffectA(() => {
    const p = PALETTES[t.paletteHex] || PALETTES["#E5A6A8"];
    document.documentElement.style.setProperty("--accent", p.accent);
    document.documentElement.style.setProperty("--accent-soft", p.soft);
    document.documentElement.style.setProperty("--accent-ink", p.ink);

    const s = PANEL_STYLES[t.panelStyle] || PANEL_STYLES.classic;
    document.documentElement.style.setProperty("--panel-border", s.border);
    document.documentElement.style.setProperty("--panel-shadow", s.shadow);
    document.documentElement.style.setProperty("--panel-radius", s.radius);
  }, [t.paletteHex, t.panelStyle]);

  // Gate: no user → auth screen (tweaks panel still mounts so theming works)
  if (!user) {
    return (
      <React.Fragment>
        <AuthScreen onAuth={login} />
        <TweaksPanel>
          <TweakSection label="Aparência" />
          <TweakColor
            label="Paleta de acento"
            value={t.paletteHex}
            options={Object.keys(PALETTES)}
            onChange={(v) => setTweak("paletteHex", v)}
          />
        </TweaksPanel>
      </React.Fragment>
    );
  }

  let body;
  switch (screen) {
    case "home":       body = <Home go={go} />; break;
    case "library":    body = <LibraryScreen go={go} />; break;
    case "new":        body = <NewProject go={go} draft={draft} setDraft={setDraft} />; break;
    case "characters": body = <CharactersScreen go={go} draft={draft} setDraft={setDraft} />; break;
    case "script":     body = <Script go={go} draft={draft} setDraft={setDraft} />; break;
    case "review":     body = <Review go={go} draft={draft} setDraft={setDraft} />; break;
    case "editor":     body = <Editor go={go} draft={draft} setDraft={setDraft} />; break;
    case "final":      body = <Final go={go} draft={draft} />; break;
    case "video":      body = <VideoScreen go={go} draft={draft} />; break;
    default:           body = <Home go={go} />;
  }

  return (
    <Shell current={screen} go={go} draft={draft} projectTitle={draft.title || "Carta de Verão"} user={user} onLogout={logout}>
      {body}
      <TweaksPanel>
        <TweakSection label="Aparência" />
        <TweakColor
          label="Paleta de acento"
          value={t.paletteHex}
          options={Object.keys(PALETTES)}
          onChange={(v) => setTweak("paletteHex", v)}
        />
        <TweakRadio
          label="Estilo de quadro"
          value={t.panelStyle}
          options={[
            { value: "classic", label: "Clássico" },
            { value: "modern",  label: "Moderno"  },
            { value: "ink",     label: "Tinta"    },
            { value: "minimal", label: "Mínimo"   },
          ]}
          onChange={(v) => setTweak("panelStyle", v)}
        />
        <TweakSection label="Protótipo" />
        <TweakButton label="Reiniciar fluxo" onClick={() => {
          localStorage.removeItem(SCREEN_KEY);
          localStorage.removeItem(DRAFT_KEY);
          setDraftState({});
          setScreen("home");
        }} />
      </TweaksPanel>
    </Shell>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
