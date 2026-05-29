// src/screens-video.jsx — Motion-comic / video reader
// Each panel becomes a "scene"; narration + per-character voices play in sequence.
const { useState: useStateV, useEffect: useEffectV, useMemo: useMemoV, useRef: useRefV } = React;

const VOICE_OPTIONS = [
  "Narração suave", "Jovem feminina", "Jovem masculina",
  "Grave e calma", "Doce", "Energética", "Misteriosa", "Madura",
];

function fmt(t) {
  const s = Math.max(0, Math.floor(t));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function buildBeats(panels) {
  const beats = [];
  panels.forEach((p, si) => {
    // 1) narrator describes the scene
    if (p.caption && p.caption.trim()) {
      beats.push({ sceneIdx: si, speaker: "Narrador", kind: "narration", text: p.caption });
    }
    // 2) each bubble is spoken by the scene's character
    (p.bubbles || []).forEach(b => {
      beats.push({
        sceneIdx: si,
        speaker: p.character || "Narrador",
        kind: b.kind || "say",
        text: b.text,
      });
    });
    // 3) if nothing, at least show the panel for a beat
    if (!p.caption && (!p.bubbles || p.bubbles.length === 0)) {
      beats.push({ sceneIdx: si, speaker: "—", kind: "silent", text: "" });
    }
  });
  // durations + start times
  let acc = 0;
  beats.forEach(b => {
    const words = (b.text || "").trim().split(/\s+/).filter(Boolean).length;
    const dur = Math.min(6, Math.max(b.kind === "silent" ? 1.6 : 2.0, words * 0.42));
    b.dur = dur;
    b.start = acc;
    acc += dur;
  });
  return { beats, total: acc };
}

function VideoScreen({ go, draft }) {
  const panels = (draft.panels && draft.panels.length ? draft.panels : window.MOCK_PANELS);
  const { beats, total } = useMemoV(() => buildBeats(panels), [panels]);

  const [t, setT] = useStateV(0);
  const [playing, setPlaying] = useStateV(false);
  const [showBubbles, setShowBubbles] = useStateV(true);
  const [transition, setTransition] = useStateV("fade");
  const [speed, setSpeed] = useStateV(1);
  const [music, setMusic] = useStateV(true);

  // voice cast
  const castNames = useMemoV(() => {
    const set = ["Narrador"];
    panels.forEach(p => { if (p.character && !set.includes(p.character)) set.push(p.character); });
    return set;
  }, [panels]);
  const [voices, setVoices] = useStateV(() => {
    const m = {};
    castNames.forEach((n, i) => {
      m[n] = { voice: n === "Narrador" ? "Narração suave" : VOICE_OPTIONS[(i + 1) % VOICE_OPTIONS.length], muted: false };
    });
    return m;
  });

  // playback tick
  useEffectV(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setT(prev => {
        const nt = prev + 0.07 * speed;
        if (nt >= total) { setPlaying(false); return total; }
        return nt;
      });
    }, 70);
    return () => clearInterval(id);
  }, [playing, speed, total]);

  // current beat / scene
  let beatIdx = 0;
  for (let i = 0; i < beats.length; i++) if (beats[i].start <= t + 0.0001) beatIdx = i;
  const beat = beats[beatIdx] || beats[0];
  const sceneIdx = beat ? beat.sceneIdx : 0;
  const scene = panels[sceneIdx];

  const togglePlay = () => {
    if (t >= total) setT(0);
    setPlaying(p => !p);
  };
  const jumpScene = (dir) => {
    const target = sceneIdx + dir;
    const b = beats.find(x => x.sceneIdx === target);
    if (b) { setT(b.start + 0.001); }
  };
  const jumpToScene = (si) => {
    const b = beats.find(x => x.sceneIdx === si);
    if (b) setT(b.start + 0.001);
  };

  const curVoice = voices[beat?.speaker] || { voice: "—", muted: false };

  return (
    <div className="screen-enter">
      <PageHead
        eyebrow="SAÍDA EM VÍDEO — MOTION COMIC"
        title="Sua HQ, narrada cena a cena."
        lede="Não é uma animação fluida: é a própria HQ em vídeo — cada quadro vira uma cena com narração e vozes por personagem. Você decide se os balões aparecem."
        actions={
          <div className="row">
            <Button kind="ghost" onClick={() => go("final")}>Voltar</Button>
            <Button kind="primary" icon="download">Exportar vídeo</Button>
          </div>
        }
      />

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.5fr) 320px", gap: 24, alignItems: "start" }}>
        {/* ── Player ── */}
        <div>
          <VideoStage
            scene={scene}
            sceneIdx={sceneIdx}
            showBubbles={showBubbles}
            transition={transition}
            playing={playing}
            beat={beat}
            voice={curVoice}
          />

          {/* Subtitle / narration bar */}
          <NarrationBar beat={beat} voice={curVoice} playing={playing} />

          {/* Transport */}
          <Transport
            playing={playing} t={t} total={total}
            onPlay={togglePlay}
            onPrev={() => jumpScene(-1)}
            onNext={() => jumpScene(1)}
            onSeek={setT}
            speed={speed} onSpeed={setSpeed}
          />

          {/* Scene timeline */}
          <SceneTimeline
            panels={panels} beats={beats} total={total} t={t}
            current={sceneIdx} onPick={jumpToScene}
          />
        </div>

        {/* ── Side controls ── */}
        <div className="col" style={{ gap: 14 }}>
          {/* Voice cast */}
          <Card>
            <div className="row" style={{ justifyContent: "space-between", marginBottom: 12 }}>
              <div className="section-eyebrow">ELENCO DE VOZ</div>
              <Icon name="mic" size={14} style={{ color: "var(--ink-3)" }} />
            </div>
            <div className="col" style={{ gap: 12 }}>
              {castNames.map(name => (
                <VoiceRow key={name} name={name}
                  data={voices[name]}
                  active={beat?.speaker === name && playing}
                  onChange={(patch) => setVoices(v => ({ ...v, [name]: { ...v[name], ...patch } }))}
                />
              ))}
            </div>
          </Card>

          {/* Current scene lines */}
          <Card>
            <div className="section-eyebrow" style={{ marginBottom: 10 }}>
              CENA {String(sceneIdx + 1).padStart(2, "0")} · {scene?.label}
            </div>
            <div className="col" style={{ gap: 8 }}>
              {beats.filter(b => b.sceneIdx === sceneIdx).map((b, i) => {
                const isNow = b === beat;
                return (
                  <div key={i}
                    onClick={() => setT(b.start + 0.001)}
                    style={{
                      display: "flex", gap: 10, cursor: "pointer",
                      padding: "7px 9px", borderRadius: "var(--r-sm)",
                      background: isNow ? "var(--accent-soft)" : "var(--paper-2)",
                      border: isNow ? "1px solid var(--ink)" : "1px solid var(--rule)",
                    }}>
                    {b.speaker === "Narrador"
                      ? <span style={{ width: 26, height: 26, borderRadius: 6, background: "var(--ink)", color: "var(--paper-3)", display: "grid", placeItems: "center", flexShrink: 0 }}><Icon name="mic" size={13} /></span>
                      : b.speaker === "—"
                      ? <span style={{ width: 26, height: 26, borderRadius: 6, background: "var(--paper-3)", border: "1px solid var(--rule)", display: "grid", placeItems: "center", flexShrink: 0, fontFamily: "var(--mono)", fontSize: 10, color: "var(--ink-3)" }}>·</span>
                      : <Avatar name={b.speaker} size={26} style={{ borderRadius: 6 }} />}
                    <div style={{ minWidth: 0 }}>
                      <div className="text-xs muted" style={{ display: "flex", gap: 6, alignItems: "center" }}>
                        {b.speaker}
                        {b.kind === "thought" && <span className="mono" style={{ fontSize: 9 }}>· pensamento</span>}
                        {b.kind === "shout" && <span className="mono" style={{ fontSize: 9 }}>· grito</span>}
                        {b.kind === "narration" && <span className="mono" style={{ fontSize: 9 }}>· narração</span>}
                      </div>
                      <div className="text-sm" style={{ color: "var(--ink-2)", lineHeight: 1.35 }}>
                        {b.text || <em className="muted">(cena silenciosa)</em>}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Settings */}
          <Card>
            <div className="section-eyebrow" style={{ marginBottom: 12 }}>AJUSTES DO VÍDEO</div>

            <div className="row" style={{ justifyContent: "space-between", marginBottom: 14 }}>
              <span className="text-sm">Mostrar balões</span>
              <Toggle on={showBubbles} onClick={() => setShowBubbles(s => !s)} />
            </div>

            <div className="field" style={{ marginBottom: 14 }}>
              <span className="text-sm" style={{ marginBottom: 6 }}>Transição entre cenas</span>
              <div className="row" style={{ flexWrap: "wrap" }}>
                {[
                  { id: "cut", label: "Corte seco" },
                  { id: "fade", label: "Fade" },
                  { id: "kenburns", label: "Zoom lento" },
                  { id: "slide", label: "Deslize" },
                ].map(o => (
                  <Chip key={o.id} active={transition === o.id} onClick={() => setTransition(o.id)}>
                    {o.label}
                  </Chip>
                ))}
              </div>
            </div>

            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="text-sm">Trilha sonora suave</span>
              <Toggle on={music} onClick={() => setMusic(m => !m)} />
            </div>
          </Card>

          <Card style={{ background: "var(--accent-soft)" }}>
            <div className="text-sm" style={{ color: "var(--ink-2)" }}>
              <b style={{ fontFamily: "var(--serif)", fontSize: 15 }}>Duração estimada</b>
              <div className="row" style={{ justifyContent: "space-between", marginTop: 8 }}>
                <span>{panels.length} cenas · {beats.length} falas</span>
                <span className="mono">{fmt(total)}</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

/* ── Stage ── */
function VideoStage({ scene, sceneIdx, showBubbles, transition, playing, beat, voice }) {
  if (!scene) return null;
  const kb = transition === "kenburns";
  return (
    <div style={{
      background: "var(--ink)",
      borderRadius: "var(--r)",
      padding: 26,
      position: "relative",
      overflow: "hidden",
      boxShadow: "inset 0 0 60px rgba(0,0,0,0.4)",
      display: "grid", placeItems: "center",
      minHeight: 380,
    }}>
      {/* letterbox grain */}
      <div style={{
        position: "absolute", inset: 0, opacity: 0.06,
        backgroundImage: "radial-gradient(circle, #fff 0.5px, transparent 1px)",
        backgroundSize: "5px 5px",
      }}></div>

      <div
        key={sceneIdx + "-" + transition}
        style={{
          width: "100%", maxWidth: 640,
          animation: transition === "cut" ? "none"
            : transition === "slide" ? "vidSlide .5s ease-out both"
            : "vidFade .5s ease-out both",
        }}>
        <div style={{
          animation: kb && playing ? "kenburns 8s ease-out both" : "none",
          transformOrigin: "55% 45%",
        }}>
          <MangaPanel
            index={scene.index}
            label={scene.label}
            aspect={scene.aspect}
            tone={scene.tone}
            character={scene.character}
            bubbles={showBubbles ? scene.bubbles : []}
            sfx={scene.sfx}
            style={{ maxHeight: 420, boxShadow: "0 10px 40px rgba(0,0,0,0.5)" }}
          />
        </div>
      </div>

      {/* on-stage caption (lower third) */}
      {beat && beat.text && (
        <div style={{
          position: "absolute", left: 26, right: 26, bottom: 22,
          display: "flex", justifyContent: "center",
        }}>
          <div style={{
            background: "rgba(255, 250, 236, 0.94)",
            border: "1.5px solid var(--ink)",
            borderRadius: 4,
            padding: "10px 16px",
            maxWidth: "82%",
            boxShadow: "0 6px 20px rgba(0,0,0,0.35)",
            display: "flex", alignItems: "center", gap: 12,
          }}>
            {beat.speaker !== "Narrador" && beat.speaker !== "—" && (
              <Avatar name={beat.speaker} size={30} style={{ borderRadius: 6 }} />
            )}
            <div style={{ minWidth: 0 }}>
              <div className="mono" style={{ fontSize: 10, color: "var(--ink-3)", letterSpacing: "0.06em" }}>
                {beat.speaker === "Narrador" ? "NARRAÇÃO" : beat.speaker.toUpperCase()}
                {voice && voice.voice ? " · " + voice.voice : ""}
              </div>
              <div style={{
                fontFamily: beat.kind === "narration" ? "var(--sans)" : "var(--serif)",
                fontSize: beat.kind === "narration" ? 13.5 : 16,
                fontStyle: beat.kind === "thought" ? "italic" : "normal",
                color: "var(--ink)", lineHeight: 1.35,
              }}>{beat.text}</div>
            </div>
          </div>
        </div>
      )}

      {/* play overlay */}
      {!playing && (
        <div style={{
          position: "absolute", inset: 0, display: "grid", placeItems: "center",
          background: "rgba(20,16,10,0.18)",
        }}>
          <div style={{
            width: 64, height: 64, borderRadius: "50%",
            background: "var(--paper-3)", border: "2px solid var(--ink)",
            display: "grid", placeItems: "center",
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
          }}>
            <Icon name="play" size={26} stroke={2} style={{ marginLeft: 3 }} />
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Narration bar (waveform) ── */
function NarrationBar({ beat, voice, playing }) {
  const speaking = playing && beat && beat.text && !(voice && voice.muted);
  return (
    <div style={{
      marginTop: 12,
      display: "flex", alignItems: "center", gap: 14,
      background: "var(--paper-3)",
      border: "1px solid var(--rule)",
      borderRadius: "var(--r-sm)",
      padding: "10px 14px",
    }}>
      <div style={{
        display: "flex", alignItems: "flex-end", gap: 3, height: 24,
      }}>
        {[0,1,2,3,4,5,6,7].map(i => (
          <span key={i} style={{
            width: 3, borderRadius: 2,
            background: voice && voice.muted ? "var(--ink-4)" : "var(--accent)",
            height: speaking ? undefined : 4,
            animation: speaking ? `wave 0.7s ease-in-out ${i * 0.08}s infinite` : "none",
          }}></span>
        ))}
      </div>
      <div className="text-sm" style={{ color: "var(--ink-2)" }}>
        {voice && voice.muted
          ? <span className="muted">{beat?.speaker} está mudo nesta prévia</span>
          : speaking
          ? <span><b style={{ fontFamily: "var(--serif)" }}>{beat?.speaker}</b> falando — <span className="muted">{voice?.voice}</span></span>
          : <span className="muted">Pressione play para ouvir a narração simulada</span>}
      </div>
    </div>
  );
}

/* ── Transport ── */
function Transport({ playing, t, total, onPlay, onPrev, onNext, onSeek, speed, onSpeed }) {
  const pct = total ? (t / total) * 100 : 0;
  const speeds = [0.75, 1, 1.5, 2];
  return (
    <div className="row" style={{ marginTop: 12, gap: 14 }}>
      <IconButton name="skip_back" onClick={onPrev} title="Cena anterior" />
      <button onClick={onPlay}
        style={{
          width: 44, height: 44, borderRadius: "50%",
          background: "var(--ink)", color: "var(--paper-3)",
          border: "none", display: "grid", placeItems: "center", cursor: "pointer",
        }}>
        <Icon name={playing ? "pause" : "play"} size={18} stroke={2}
          style={{ marginLeft: playing ? 0 : 2 }} />
      </button>
      <IconButton name="skip_fwd" onClick={onNext} title="Próxima cena" />

      <div className="mono text-xs" style={{ color: "var(--ink-3)", width: 38 }}>{fmt(t)}</div>
      <div
        onClick={(e) => {
          const r = e.currentTarget.getBoundingClientRect();
          onSeek(((e.clientX - r.left) / r.width) * total);
        }}
        style={{
          flex: 1, height: 8, background: "var(--paper-2)",
          border: "1px solid var(--rule)", borderRadius: 999,
          position: "relative", cursor: "pointer",
        }}>
        <div style={{
          position: "absolute", left: 0, top: 0, bottom: 0,
          width: pct + "%", background: "var(--accent)", borderRadius: 999,
        }}></div>
        <div style={{
          position: "absolute", left: `calc(${pct}% - 7px)`, top: "50%",
          transform: "translateY(-50%)",
          width: 14, height: 14, borderRadius: "50%",
          background: "var(--paper-3)", border: "1.5px solid var(--ink)",
        }}></div>
      </div>
      <div className="mono text-xs" style={{ color: "var(--ink-3)", width: 38 }}>{fmt(total)}</div>

      <select className="select" value={speed}
        onChange={e => onSpeed(+e.target.value)}
        style={{ width: "auto", padding: "4px 8px", fontSize: 12 }}>
        {speeds.map(s => <option key={s} value={s}>{s}×</option>)}
      </select>
    </div>
  );
}

/* ── Scene timeline (filmstrip) ── */
function SceneTimeline({ panels, beats, total, t, current, onPick }) {
  return (
    <div style={{ marginTop: 18 }}>
      <div className="section-eyebrow" style={{ marginBottom: 10 }}>LINHA DO TEMPO · {panels.length} CENAS</div>
      <div style={{
        display: "flex", gap: 8, overflowX: "auto", paddingBottom: 6,
      }}>
        {panels.map((p, si) => {
          const first = beats.find(b => b.sceneIdx === si);
          const start = first ? first.start : 0;
          const isCur = si === current;
          return (
            <button key={p.id} onClick={() => onPick(si)}
              style={{
                flex: "0 0 auto", width: 132,
                background: "transparent", border: "none", padding: 0,
                cursor: "pointer", textAlign: "left",
              }}>
              <div style={{
                aspectRatio: "16/10",
                border: isCur ? "2px solid var(--ink)" : "1.5px solid var(--ink)",
                borderRadius: 2,
                background: "var(--paper-3)",
                position: "relative", overflow: "hidden",
                boxShadow: isCur ? "0 0 0 3px var(--accent-soft)" : "none",
              }}>
                <div style={{
                  position: "absolute", inset: 0,
                  backgroundImage: p.tone === "diag"
                    ? "repeating-linear-gradient(45deg, rgba(30,24,18,0.18) 0 1px, transparent 1px 6px)"
                    : p.tone === "dense"
                    ? "radial-gradient(circle, rgba(30,24,18,0.22) 0.7px, transparent 1px)"
                    : "radial-gradient(circle, rgba(30,24,18,0.18) 0.6px, transparent 1px)",
                  backgroundSize: p.tone === "dense" ? "4px 4px" : "6px 6px",
                  opacity: 0.5,
                }}></div>
                {p.character && (
                  <div style={{
                    position: "absolute", left: "50%", top: "55%", transform: "translate(-50%,-50%)",
                    width: 34, height: 34, borderRadius: "50%",
                    background: toneFor(p.character)[1], border: "1px solid var(--ink)",
                    display: "grid", placeItems: "center", fontFamily: "var(--serif)", fontSize: 16,
                  }}>{p.character[0]}</div>
                )}
                <div style={{
                  position: "absolute", top: 4, left: 4,
                  fontFamily: "var(--mono)", fontSize: 9,
                  background: "var(--paper-3)", border: "1px solid var(--ink)",
                  padding: "1px 4px",
                }}>{String(si + 1).padStart(2, "0")}</div>
              </div>
              <div className="text-xs" style={{ marginTop: 5, color: isCur ? "var(--ink)" : "var(--ink-3)", display: "flex", justifyContent: "space-between" }}>
                <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{p.label}</span>
                <span className="mono" style={{ flexShrink: 0, marginLeft: 6 }}>{fmt(start)}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/* ── Voice row ── */
function VoiceRow({ name, data, active, onChange }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "8px 10px", borderRadius: "var(--r-sm)",
      background: active ? "var(--accent-soft)" : "var(--paper-2)",
      border: active ? "1px solid var(--ink)" : "1px solid var(--rule)",
    }}>
      {name === "Narrador"
        ? <span style={{ width: 32, height: 32, borderRadius: 8, background: "var(--ink)", color: "var(--paper-3)", display: "grid", placeItems: "center", flexShrink: 0 }}><Icon name="mic" size={15} /></span>
        : <Avatar name={name} size={32} style={{ borderRadius: 8 }} />}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: "var(--serif)", fontSize: 14, lineHeight: 1 }}>{name}</div>
        <select className="select" value={data.voice}
          onChange={e => onChange({ voice: e.target.value })}
          style={{ marginTop: 4, padding: "3px 6px", fontSize: 11.5, width: "100%" }}>
          {VOICE_OPTIONS.map(v => <option key={v} value={v}>{v}</option>)}
        </select>
      </div>
      <button onClick={() => onChange({ muted: !data.muted })}
        title={data.muted ? "Ativar voz" : "Silenciar"}
        className="icon-btn"
        style={{ flexShrink: 0, background: data.muted ? "var(--paper-2)" : "var(--paper-3)" }}>
        <Icon name={data.muted ? "mute" : "volume"} size={15}
          style={{ color: data.muted ? "var(--ink-4)" : "var(--ink-2)" }} />
      </button>
    </div>
  );
}

/* ── Toggle ── */
function Toggle({ on, onClick }) {
  return (
    <button onClick={onClick}
      style={{
        width: 42, height: 24, borderRadius: 999,
        background: on ? "var(--accent)" : "var(--paper-2)",
        border: "1px solid var(--ink)", cursor: "pointer",
        position: "relative", padding: 0,
      }}>
      <span style={{
        position: "absolute", top: 2, left: on ? 20 : 2,
        width: 18, height: 18, borderRadius: "50%",
        background: "var(--paper-3)", border: "1px solid var(--ink)",
        transition: "left .15s",
      }}></span>
    </button>
  );
}

Object.assign(window, { VideoScreen });
