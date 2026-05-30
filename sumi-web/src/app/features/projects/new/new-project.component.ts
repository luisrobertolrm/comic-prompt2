import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';

const GENRES = [
  'Shojo', 'Shonen', 'Slice of life', 'Mistério', 'Drama',
  'Comédia', 'Fantasia', 'Romance', 'Aventura', 'Horror leve',
];

const TONES = [
  'Doce e melancólico', 'Tenso', 'Cômico', 'Mistério leve', 'Reflexivo', 'Heróico',
];

const STYLES = [
  { id: 'classic-shoujo', label: 'Shojo clássico (olhos grandes)', note: '70s–80s, traços líricos' },
  { id: 'modern-line', label: 'Linha moderna limpa', note: 'contornos finos, screentones suaves' },
  { id: 'ink-heavy', label: 'Tinta marcada', note: 'sombras profundas, contraste alto' },
  { id: 'minimal', label: 'Minimalista', note: 'muito branco, balões grandes' },
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
export class NewProjectComponent {
  private router = inject(Router);
  private projectService = inject(ProjectService);
  private draftService = inject(ProjectDraftService);

  readonly genres = GENRES;
  readonly tones = TONES;
  readonly styles = STYLES;
  readonly examples = EXAMPLES;
  readonly languages = LANGUAGES;

  idea = signal('');
  genre = signal('Shojo');
  tone = signal('Doce e melancólico');
  pages = signal(4);
  language = signal('pt-BR');
  style = signal('classic-shoujo');
  loading = signal(false);

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

  decPages(): void {
    if (this.pages() > 1) this.pages.update(p => p - 1);
  }

  incPages(): void {
    if (this.pages() < 20) this.pages.update(p => p + 1);
  }

  advance(): void {
    if (!this.idea().trim() || this.loading()) return;
    this.loading.set(true);
    this.projectService.create({
      premise: this.idea(),
      genre: this.genre(),
      tone: this.tone(),
      pages: this.pages(),
      language: this.language(),
      style: this.style(),
    }).subscribe({
      next: (project) => {
        this.draftService.projectId.set(project.id);
        void this.router.navigate(['/projects/new/characters']);
      },
      error: () => this.loading.set(false),
    });
  }

  cancel(): void {
    void this.router.navigate(['/home']);
  }
}
