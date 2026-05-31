import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { environment } from '../../../../environments/environment';
import type { CharacterCreate, CharacterOut } from '../../../core/models/home.models';
import { CharacterService } from '../../../core/services/character.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';

type Tab = 'library' | 'manual' | 'ai';
type AiMode = 'prompt' | 'attrs';

interface AiCandidate {
  id: string;
  imageUrl: string;
  notes: string;
}

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

  selectedCount = computed(() => this.selectedIds().size);

  ngOnInit(): void {
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

    const prompt = this.aiMode() === 'prompt'
      ? this.aiPrompt()
      : Object.values(this.aiAttrs()).join(', ');

    this.characterService.generatePortrait(prompt).subscribe({
      next: candidates => {
        this.aiCandidates.set(candidates.map(c => ({
          id: c.id,
          imageUrl: `${environment.apiUrl}${c.url}`,
          notes: c.notes,
        })));
        this.aiGenerating.set(false);
      },
      error: () => this.aiGenerating.set(false),
    });
  }

  pickCandidate(id: string): void {
    this.aiPicked.set(this.aiPicked() === id ? null : id);
  }

  confirmAi(): void {
    if (!this.aiPicked() || !this.aiName().trim() || this.aiSaving()) return;
    const picked = this.aiCandidates().find(c => c.id === this.aiPicked());
    this.aiSaving.set(true);
    const req: CharacterCreate = {
      name: this.aiName(),
      role: this.aiMode() === 'attrs' ? this.aiAttrs().archetype : 'Personagem',
      traits: ['gerado por IA'],
      image_url: picked?.imageUrl,
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
    if (this.saving()) return;
    const projectId = this.draftService.projectId();
    if (!projectId) {
      void this.router.navigate(['/projects/new']);
      return;
    }
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
    if (!projectId) {
      void this.router.navigate(['/projects/new']);
      return;
    }
    this.draftService.projectId.set(null);
    void this.router.navigate(['/projects', projectId, 'script']);
  }

  back(): void {
    void this.router.navigate(['/projects/new']);
  }
}
