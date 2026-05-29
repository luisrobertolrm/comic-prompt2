// src/ui.jsx — primitives & shared components
// Exports to window: Icon, Button, IconButton, Field, Chip, Card, Avatar,
//   MangaPanel, SpeechBubble, Stepper, PageHead, Brand, EmptyHint

const { useState, useEffect, useRef, useMemo, Fragment } = React;

/* ── Icons (minimal line set, hand-drawn feel) ─────────────────────── */
const ICONS = {
  home:    "M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1z",
  book:    "M4 4h7a3 3 0 0 1 3 3v13M20 4h-3a3 3 0 0 0-3 3v13M4 4v15h7M20 4v15h-6",
  users:   "M16 11a4 4 0 1 0-8 0 4 4 0 0 0 8 0zM3 21v-1a6 6 0 0 1 6-6h6a6 6 0 0 1 6 6v1",
  spark:   "M12 3l1.8 4.7L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.3L12 3zM19 14l.9 2.3L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.7L19 14zM5 14l.7 1.8L7 16l-1.3.6L5 18l-.7-1.4L3 16l1.3-.2L5 14z",
  edit:    "M4 20h4l10-10-4-4L4 16v4zM14 6l4 4",
  layout:  "M3 4h18v6H3zM3 12h8v8H3zM13 12h8v8h-8z",
  check:   "M5 12l4 4 10-10",
  x:       "M6 6l12 12M6 18L18 6",
  plus:    "M12 5v14M5 12h14",
  arr_r:   "M5 12h14M13 6l6 6-6 6",
  arr_l:   "M19 12H5M11 6l-6 6 6 6",
  search:  "M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zM21 21l-4.3-4.3",
  refresh: "M3 12a9 9 0 0 1 15-6.7L21 8M21 3v5h-5M21 12a9 9 0 0 1-15 6.7L3 16M3 21v-5h5",
  trash:   "M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6",
  move:    "M5 9l-3 3 3 3M9 5l3-3 3 3M15 19l-3 3-3-3M19 9l3 3-3 3M2 12h20M12 2v20",
  download:"M12 4v12m0 0l-4-4m4 4l4-4M5 20h14",
  eye:     "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z",
  wand:    "M15 4l5 5M3 21l11-11 5 5L8 26 3 21zM18 2l1 2 2 1-2 1-1 2-1-2-2-1 2-1 1-2z",
  grid:    "M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z",
  list:    "M4 6h16M4 12h16M4 18h16",
  back:    "M15 6l-6 6 6 6",
  send:    "M4 20l17-8L4 4l3 8-3 8z",
  filter:  "M3 5h18l-7 9v6l-4-2v-4L3 5z",
  bubble:  "M21 12a8 8 0 1 1-3.4-6.5L21 4l-1.2 3.7A8 8 0 0 1 21 12z",
  star:    "M12 3l2.6 6.3 6.4.5-5 4.3 1.6 6.5L12 17l-5.6 3.6L8 14.1l-5-4.3 6.4-.5L12 3z",
  scroll:  "M4 4h12a3 3 0 0 1 3 3v10a3 3 0 0 0 3 3H8a3 3 0 0 1-3-3V4z",
  tag:     "M3 11l8-8 9 1 1 9-8 8-10-10zM7 7a1.5 1.5 0 1 0 0 .01z",
  play:    "M7 4l13 8-13 8z",
  pause:   "M8 5v14M16 5v14",
  film:    "M4 4h16v16H4zM4 9h16M4 15h16M9 4v16M15 4v16",
  volume:  "M4 9v6h4l5 4V5L8 9H4zM17 8a5 5 0 0 1 0 8",
  mute:    "M4 9v6h4l5 4V5L8 9H4zM18 9l4 6M22 9l-4 6",
  mic:     "M12 3a3 3 0 0 1 3 3v5a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3zM5 11a7 7 0 0 0 14 0M12 18v3",
  skip_back:"M19 5v14l-10-7zM7 5v14",
  skip_fwd: "M5 5v14l10-7zM17 5v14",
  music:   "M9 18V6l10-2v12M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0zM19 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0z",
};
function Icon({ name, size = 16, stroke = 1.6, style }) {
  const d = ICONS[name];
  if (!d) return null;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth={stroke}
         strokeLinecap="round" strokeLinejoin="round" style={style}>
      <path d={d}></path>
    </svg>
  );
}

