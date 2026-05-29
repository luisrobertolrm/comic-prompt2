// src/screens-auth.jsx — Login / Register split screen
const { useState: useStateAu } = React;

function AuthScreen({ onAuth }) {
  const [mode, setMode] = useStateAu("login"); // login | register
  const [form, setForm] = useStateAu({
    name: "", email: "", password: "", confirm: "", remember: true, terms: false,
  });
  const [errors, setErrors] = useStateAu({});
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const submit = (e) => {
    e.preventDefault();
    const er = {};
    if (mode === "register" && !form.name.trim()) er.name = "Como devemos te chamar?";
    if (!/^\S+@\S+\.\S+$/.test(form.email)) er.email = "E-mail inválido.";
    if (form.password.length < 6) er.password = "Mínimo de 6 caracteres.";
    if (mode === "register" && form.password !== form.confirm) er.confirm = "As senhas não conferem.";
    if (mode === "register" && !form.terms) er.terms = "Aceite os termos para continuar.";
    setErrors(er);
    if (Object.keys(er).length) return;

    const name = mode === "register"
      ? form.name.trim()
      : form.email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    onAuth({
      name,
      email: form.email.trim(),
      plan: "Plano criador",
    });
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "grid",
      gridTemplateColumns: "1.05fr 0.95fr",
    }}>
      {/* ── Left: brand / hero ── */}
      <div style={{
        position: "relative",
        background: "var(--accent-soft)",
        borderRight: "1.5px solid var(--ink)",
        padding: "48px 56px",
        display: "flex", flexDirection: "column",
        overflow: "hidden",
      }}>
        <div style={{
          position: "absolute", inset: 0,
          backgroundImage: "radial-gradient(circle, rgba(30,24,18,0.16) 0.7px, transparent 1px)",
          backgroundSize: "8px 8px", opacity: 0.5,
        }}></div>

        <div style={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", height: "100%" }}>
          <div className="brand" style={{ padding: 0 }}>
            <div className="brand-mark" style={{ width: 38, height: 38, fontSize: 22 }}>墨</div>
            <div className="brand-name" style={{ fontSize: 24 }}>Sumi</div>
          </div>

          <div style={{ margin: "auto 0", maxWidth: 460 }}>
            <div className="section-eyebrow" style={{ marginBottom: 14 }}>ESTÚDIO DE HQ COM IA</div>
            <h1 style={{ fontSize: 46, lineHeight: 1.05, marginBottom: 18 }}>
              Da primeira faísca à página pronta.
            </h1>
            <p style={{ fontSize: 16, color: "var(--ink-2)", lineHeight: 1.6, maxWidth: "42ch" }}>
              Dê uma ideia, crie seus personagens, e deixe a IA propor o roteiro,
              os quadros e a narração. Você aprova cada passo.
            </p>

            {/* Mini panel decoration */}
            <div style={{ display: "flex", gap: 12, marginTop: 36 }}>
              {[
                { t: "dots", c: "Yumi" },
                { t: "diag", c: "Ren" },
                { t: "dense", c: null },
              ].map((d, i) => (
                <div key={i} style={{
                  width: 92, aspectRatio: "3/4",
                  background: "var(--paper-3)",
                  border: "1.5px solid var(--ink)",
                  boxShadow: "3px 3px 0 rgba(40,28,12,0.12)",
                  position: "relative", overflow: "hidden",
                  transform: `rotate(${(i - 1) * 3}deg)`,
                }}>
                  <div style={{
                    position: "absolute", inset: 0,
                    backgroundImage: d.t === "diag"
                      ? "repeating-linear-gradient(45deg, rgba(30,24,18,0.18) 0 1px, transparent 1px 6px)"
                      : d.t === "dense"
                      ? "radial-gradient(circle, rgba(30,24,18,0.22) 0.7px, transparent 1px)"
                      : "radial-gradient(circle, rgba(30,24,18,0.18) 0.6px, transparent 1px)",
                    backgroundSize: d.t === "dense" ? "4px 4px" : "6px 6px",
                    opacity: 0.5,
                  }}></div>
                  {d.c && (
                    <div style={{
                      position: "absolute", left: "50%", top: "52%", transform: "translate(-50%,-50%)",
                      width: 40, height: 40, borderRadius: "50%",
                      background: toneFor(d.c)[1], border: "1px solid var(--ink)",
                      display: "grid", placeItems: "center", fontFamily: "var(--serif)", fontSize: 18,
                    }}>{d.c[0]}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="text-xs muted" style={{ position: "relative", zIndex: 1 }}>
            © 2026 Sumi Studio · feito para criadores de mangá
          </div>
        </div>
      </div>

      {/* ── Right: form ── */}
      <div style={{
        display: "flex", flexDirection: "column",
        justifyContent: "center",
        padding: "48px 56px",
        background: "var(--paper)",
      }}>
        <div style={{ width: "100%", maxWidth: 380, margin: "0 auto" }}>
          {/* Tabs */}
          <div className="row" style={{ gap: 0, marginBottom: 28, background: "var(--paper-2)", border: "1px solid var(--rule)", padding: 4, borderRadius: 999 }}>
            {[
              { id: "login", label: "Entrar" },
              { id: "register", label: "Criar conta" },
            ].map(m => (
              <button key={m.id} onClick={() => { setMode(m.id); setErrors({}); }}
                style={{
                  flex: 1, padding: "9px 12px",
                  background: mode === m.id ? "var(--paper-3)" : "transparent",
                  border: mode === m.id ? "1px solid var(--ink)" : "1px solid transparent",
                  borderRadius: 999,
                  fontWeight: mode === m.id ? 600 : 400,
                  fontSize: 14, cursor: "pointer", color: "var(--ink)",
                }}>{m.label}</button>
            ))}
          </div>

          <h2 style={{ fontSize: 28, marginBottom: 6 }}>
            {mode === "login" ? "Bem-vinda de volta." : "Crie sua conta."}
          </h2>
          <p className="muted text-sm" style={{ marginBottom: 24 }}>
            {mode === "login"
              ? "Continue de onde parou no seu estúdio."
              : "Leva menos de um minuto — e o primeiro projeto é grátis."}
          </p>

          <form onSubmit={submit} className="col" style={{ gap: 16 }}>
            {mode === "register" && (
              <AuthField label="Nome" error={errors.name}>
                <input className="input" value={form.name} autoComplete="name"
                  placeholder="Seu nome ou pseudônimo"
                  onChange={e => set("name", e.target.value)} />
              </AuthField>
            )}

            <AuthField label="E-mail" error={errors.email}>
              <input className="input" type="email" value={form.email} autoComplete="email"
                placeholder="voce@exemplo.com"
                onChange={e => set("email", e.target.value)} />
            </AuthField>

            <AuthField label="Senha" error={errors.password}>
              <input className="input" type="password" value={form.password}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                placeholder="••••••••"
                onChange={e => set("password", e.target.value)} />
            </AuthField>

            {mode === "register" && (
              <AuthField label="Confirmar senha" error={errors.confirm}>
                <input className="input" type="password" value={form.confirm}
                  autoComplete="new-password" placeholder="••••••••"
                  onChange={e => set("confirm", e.target.value)} />
              </AuthField>
            )}

            {/* Options row */}
            {mode === "login" ? (
              <div className="row" style={{ justifyContent: "space-between" }}>
                <label className="row" style={{ gap: 8, cursor: "pointer" }}>
                  <Checkbox on={form.remember} onClick={() => set("remember", !form.remember)} />
                  <span className="text-sm">Lembrar de mim</span>
                </label>
                <a href="#" className="text-sm" style={{ color: "var(--accent-ink)", textDecoration: "none" }}
                  onClick={e => e.preventDefault()}>Esqueceu a senha?</a>
              </div>
            ) : (
              <div>
                <label className="row" style={{ gap: 8, cursor: "pointer", alignItems: "flex-start" }}>
                  <Checkbox on={form.terms} onClick={() => set("terms", !form.terms)} />
                  <span className="text-sm" style={{ lineHeight: 1.4 }}>
                    Li e aceito os <a href="#" style={{ color: "var(--accent-ink)" }} onClick={e => e.preventDefault()}>Termos</a> e a <a href="#" style={{ color: "var(--accent-ink)" }} onClick={e => e.preventDefault()}>Política de Privacidade</a>.
                  </span>
                </label>
                {errors.terms && <div style={{ color: "#b3503f", fontSize: 11.5, marginTop: 4 }}>{errors.terms}</div>}
              </div>
            )}

            <Button kind="primary" size="lg" type="submit"
              style={{ width: "100%", justifyContent: "center", marginTop: 4 }}>
              {mode === "login" ? "Entrar no estúdio" : "Criar conta e começar"}
            </Button>
          </form>

          {/* Divider */}
          <div className="row" style={{ margin: "22px 0", gap: 12 }}>
            <div className="divider" style={{ flex: 1 }}></div>
            <span className="text-xs muted">ou continue com</span>
            <div className="divider" style={{ flex: 1 }}></div>
          </div>

          <div className="row" style={{ gap: 10 }}>
            <button className="btn" style={{ flex: 1, justifyContent: "center" }}
              onClick={() => onAuth({ name: "Maya Tanaka", email: "maya@gmail.com", plan: "Plano criador" })}>
              <GoogleG /> Google
            </button>
            <button className="btn" style={{ flex: 1, justifyContent: "center" }}
              onClick={() => onAuth({ name: "Maya Tanaka", email: "maya@exemplo.com", plan: "Plano criador" })}>
              <Icon name="users" size={15} /> Convidado
            </button>
          </div>

          <div className="text-xs muted" style={{ textAlign: "center", marginTop: 22 }}>
            {mode === "login"
              ? <>Ainda não tem conta? <a href="#" style={{ color: "var(--accent-ink)" }} onClick={e => { e.preventDefault(); setMode("register"); }}>Crie agora</a></>
              : <>Já tem conta? <a href="#" style={{ color: "var(--accent-ink)" }} onClick={e => { e.preventDefault(); setMode("login"); }}>Entrar</a></>}
          </div>
        </div>
      </div>
    </div>
  );
}

function AuthField({ label, error, children }) {
  return (
    <div className="field">
      <label className="field-label">{label}</label>
      {children}
      {error && <div style={{ color: "#b3503f", fontSize: 11.5 }}>{error}</div>}
    </div>
  );
}

function Checkbox({ on, onClick }) {
  return (
    <button type="button" onClick={onClick}
      style={{
        width: 18, height: 18, flexShrink: 0,
        borderRadius: 4, border: "1.5px solid var(--ink)",
        background: on ? "var(--accent)" : "var(--paper-3)",
        display: "grid", placeItems: "center", cursor: "pointer", padding: 0,
        marginTop: 1,
      }}>
      {on && <Icon name="check" size={11} stroke={3} />}
    </button>
  );
}

function GoogleG() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M23 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.2a5.3 5.3 0 0 1-2.3 3.5v2.9h3.7c2.2-2 3.4-5 3.4-8.6z"/>
      <path fill="#34A853" d="M12 24c3.1 0 5.7-1 7.6-2.8l-3.7-2.9c-1 .7-2.3 1.1-3.9 1.1-3 0-5.5-2-6.4-4.7H1.8v3C3.7 21.4 7.6 24 12 24z"/>
      <path fill="#FBBC05" d="M5.6 14.7c-.2-.7-.4-1.4-.4-2.2s.1-1.5.4-2.2v-3H1.8A12 12 0 0 0 0 12.5c0 1.9.5 3.7 1.8 5.2l3.8-3z"/>
      <path fill="#EA4335" d="M12 4.8c1.7 0 3.2.6 4.4 1.7l3.3-3.3C17.7 1.2 15.1 0 12 0 7.6 0 3.7 2.6 1.8 6.3l3.8 3C6.5 6.7 9 4.8 12 4.8z"/>
    </svg>
  );
}

Object.assign(window, { AuthScreen });
