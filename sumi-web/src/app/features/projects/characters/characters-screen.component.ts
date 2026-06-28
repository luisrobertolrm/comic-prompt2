import { Component, DestroyRef, computed, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import type { AttrOption, CharacterOut, CharacterUpdate } from '../../../core/models/home.models';
import { CharacterService } from '../../../core/services/character.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';
import { StyleService, type StyleOption } from '../../../core/services/style.service';
import { VoiceService, type SavedVoice } from '../../../core/services/voice.service';
import { AiTabComponent } from './ai-tab/ai-tab.component';
import { ManualTabComponent } from './manual-tab/manual-tab.component';
import { AiCandidate, portraitStream, toCandidates } from './shared/portrait-stream';

type Tab = 'library' | 'manual' | 'ai';

const GENDERS = ['Feminino', 'Masculino', 'Outro', 'Não especificado'];

@Component({
  selector: 'app-characters-screen',
  standalone: true,
  imports: [ManualTabComponent, AiTabComponent],
  templateUrl: './characters-screen.component.html',
  styleUrl: './characters-screen.component.scss',
})
export class CharactersScreenComponent implements OnInit {
  private router = inject(Router);
  private draftService = inject(ProjectDraftService);
  private characterService = inject(CharacterService);
  private projectService = inject(ProjectService);
  private styleService = inject(StyleService);
  private voiceService = inject(VoiceService);
  private destroyRef = inject(DestroyRef);

  tab = signal<Tab>('library');
  characters = signal<CharacterOut[]>([]);
  projectStyle = signal('anime-90s');
  projectColorMode = signal('tons-cinza');
  selectedIds = signal<Set<string>>(new Set());
  loading = signal(true);
  saving = signal(false);
  voices = signal<SavedVoice[]>([]);

  readonly genders = GENDERS;

  ethnicities = signal<AttrOption[]>([]);
  ageRanges = signal<AttrOption[]>([]);
  private styleCatalog = signal<StyleOption[]>([]);
  styleLabel = computed(() =>
    this.styleCatalog().find(s => s.id === this.projectStyle())?.label ?? this.projectStyle()
  );

  // Modal de edição
  editing = signal<CharacterOut | null>(null);
  eName = signal('');
  eRole = signal('');
  eGender = signal('');
  eAge = signal('');
  eHeight = signal('');
  eSummary = signal('');
  eOutfit = signal('');
  eTraits = signal('');
  eNarratorVoiceId = signal<string | null>(null);
  eImageUrl = signal<string | null>(null);
  eGenerating = signal(false);
  eError = signal('');
  eCandidates = signal<AiCandidate[]>([]);
  ePicked = signal<string | null>(null);
  eSaving = signal(false);

  selectedCount = computed(() => this.selectedIds().size);

  // Não usados (sem projeto) e fora da seleção atual — seguros para excluir.
  deletableUnused = computed(() =>
    this.characters().filter(c => c.project_count === 0 && !this.selectedIds().has(c.id))
  );
  confirmDeleteUnused = signal(false);
  deletingUnused = signal(false);
  eRegenWarn = signal(false);

  ngOnInit(): void {
    this.voiceService.list().subscribe({ next: vs => this.voices.set(vs) });

    this.styleService.catalog().subscribe({ next: c => this.styleCatalog.set(c.styles) });

    this.characterService.options().subscribe({
      next: groups => {
        this.ethnicities.set(groups.find(g => g.id === 'ethnicity')?.options ?? []);
        this.ageRanges.set(groups.find(g => g.id === 'age_range')?.options ?? []);
      },
    });

    this.characterService.listAll().subscribe({
      next: chars => { this.characters.set(chars); this.loading.set(false); },
      error: () => this.loading.set(false),
    });

    const projectId = this.draftService.projectId();
    if (projectId) {
      this.projectService.get(projectId).subscribe({
        next: p => {
          this.selectedIds.set(new Set(p.characters.map(c => c.id)));
          this.projectStyle.set(p.style);
          this.projectColorMode.set(p.color_mode ?? 'tons-cinza');
        },
      });
    }
  }

  /** Personagem criado por uma das abas (manual/ia): adiciona, seleciona e volta à biblioteca. */
  onCharacterCreated(char: CharacterOut): void {
    this.characters.update(c => [...c, char]);
    this.toggleChar(char.id);
    this.tab.set('library');
  }

  deleteUnused(): void {
    const ids = this.deletableUnused().map(c => c.id);
    if (ids.length === 0 || this.deletingUnused()) return;
    this.deletingUnused.set(true);
    this.characterService.deleteUnused(ids).subscribe({
      next: () => {
        const removed = new Set(ids);
        this.characters.update(list => list.filter(c => !removed.has(c.id)));
        this.deletingUnused.set(false);
        this.confirmDeleteUnused.set(false);
      },
      error: () => this.deletingUnused.set(false),
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

  voiceName(voiceId: string | null): string | null {
    if (!voiceId) return null;
    return this.voices().find(v => v.id === voiceId)?.name ?? null;
  }

  voiceMeta(v: SavedVoice): string {
    const parts: string[] = [];
    if (v.sex) parts.push(v.sex);
    if (v.age_start != null || v.age_end != null) {
      parts.push(`${v.age_start ?? '?'}–${v.age_end ?? '?'} anos`);
    }
    return parts.join(' · ');
  }

  setField(sig: ReturnType<typeof signal<string>>, e: Event): void {
    sig.set((e.target as HTMLInputElement | HTMLTextAreaElement).value);
  }

  // ── Modal de edição ──

  openEdit(c: CharacterOut): void {
    this.editing.set(c);
    this.eName.set(c.name);
    this.eRole.set(c.role);
    this.eGender.set(c.gender ?? '');
    this.eAge.set(c.age != null ? String(c.age) : '');
    this.eHeight.set(c.height ?? '');
    this.eSummary.set(c.summary ?? '');
    this.eOutfit.set(c.outfit ?? '');
    this.eTraits.set(c.traits.join(', '));
    this.eNarratorVoiceId.set(c.narrator_voice_id);
    this.eImageUrl.set(c.image_url);
    this.eGenerating.set(false);
    this.eError.set('');
    this.eCandidates.set([]);
    this.ePicked.set(null);
    this.eRegenWarn.set(false);
  }

  closeEdit(): void {
    this.editing.set(null);
  }

  regenPortrait(force = false): void {
    if (!this.eSummary().trim() || this.eGenerating()) return;
    const ed = this.editing();
    if (!ed) return;
    if (!this.eName().trim()) {
      this.eError.set('Informe o nome antes de regerar.');
      return;
    }
    if (!force && ed.project_count > 0) {
      this.eRegenWarn.set(true);
      return;
    }
    this.eRegenWarn.set(false);
    this.eGenerating.set(true);
    this.eError.set('');

    // Salva os dados da tela primeiro; só dispara a geração após a confirmação do save.
    this.characterService.update(ed.id, this.buildEditReq()).subscribe({
      next: char => {
        this.characters.update(list => list.map(c => (c.id === char.id ? char : c)));
        this.runPortraitRegen();
      },
      error: err => {
        this.eGenerating.set(false);
        this.eError.set(err?.error?.detail ?? err?.message ?? 'Falha ao salvar antes de regerar.');
      },
    });
  }

  private runPortraitRegen(): void {
    this.eCandidates.set([]);
    this.ePicked.set(null);
    portraitStream(this.characterService, this.destroyRef, {
      style: this.projectStyle(),
      colorMode: this.projectColorMode(),
      gender: this.eGender(),
      extra: this.eSummary(),
    }).subscribe({
      next: job => {
        if (job.status === 'done') {
          this.eCandidates.set(toCandidates(job));
          this.eGenerating.set(false);
        } else if (job.status === 'error') {
          this.eError.set(job.detail || 'Erro ao gerar retratos.');
          this.eGenerating.set(false);
        }
      },
      error: err => {
        this.eGenerating.set(false);
        this.eError.set(err?.error?.detail ?? err?.message ?? 'Erro ao gerar retratos.');
      },
    });
  }

  pickEditCandidate(id: string): void {
    this.ePicked.set(this.ePicked() === id ? null : id);
  }

  private buildEditReq(): CharacterUpdate {
    return {
      name: this.eName(),
      role: this.eRole() || 'Personagem',
      gender: this.eGender() || null,
      age: this.eAge() ? +this.eAge() : null,
      height: this.eHeight() || null,
      summary: this.eSummary() || null,
      outfit: this.eOutfit() || null,
      traits: this.eTraits().split(',').map(t => t.trim()).filter(Boolean),
      narrator_voice_id: this.eNarratorVoiceId(),
    };
  }

  saveEdit(): void {
    const current = this.editing();
    if (!current || !this.eName().trim() || this.eSaving()) return;
    this.eSaving.set(true);

    const picked = this.eCandidates().find(c => c.id === this.ePicked());
    const req: CharacterUpdate = this.buildEditReq();
    if (picked) req.image_url = picked.imageUrl;

    this.characterService.update(current.id, req).subscribe({
      next: char => {
        this.characters.update(list => list.map(c => (c.id === char.id ? char : c)));
        this.eSaving.set(false);
        this.closeEdit();
      },
      error: () => this.eSaving.set(false),
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
        void this.router.navigate(['/projects/new/scenarios']);
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