/* ── Button ──────────────────────────────────────────────────────── */
function Button({ kind = "default", size = "md", icon, iconRight, children, onClick, type, disabled, style }) {
  const cls = ["btn"];
  if (kind === "primary") cls.push("btn-primary");
  if (kind === "accent")  cls.push("btn-accent");
  if (kind === "ghost")   cls.push("btn-ghost");
  if (size === "sm")      cls.push("btn-sm");
  if (size === "lg")      cls.push("btn-lg");
  return (
    <button className={cls.join(" ")} onClick={onClick} type={type} disabled={disabled} style={style}>
      {icon && <Icon name={icon} size={size === "sm" ? 13 : 15} />}
      {children}
      {iconRight && <Icon name={iconRight} size={size === "sm" ? 13 : 15} />}
    </button>
  );
}

function IconButton({ name, onClick, title, size = 16, style }) {
  return (
    <button className="icon-btn" onClick={onClick} title={title} style={style}>
      <Icon name={name} size={size} />
    </button>
  );
}

/* ── Field ───────────────────────────────────────────────────────── */
function Field({ label, hint, children, style }) {
  return (
    <div className="field" style={style}>
      {label && <label className="field-label">{label}</label>}
      {children}
      {hint && <div className="field-hint">{hint}</div>}
    </div>
  );
}

/* ── Chip ────────────────────────────────────────────────────────── */
function Chip({ active, onClick, children, muted, style }) {
  return (
    <span
      className={"chip" + (active ? " active" : "") + (muted ? " muted" : "")}
      onClick={onClick}
      style={style}
    >
      {children}
    </span>
  );
}

/* ── Card ────────────────────────────────────────────────────────── */
function Card({ children, pad = true, style }) {
  return (
    <div className={"card" + (pad ? " card-pad" : "")} style={style}>
      {children}
    </div>
  );
}

/* ── Avatar (manga-style placeholder) ────────────────────────────── */
const TONE_PALETTES = [
  ["#F4D6D7", "#E5A6A8"], // blush
  ["#F6DEC2", "#E7BD8E"], // peach
  ["#DBEADF", "#A9CDB6"], // mint
  ["#E1D8EC", "#B8A9CE"], // lilac
  ["#D8E2EC", "#A9C0D2"], // sky
];
function toneFor(seed) {
  const s = String(seed || "");
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return TONE_PALETTES[h % TONE_PALETTES.length];
}
function Avatar({ name, size = 40, art = true, style }) {
  const [bg] = toneFor(name);
  const initial = (name || "?").trim()[0]?.toUpperCase() || "?";
  return (
    <div className="avatar"
         style={{ width: size, height: size, background: bg, fontSize: size, ...style }}>
      {art && <div className="av-art"></div>}
      <span className="av-initial">{initial}</span>
    </div>
  );
}

/* ── Manga panel placeholder ─────────────────────────────────────── */
function MangaPanel({
  index, label, caption, aspect = "4-3", tone = "dots",
  bubbles = [], sfx, character, style
}) {
  const aspectCls = aspect === "3-4" ? "tall" : aspect === "16-9" ? "wide" : aspect === "1-1" ? "square" : "";
  const toneCls = tone === "dense" ? "dense" : tone === "diag" ? "diag" : "";
  return (
    <div className={"panel " + aspectCls} style={style}>
      {/* Background tone */}
      <div className={"panel-art " + toneCls}></div>

      {/* Character silhouette placeholder (very simple, no representational art) */}
      {character && <PanelCharacter name={character} />}

      {/* Speech bubbles */}
      {bubbles.map((b, i) => (
        <SpeechBubble key={i} {...b} />
      ))}

      {/* SFX */}
      {sfx && <span className="sfx" style={{ top: sfx.top, left: sfx.left, right: sfx.right, fontSize: sfx.size || 32 }}>{sfx.text}</span>}

      {/* Meta tag */}
      {index != null && (
        <div className="panel-meta">PANEL · {String(index).padStart(2, "0")}{label ? " · " + label : ""}</div>
      )}

      {/* Director caption */}
      {caption && <div className="panel-caption">{caption}</div>}
    </div>
  );
}

