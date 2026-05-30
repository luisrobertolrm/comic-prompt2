import { Component, computed, effect, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import type { PanelOut } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { environment } from '../../../../environments/environment';

// ── Tipos ────────────────────────────────────────────────────────────

interface Beat {
  sceneIdx: number;
  speaker: string;
  kind: string;  // narration | say | thought | shout | silent
  text: string;
  dur: number;
  start: number;
}

interface BeatData { beats: Beat[]; total: number; }
interface VoiceData { voice: string; muted: boolean; }

// ── Constantes ───────────────────────────────────────────────────────

const VOICE_OPTIONS = [
  'Narração suave', 'Jovem feminina', 'Jovem masculina',
  'Grave e calma', 'Doce', 'Energética', 'Misteriosa', 'Madura',
];

const SPEEDS = [0.75, 1, 1.5, 2];

const TRANSITIONS = [
  { id: 'cut',      label: 'Corte seco' },
  { id: 'fade',     label: 'Fade' },
  { id: 'kenburns', label: 'Zoom lento' },
  { id: 'slide',    label: 'Deslize' },
];

// ── Helpers ──────────────────────────────────────────────────────────

function buildBeats(panels: PanelOut[]): BeatData {
  const beats: Beat[] = [];
  panels.forEach((p, si) => {
    if (p.caption?.trim()) {
      beats.push({ sceneIdx: si, speaker: 'Narrador', kind: 'narration', text: p.caption, dur: 0, start: 0 });
    }
    p.bubbles.forEach(b => {
      beats.push({ sceneIdx: si, speaker: p.character_name ?? 'Narrador', kind: b.kind, text: b.text, dur: 0, start: 0 });
    });
    if (!p.caption?.trim() && p.bubbles.length === 0) {
      beats.push({ sceneIdx: si, speaker: '—', kind: 'silent', text: '', dur: 0, start: 0 });
    }
  });
  let acc = 0;
  for (const b of beats) {
    const words = b.text.trim().split(/\s+/).filter(Boolean).length;
    const dur = Math.min(6, Math.max(b.kind === 'silent' ? 1.6 : 2.0, words * 0.42));
    b.dur = dur;
    b.start = acc;
    acc += dur;
  }
  return { beats, total: acc };
}

export function fmt(s: number): string {
  const t = Math.max(0, Math.floor(s));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, '0')}`;
}

// ── Componente ───────────────────────────────────────────────────────

@Component({
  selector: 'app-video',
  standalone: true,
  imports: [],
  templateUrl: './video.component.html',
  styleUrl: './video.component.scss',
})
export class VideoComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private draft = inject(ProjectDraftService);
  private panelService = inject(PanelService);

  readonly voiceOptions = VOICE_OPTIONS;
  readonly speeds = SPEEDS;
  readonly transitions = TRANSITIONS;
  readonly baseUrl = environment.apiUrl;

  projectId = signal('');
  panels    = signal<PanelOut[]>([]);
  loading   = signal(true);

  // Playback
  t          = signal(0);
  playing    = signal(false);
  showBubbles = signal(true);
  transition  = signal('fade');
  speed       = signal(1);
  music       = signal(true);
  voices      = signal<Record<string, VoiceData>>({});
  panelFading = signal(false);

  // Computed
  bd          = computed(() => buildBeats(this.panels()));
  beatIdx     = computed(() => {
    const cur = this.t();
    const bs  = this.bd().beats;
    let idx = 0;
    for (let i = 0; i < bs.length; i++) if (bs[i].start <= cur + 0.0001) idx = i;
    return idx;
  });
  beat       = computed(() => this.bd().beats[this.beatIdx()] ?? null);
  sceneIdx   = computed(() => this.beat()?.sceneIdx ?? 0);
  scene      = computed(() => this.panels()[this.sceneIdx()] ?? null);
  pct        = computed(() => this.bd().total > 0 ? (this.t() / this.bd().total) * 100 : 0);
  castNames  = computed(() => {
    const names = ['Narrador'];
    for (const p of this.panels()) {
      if (p.character_name && !names.includes(p.character_name)) names.push(p.character_name);
    }
    return names;
  });
  sceneBeatLines = computed(() =>
    this.bd().beats.filter(b => b.sceneIdx === this.sceneIdx())
  );
  curVoice = computed(() => this.voices()[this.beat()?.speaker ?? ''] ?? { voice: '—', muted: false });

  private intervalId: ReturnType<typeof setInterval> | null = null;
  private prevScene = -1;

  constructor() {
    effect(() => {
      const idx = this.sceneIdx();
      if (idx !== this.prevScene && this.prevScene !== -1) this.triggerTransition();
      this.prevScene = idx;
    });
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.projectId.set(id);
    this.panelService.list(id).subscribe({
      next: ps => { this.panels.set(ps); this.initVoices(ps); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  ngOnDestroy(): void { this.stopTicker(); }

  private initVoices(panels: PanelOut[]): void {
    const names = ['Narrador'];
    for (const p of panels) if (p.character_name && !names.includes(p.character_name)) names.push(p.character_name);
    const v: Record<string, VoiceData> = {};
    names.forEach((n, i) => {
      v[n] = { voice: n === 'Narrador' ? VOICE_OPTIONS[0] : VOICE_OPTIONS[(i + 1) % VOICE_OPTIONS.length], muted: false };
    });
    this.voices.set(v);
  }

  private triggerTransition(): void {
    if (this.transition() === 'cut') return;
    this.panelFading.set(true);
    setTimeout(() => this.panelFading.set(false), 50);
  }

  // ── Playback ──────────────────────────────────────────────────────

  togglePlay(): void {
    if (this.t() >= this.bd().total) this.t.set(0);
    if (this.playing()) { this.stopTicker(); }
    else { this.playing.set(true); this.startTicker(); }
  }

  private startTicker(): void {
    this.intervalId = setInterval(() => {
      const next = this.t() + 0.07 * this.speed();
      if (next >= this.bd().total) { this.t.set(this.bd().total); this.stopTicker(); }
      else { this.t.set(next); }
    }, 70);
  }

  private stopTicker(): void {
    if (this.intervalId) { clearInterval(this.intervalId); this.intervalId = null; }
    this.playing.set(false);
  }

  jumpScene(dir: -1 | 1): void {
    const target = this.sceneIdx() + dir;
    const b = this.bd().beats.find(x => x.sceneIdx === target);
    if (b) this.t.set(b.start + 0.001);
  }

  jumpToScene(si: number): void {
    const b = this.bd().beats.find(x => x.sceneIdx === si);
    if (b) this.t.set(b.start + 0.001);
  }

  jumpToBeat(b: Beat): void { this.t.set(b.start + 0.001); }

  onSeek(event: MouseEvent): void {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
    const pct = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
    this.t.set(pct * this.bd().total);
  }

  setSpeed(e: Event): void { this.speed.set(+(e.target as HTMLSelectElement).value); }

  setVoice(name: string, patch: Partial<VoiceData>): void {
    this.voices.update(v => ({ ...v, [name]: { ...v[name], ...patch } }));
  }

  // ── Display helpers ───────────────────────────────────────────────

  readonly String = String;

  fmt(s: number): string { return fmt(s); }
  padNum(n: number): string { return String(n).padStart(2, '0'); }
  initial(name: string): string { return name.charAt(0).toUpperCase(); }
  imageUrl(p: PanelOut | null): string { return p?.image_url ? `${this.baseUrl}${p.image_url}` : ''; }

  tonePattern(tone: string): string {
    if (tone === 'diag') return 'repeating-linear-gradient(45deg,rgba(30,24,18,.18) 0 1px,transparent 1px 6px)';
    if (tone === 'dense') return 'radial-gradient(circle,rgba(30,24,18,.22) .7px,transparent 1px)';
    return 'radial-gradient(circle,rgba(30,24,18,.18) .6px,transparent 1px)';
  }
  toneBgSize(tone: string): string { return tone === 'dense' ? '4px 4px' : '6px 6px'; }

  stageAnim(): string {
    if (this.transition() === 'cut' || !this.panelFading()) return 'none';
    if (this.transition() === 'slide') return 'vidSlide .45s ease-out both';
    return 'vidFade .45s ease-out both';
  }

  isBeatNow(b: Beat): boolean { return b === this.beat(); }

  goFinal(): void { void this.router.navigate(['/projects', this.projectId(), 'final']); }
}
