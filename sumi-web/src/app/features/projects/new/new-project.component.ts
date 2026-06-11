import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';
import { StyleService, type StyleOption } from '../../../core/services/style.service';
import { VoiceService, type SavedVoice } from '../../../core/services/voice.service';


const GENRES = [
  'Shojo', 'Shonen', 'Slice of life', 'Mistério', 'Drama',
  'Comédia', 'Fantasia', 'Romance', 'Aventura', 'Horror leve',
];

const TONES = [
  'Doce e melancólico', 'Tenso', 'Cômico', 'Mistério leve', 'Reflexivo', 'Heróico',
];

const EXAMPLES = [
  'Uma estudante recebe uma carta anônima debaixo da carteira no último dia de aula.',
  'Um gato preto guia uma garota tímida até um portão que ela nunca tinha visto.',
  'Dois rivais de clube esquecem o jogo quando começa a chover.',
];

const LANGUAGES = [
  { value: 'pt-BR', label: 'Português (BR)' },
  { value: 'ja', label: '日本語' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español' },
];

@Component({
  selector: 'app-new-project',
  standalone: true,
  templateUrl: './new-project.component.html',
  styleUrl: './new-project.component.scss',
})
export class NewProjectComponent implements OnInit {
  private router = inject(Router);
  private projectService = inject(ProjectService);
  private draftService = inject(ProjectDraftService);
  private styleService = inject(StyleService);
  private voiceService = inject(VoiceService);

  readonly genres = GENRES;
  readonly tones = TONES;
  readonly examples = EXAMPLES;
  readonly languages = LANGUAGES;

  styles = signal<StyleOption[]>([]);
  colorModes = signal<StyleOption[]>([]);

  idea = signal('');
  genre = signal('Shojo');
  tone = signal('Doce e melancólico');
  pages = signal(4);
  language = signal('pt-BR');
  style = signal('');
  colorMode = signal('');
  narratorVoiceId = signal<string | null>(null);
  voices = signal<SavedVoice[]>([]);
  loading = signal(false);

  ngOnInit(): void {
    this.styleService.catalog().subscribe({
      next: c => {
        this.styles.set(c.styles);
        this.colorModes.set(c.color_modes);
        if (!this.style()) this.style.set(c.default_style);
        if (!this.colorMode()) this.colorMode.set(c.default_color_mode);
      },
    });
    this.voiceService.list().subscribe({ next: vs => this.voices.set(vs) });

    const pid = this.draftService.projectId();
    if (!pid) return;
    this.loading.set(true);
    this.projectService.get(pid).subscribe({
      next: p => {
        this.idea.set(p.premise ?? '');
        this.genre.set(p.genre);
        this.tone.set(p.tone);
        this.pages.set(p.pages);
        this.style.set(p.style);
        if (p.color_mode) this.colorMode.set(p.color_mode);
        this.narratorVoiceId.set(p.narrator_voice_id);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  get panelCount(): string {
    const p = this.pages();
    return `≈ ${p * 3}–${p * 4} quadros`;
  }

  setIdea(e: Event): void {
    this.idea.set((e.target as HTMLTextAreaElement).value);
  }

  setLanguage(e: Event): void {
    this.language.set((e.target as HTMLSelectElement).value);
  }

  voiceMeta(v: SavedVoice): string {
    const parts: string[] = [];
    if (v.sex) parts.push(v.sex);
    if (v.age_start != null || v.age_end != null) {
      parts.push(`${v.age_start ?? '?'}–${v.age_end ?? '?'} anos`);
    }
    return parts.join(' · ');
  }

  decPages(): void {
    if (this.pages() > 1) this.pages.update(p => p - 1);
  }

  incPages(): void {
    if (this.pages() < 20) this.pages.update(p => p + 1);
  }

  advance(): void {
    if (!this.idea().trim() || this.loading()) return;
    const pid = this.draftService.projectId();
    this.loading.set(true);
    if (pid) {
      this.projectService.update(pid, {
        premise: this.idea(),
        genre: this.genre(),
        tone: this.tone(),
        pages: this.pages(),
        style: this.style(),
        color_mode: this.colorMode(),
        narrator_voice_id: this.narratorVoiceId(),
      }).subscribe({
        next: () => {
          this.loading.set(false);
          void this.router.navigate(['/projects/new/characters']);
        },
        error: () => this.loading.set(false),
      });
    } else {
      this.projectService.create({
        premise: this.idea(),
        genre: this.genre(),
        tone: this.tone(),
        pages: this.pages(),
        language: this.language(),
        style: this.style(),
        color_mode: this.colorMode(),
        narrator_voice_id: this.narratorVoiceId(),
      }).subscribe({
        next: (project) => {
          this.draftService.projectId.set(project.id);
          void this.router.navigate(['/projects/new/characters']);
        },
        error: () => this.loading.set(false),
      });
    }
  }

  cancel(): void {
    const pid = this.draftService.projectId();
    void this.router.navigate(pid ? ['/projects', pid, 'script'] : ['/home']);
  }
}