function PanelCharacter({ name }) {
  // Just a soft halo and an initial bubble — keeps placeholder honest.
  const [bg, accent] = toneFor(name);
  return (
    <div style={{
      position: "absolute",
      left: "50%", top: "55%",
      transform: "translate(-50%, -50%)",
      display: "flex", flexDirection: "column",
      alignItems: "center", gap: 6,
    }}>
      <div style={{
        width: 86, height: 86, borderRadius: "50%",
        background: `radial-gradient(circle at 35% 35%, ${bg} 0%, ${accent} 100%)`,
        border: "1.5px solid var(--ink)",
        display: "grid", placeItems: "center",
        fontFamily: "var(--serif)", fontSize: 38, color: "var(--ink)",
        position: "relative",
      }}>
        {(name || "?")[0]}
      </div>
      <div style={{
        fontFamily: "var(--mono)", fontSize: 10,
        color: "var(--ink-3)", background: "var(--paper-3)",
        padding: "2px 6px", border: "1px solid var(--rule)",
      }}>{name}</div>
    </div>
  );
}

function SpeechBubble({ text, kind = "say", x = 50, y = 12, side = "left", width }) {
  const cls = "bubble" + (kind === "thought" ? " thought" : kind === "shout" ? " shout" : "") + (side === "right" ? " right" : "");
  return (
    <div className={cls} style={{ left: side === "right" ? "auto" : x + "%", right: side === "right" ? x + "%" : "auto", top: y + "%", maxWidth: width || "58%" }}>
      {text}
    </div>
  );
}

/* ── Stepper ─────────────────────────────────────────────────────── */
function Stepper({ steps, current, onJump }) {
  return (
    <div className="stepper">
      {steps.map((s, i) => (
        <Fragment key={s.key}>
          <div
            className={"step" + (i === current ? " active" : "") + (i < current ? " done" : "")}
            onClick={() => onJump && onJump(i)}
          >
            <span className="n">{i < current ? "✓" : i + 1}</span>
            <span>{s.label}</span>
          </div>
          {i < steps.length - 1 && <span className="arr">›</span>}
        </Fragment>
      ))}
    </div>
  );
}

/* ── Page head ───────────────────────────────────────────────────── */
function PageHead({ eyebrow, title, lede, actions }) {
  return (
    <div className="page-head">
      <div>
        {eyebrow && <div className="section-eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {lede && <p className="lede">{lede}</p>}
      </div>
      {actions && <div className="row" style={{ gap: 8, flexShrink: 0 }}>{actions}</div>}
    </div>
  );
}

/* ── Brand ───────────────────────────────────────────────────────── */
function Brand() {
  return (
    <div className="brand">
      <div className="brand-mark">墨</div>
      <div className="brand-name">Sumi</div>
    </div>
  );
}

/* ── Empty hint ──────────────────────────────────────────────────── */
function EmptyHint({ children }) {
  return (
    <div style={{
      border: "1px dashed var(--rule)",
      background: "var(--paper-2)",
      borderRadius: "var(--r)",
      padding: 28,
      textAlign: "center",
      color: "var(--ink-3)",
      fontSize: 13,
    }}>{children}</div>
  );
}

Object.assign(window, {
  Icon, Button, IconButton, Field, Chip, Card, Avatar, MangaPanel,
  SpeechBubble, PanelCharacter, Stepper, PageHead, Brand, EmptyHint,
  toneFor,
});
