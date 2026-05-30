import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import type { CharacterCreate, CharacterOut } from '../../../core/models/home.models';
import { CharacterService } from '../../../core/services/character.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';

type Tab = 'library' | 'manual' | 'ai';
type AiMode = 'prompt' | 'attrs';

interface AiCandidate {
  id: string;
  palette: string;
  tone: string;
  notes: string;
}

const AI_CANDIDATES: AiCandidate[] = [
  { id: 'c0', palette: 'blush', tone: 'dots', notes: 'Linha leve · olhos marcantes' },
  { id: 'c1', palette: 'peach', tone: 'diag', notes: 'Sombras suaves · postura tímida' },
  { id: 'c2', palette: 'mint', tone: 'dense', notes: 'Olhar direto · mais maturidade' },
  { id: 'c3', palette: 'lilac', tone: 'dots', notes: 'Estilo retrô · screentone denso' },
];

@Component({
  selector: 'app-characters-screen',
  standalone: true,
  templateUrl: './characters-screen.component.html',
  styleUrl: './characters-screen.component.scss',
})
export class CharactersScreenComponent implements OnInit {
  private router = inject(Router);
  private draftService = inject(ProjectDraftService);
  private characterService = inject(CharacterService);
  private projectService = inject(ProjectService);

  tab = signal<Tab>('library');
  characters = signal<CharacterOut[]>([]);
  selectedIds = signal<Set<string>>(new Set());
  loading = signal(true);
  saving = signal(false);

  // Form manual
  mName = signal('');
  mRole = signal('Protagonista');
  mAge = signal('16');
  mHeight = signal('');
  mSummary = signal('');
  mOutfit = signal('');
  mTraits = signal('');
  mSaving = signal(false);

  // IA
  aiMode = signal<AiMode>('prompt');
  aiPrompt = signal('Uma garota tímida de 16 anos, olhos grandes castanho-âmbar com brilho, franja reta, sempre carrega um caderno. Veste uniforme escolar.');
  aiAttrs = signal({ archetype: 'protagonista', age: '16', hair: 'preto, franja reta', eyes: 'âmbar, grandes', outfit: 'uniforme escolar', personality: 'tímida, curiosa', quirk: 'anota tudo em um caderno' });
  aiGenerating = signal(false);
  aiCandidates = signal<AiCandidate[]>([]);
  aiPicked = signal<string | null>(null);
  aiName = signal('');
  aiSaving = signal(false);

  readonly candidates = AI_CANDIDATES;

  selectedCount = computed(() => this.selectedIds().size);

  ngOnInit(): void {
    if (!this.draftService.projectId()) {
      void this.router.navigate(['/projects/new']);
      return;
    }
    this.characterService.listAll().subscribe({
      next: chars => { this.characters.set(chars); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  toggleChar(id: string): void {
    const s = new Set(this.selectedIds());
    if (s.has(id)) s.delete(id); else s.add(id);
    this.selectedIds.set(s);
  }

  isSelected(id: string): boolean {
    return this.selectedIds().has(id);
  }

  initial(name: string): string {
    return name.charAt(0).toUpperCase();
  }

  // ── Manual form ──

  setField(sig: ReturnType<typeof signal<string>>, e: Event): void {
    sig.set((e.target as HTMLInputElement | HTMLTextAreaElement).value);
  }

  submitManual(): void {
    if (!this.mName().trim() || this.mSaving()) return;
    this.mSaving.set(true);
    const req: CharacterCreate = {
      name: this.mName(),
      role: this.mRole() || 'Personagem',
      age: this.mAge() ? +this.mAge() : undefined,
      height: this.mHeight() || undefined,
      summary: this.mSummary() || undefined,
      outfit: this.mOutfit() || undefined,
      traits: this.mTraits().split(',').map(t => t.trim()).filter(Boolean),
    };
    this.characterService.create(req).subscribe({
      next: char => {
        this.characters.update(c => [...c, char]);
        this.toggleChar(char.id);
        this.resetManual();
        this.tab.set('library');
        this.mSaving.set(false);
      },
      error: () => this.mSaving.set(false),
    });
  }

  private resetManual(): void {
    this.mName.set(''); this.mRole.set('Protagonista');
    this.mAge.set('16'); this.mHeight.set('');
    this.mSummary.set(''); this.mOutfit.set(''); this.mTraits.set('');
  }

  // ── IA ──

  setAiAttr(key: string, e: Event): void {
    const value = (e.target as HTMLInputElement).value;
    this.aiAttrs.update(a => ({ ...a, [key]: value }));
  }

  generateAi(): void {
    this.aiGenerating.set(true);
    this.aiCandidates.set([]);
    this.aiPicked.set(null);
    setTimeout(() => {
      this.aiCandidates.set([...AI_CANDIDATES]);
      this.aiGenerating.set(false);
    }, 1200);
  }

  pickCandidate(id: string): void {
    this.aiPicked.set(this.aiPicked() === id ? null : id);
  }

  coverPattern(tone: string): string {
    if (tone === 'diag') return 'repeating-linear-gradient(45deg,rgba(30,24,18,.2) 0 1px,transparent 1px 6px)';
    if (tone === 'dense') return 'radial-gradient(circle,rgba(30,24,18,.24) .8px,transparent 1px)';
    return 'radial-gradient(circle,rgba(30,24,18,.18) .6px,transparent 1px)';
  }

  coverBgSize(tone: string): string {
    return tone === 'dense' ? '4px 4px' : '7px 7px';
  }

  confirmAi(): void {
    if (!this.aiPicked() || !this.aiName().trim() || this.aiSaving()) return;
    this.aiSaving.set(true);
    const req: CharacterCreate = {
      name: this.aiName(),
      role: this.aiMode() === 'attrs' ? this.aiAttrs().archetype : 'Personagem',
      traits: ['gerado por IA'],
    };
    this.characterService.create(req).subscribe({
      next: char => {
        this.characters.update(c => [...c, char]);
        this.toggleChar(char.id);
        this.aiCandidates.set([]); this.aiPicked.set(null); this.aiName.set('');
        this.tab.set('library');
        this.aiSaving.set(false);
      },
      error: () => this.aiSaving.set(false),
    });
  }

  // ── Navegação ──

  advance(): void {
    const projectId = this.draftService.projectId();
    if (!projectId || this.saving()) return;
    this.saving.set(true);
    this.projectService.setCharacters(projectId, [...this.selectedIds()]).subscribe({
      next: () => {
        this.draftService.projectId.set(null);
        void this.router.navigate(['/projects', projectId, 'script']);
      },
      error: () => this.saving.set(false),
    });
  }

  skip(): void {
    const projectId = this.draftService.projectId();
    this.draftService.projectId.set(null);
    void this.router.navigate(['/projects', projectId ?? '', 'script']);
  }

  back(): void {
    void this.router.navigate(['/projects/new']);
  }
}
