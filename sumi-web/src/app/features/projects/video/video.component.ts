import { Component, computed, effect, inject, OnDestroy, OnInit, signal } from '@angular/core';
import { DecimalPipe, DatePipe } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin, timer, switchMap, takeWhile } from 'rxjs';
import type { PanelOut } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService, VideoJob, YtMeta } from '../../../core/services/project.service';
import { VoiceService, type SavedVoice } from '../../../core/services/voice.service';
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

const YT_CATEGORIES = [
  { id: '1',  label: 'Filme e Animação' },
  { id: '24', label: 'Entretenimento' },
  { id: '27', label: 'Educação' },
  { id: '23', label: 'Comédia' },
  { id: '20', label: 'Games' },
  { id: '28', label: 'Ciência e Tecnologia' },
  { id: '22', label: 'Pessoas e Blogs' },
];

const DEFAULT_YT_META: YtMeta = {
  yt_title: '',
  yt_description: '',
  yt_tags: [],
  yt_category_id: '1',
  privacy_status: 'private',
  publish_at: null,
  thumbnail_panel_id: null,
};

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
  imports: [DecimalPipe, DatePipe],
  templateUrl: './video.component.html',
  styleUrl: './video.component.scss',
})
export class VideoComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private draft = inject(ProjectDraftService);
  private panelService = inject(PanelService);
  private projectService = inject(ProjectService);
  private voiceService = inject(VoiceService);

  readonly voiceOptions = VOICE_OPTIONS;
  readonly speeds = SPEEDS;
  readonly transitions = TRANSITIONS;
  readonly ytCategories = YT_CATEGORIES;
  readonly baseUrl = environment.apiUrl;

  projectId = signal('');
  projectTitle = signal('');
  panels    = signal<PanelOut[]>([]);
  loading   = signal(true);

  // Export (ZIP)
  exporting       = signal(false);
  exportProgress  = signal(0);
  private exportTimer: ReturnType<typeof setInterval> | null = null;

  // Render de vídeo (.mp4)
  rendering       = signal(false);
  renderProgress  = signal(0);
  renderStage     = signal('');
  renderError     = signal('');
  videoUrl        = signal<string | null>(null);

  // YouTube modal
  ytModalOpen  = signal(false);
  ytMeta       = signal<YtMeta>({ ...DEFAULT_YT_META });
  ytGenerating = signal(false);
  ytSaving     = signal(false);
  ytTagInput   = signal('');

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
  private speechActive = false;
  private availableVoices = signal<SpeechSynthesisVoice[]>([]);

  // Vozes salvas (mesmas usadas no .mp4): narrador do projeto + voz por personagem.
  narratorVoice   = signal<SavedVoice | null>(null);
  charVoiceByName = signal<Map<string, SavedVoice>>(new Map());
  private audioEl: HTMLAudioElement | null = null;
  private currentBeatKey = '';
  private audioCache = new Map<string, string>();

  constructor() {
    // Transição de cena
    effect(() => {
      const idx = this.sceneIdx();
      if (idx !== this.prevScene && this.prevScene !== -1) this.triggerTransition();
      this.prevScene = idx;
    });

    // Narração: toca o beat atual sempre que ele muda durante o play
    effect(() => {
      const idx       = this.beatIdx();
      const isPlaying = this.playing();
      const beat      = this.bd().beats[idx];
      const voiceMap  = this.voices();

      if (!isPlaying || !beat?.text || beat.kind === 'silent') {
        this.stopNarration();
        return;
      }
      if (voiceMap[beat.speaker]?.muted) { this.stopNarration(); return; }
      this.narrate(beat);
    });
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.projectId.set(id);
    this.loadBrowserVoices();
    forkJoin({
      panels: this.panelService.list(id),
      project: this.projectService.get(id),
      voices: this.voiceService.list(),
    }).subscribe({
      next: ({ panels, project, voices }) => {
        this.projectTitle.set(project.title);
        if (project.video_url) this.videoUrl.set(`${this.baseUrl}${project.video_url}`);
        this.buildVoiceMaps(project.narrator_voice_id, project.characters, voices);
        this.panels.set(panels);
        this.initVoices(panels);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  ngOnDestroy(): void {
    this.stopTicker();
    this.clearExportTimer();
    this.stopNarration();
    for (const url of this.audioCache.values()) URL.revokeObjectURL(url);
  }

  private loadBrowserVoices(): void {
    if (!('speechSynthesis' in window)) return;
    const load = (): void => {
      const v = window.speechSynthesis.getVoices();
      if (v.length) this.availableVoices.set(v);
    };
    load();
    window.speechSynthesis.onvoiceschanged = load;
  }

  private buildVoiceMaps(
    narratorVoiceId: string | null,
    characters: { name: string; narrator_voice_id: string | null }[],
    saved: SavedVoice[],
  ): void {
    const byId = new Map(saved.map(v => [v.id, v]));
    this.narratorVoice.set(narratorVoiceId ? byId.get(narratorVoiceId) ?? null : null);
    const charMap = new Map<string, SavedVoice>();
    for (const c of characters) {
      if (c.narrator_voice_id) {
        const v = byId.get(c.narrator_voice_id);
        if (v) charMap.set(c.name, v);
      }
    }
    this.charVoiceByName.set(charMap);
  }

  /** Voz salva (narrador do projeto ou voz do personagem em cena), igual ao render do .mp4. */
  speakerVoice(name: string): SavedVoice | null {
    if (name === 'Narrador' || name === '—') return this.narratorVoice();
    return this.charVoiceByName().get(name) ?? this.narratorVoice();
  }

  private initVoices(panels: PanelOut[]): void {
    const names = ['Narrador'];
    for (const p of panels) if (p.character_name && !names.includes(p.character_name)) names.push(p.character_name);
    const v: Record<string, VoiceData> = {};
    for (const n of names) {
      const sv = this.speakerVoice(n);
      v[n] = { voice: sv ? sv.name : 'Voz padrão', muted: false };
    }
    this.voices.set(v);
  }

  // ── Narração (voz salva via MiniMax, com fallback do navegador) ────

  private narrate(beat: Beat): void {
    const key = `${beat.start}|${beat.speaker}|${beat.text}`;
    if (key === this.currentBeatKey) return;
    this.currentBeatKey = key;
    window.speechSynthesis?.cancel();
    if (this.audioEl) this.audioEl.pause();

    const voiceId = this.speakerVoice(beat.speaker)?.voice_id ?? null;
    if (!voiceId) { this.speakBrowser(beat); return; }

    this.speechActive = true;
    this.getAudio(beat.text, voiceId).then(url => {
      if (this.currentBeatKey !== key || !this.playing()) return;
      const audio = this.audioEl ?? (this.audioEl = new Audio());
      audio.src = url;
      audio.playbackRate = Math.max(0.5, Math.min(4, this.speed()));
      audio.onended = () => this.onBeatEnd(beat);
      audio.onerror = () => { this.speechActive = false; };
      void audio.play();
    }).catch(() => this.speakBrowser(beat));
  }

  private speakBrowser(beat: Beat): void {
    this.speechActive = true;
    if (!('speechSynthesis' in window)) {
      this.onBeatEnd(beat);
      return;
    }
    const utter = new SpeechSynthesisUtterance(beat.text);
    utter.lang = 'pt-BR';
    utter.rate = Math.max(0.5, Math.min(2, this.speed()));
    const ptVoices = this.availableVoices().filter(v => v.lang.startsWith('pt'));
    if (ptVoices.length) {
      const si = this.castNames().indexOf(beat.speaker);
      utter.voice = ptVoices[Math.max(0, si) % ptVoices.length] ?? null;
    }
    utter.onend = () => this.onBeatEnd(beat);
    utter.onerror = () => { this.speechActive = false; };
    window.speechSynthesis.speak(utter);
  }

  private onBeatEnd(beat: Beat): void {
    this.speechActive = false;
    if (this.playing() && this.t() < beat.start + beat.dur) {
      this.t.set(beat.start + beat.dur);
    }
  }

  private getAudio(text: string, voiceId: string): Promise<string> {
    const key = `${voiceId}|${text}`;
    const cached = this.audioCache.get(key);
    if (cached) return Promise.resolve(cached);
    return new Promise<string>((resolve, reject) => {
      this.voiceService.synthesize(text, voiceId).subscribe({
        next: blob => {
          const url = URL.createObjectURL(blob);
          this.audioCache.set(key, url);
          resolve(url);
        },
        error: reject,
      });
    });
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
      if (this.speechActive) return;          // aguarda o áudio terminar
      const next = this.t() + 0.07 * this.speed();
      if (next >= this.bd().total) { this.t.set(this.bd().total); this.stopTicker(); }
      else { this.t.set(next); }
    }, 70);
  }

  private stopTicker(): void {
    if (this.intervalId) { clearInterval(this.intervalId); this.intervalId = null; }
    this.stopNarration();
    this.playing.set(false);
  }

  private stopNarration(): void {
    window.speechSynthesis?.cancel();
    if (this.audioEl) this.audioEl.pause();
    this.currentBeatKey = '';
    this.speechActive = false;
  }

  jumpScene(dir: -1 | 1): void {
    this.stopNarration();
    const target = this.sceneIdx() + dir;
    const b = this.bd().beats.find(x => x.sceneIdx === target);
    if (b) this.t.set(b.start + 0.001);
  }

  jumpToScene(si: number): void {
    this.stopNarration();
    const b = this.bd().beats.find(x => x.sceneIdx === si);
    if (b) this.t.set(b.start + 0.001);
  }

  jumpToBeat(b: Beat): void { this.stopNarration(); this.t.set(b.start + 0.001); }

  onSeek(event: MouseEvent): void {
    this.stopNarration();
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

  startExport(): void {
    if (this.exporting()) return;
    this.exporting.set(true);
    this.exportProgress.set(0);

    // Barra de progresso animada enquanto o servidor processa
    this.exportTimer = setInterval(() => {
      const cur = this.exportProgress();
      if (cur < 88) this.exportProgress.set(cur + (88 - cur) * 0.08);
    }, 120);

    this.panelService.exportZip(this.projectId()).subscribe({
      next: blob => {
        this.clearExportTimer();
        this.exportProgress.set(100);
        const url = URL.createObjectURL(blob);
        const a   = document.createElement('a');
        a.href     = url;
        a.download = `sumi-${this.projectId().slice(0, 8)}.zip`;
        a.click();
        URL.revokeObjectURL(url);
        setTimeout(() => { this.exporting.set(false); this.exportProgress.set(0); }, 1200);
      },
      error: () => { this.clearExportTimer(); this.exporting.set(false); this.exportProgress.set(0); },
    });
  }

  private clearExportTimer(): void {
    if (this.exportTimer) { clearInterval(this.exportTimer); this.exportTimer = null; }
  }

  // ── Render de vídeo (.mp4) ────────────────────────────────────────

  generateVideo(): void {
    if (this.rendering()) return;
    this.rendering.set(true);
    this.renderProgress.set(0);
    this.renderStage.set('Iniciando…');
    this.renderError.set('');
    this.videoUrl.set(null);

    this.projectService.startVideoExport(this.projectId()).pipe(
      switchMap(job =>
        timer(0, 2500).pipe(
          switchMap(() => this.projectService.pollVideoJob(this.projectId(), job.job_id)),
          takeWhile((j: VideoJob) => j.status !== 'done' && j.status !== 'error', true),
        )
      ),
    ).subscribe({
      next: (j: VideoJob) => {
        this.renderProgress.set(j.progress);
        this.renderStage.set(j.detail);
        if (j.status === 'done') {
          this.videoUrl.set(j.video_url ? `${this.baseUrl}${j.video_url}` : null);
          this.rendering.set(false);
        } else if (j.status === 'error') {
          this.renderError.set(j.detail || 'Falha ao gerar o vídeo.');
          this.rendering.set(false);
        }
      },
      error: err => {
        this.renderError.set(err?.error?.detail ?? err?.message ?? 'Falha ao gerar o vídeo.');
        this.rendering.set(false);
      },
    });
  }

  downloadVideo(): void {
    const url = this.videoUrl();
    if (!url) return;
    const slug = this.projectTitle().trim().toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
      || `sumi-${this.projectId().slice(0, 8)}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `${slug}.mp4`;
    a.click();
  }

  goFinal(): void { void this.router.navigate(['/projects', this.projectId(), 'final']); }

  // ── YouTube ───────────────────────────────────────────────────────────────

  openYoutubeModal(): void {
    this.ytModalOpen.set(true);
    this.projectService.getYtMeta(this.projectId()).subscribe({
      next: meta => this.ytMeta.set(meta),
      error: () => this.ytMeta.set({ ...DEFAULT_YT_META }),
    });
  }

  closeYtModal(): void { this.ytModalOpen.set(false); }

  generateYtMeta(): void {
    if (this.ytGenerating()) return;
    this.ytGenerating.set(true);
    this.projectService.generateYtMeta(this.projectId()).subscribe({
      next: meta => { this.ytMeta.set(meta); this.ytGenerating.set(false); },
      error: () => this.ytGenerating.set(false),
    });
  }

  setYtField<K extends keyof YtMeta>(field: K, value: YtMeta[K]): void {
    this.ytMeta.update(m => ({ ...m, [field]: value }));
  }

  addYtTag(): void {
    const raw = this.ytTagInput().trim();
    if (!raw) return;
    const tags = raw.split(',').map(t => t.trim()).filter(Boolean);
    this.ytMeta.update(m => ({ ...m, yt_tags: [...new Set([...m.yt_tags, ...tags])] }));
    this.ytTagInput.set('');
  }

  removeYtTag(tag: string): void {
    this.ytMeta.update(m => ({ ...m, yt_tags: m.yt_tags.filter(t => t !== tag) }));
  }

  selectThumbnail(panelId: string): void {
    this.ytMeta.update(m => ({
      ...m,
      thumbnail_panel_id: m.thumbnail_panel_id === panelId ? null : panelId,
    }));
  }

  saveAndOpenYoutube(): void {
    if (this.ytSaving()) return;
    this.ytSaving.set(true);
    this.projectService.saveYtMeta(this.projectId(), this.ytMeta()).subscribe({
      next: () => {
        this.ytSaving.set(false);
        this.ytModalOpen.set(false);
        window.open('https://studio.youtube.com/', '_blank');
      },
      error: () => this.ytSaving.set(false),
    });
  }
}
