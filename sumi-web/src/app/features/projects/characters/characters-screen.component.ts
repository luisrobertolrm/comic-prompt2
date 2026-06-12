import { Component, DestroyRef, computed, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { Observable, timer, switchMap, takeWhile } from 'rxjs';
import { environment } from '../../../../environments/environment';
import type { AttrOption, CharacterCreate, CharacterOut, CharacterUpdate, PortraitJob } from '../../../core/models/home.models';
import { CharacterService } from '../../../core/services/character.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';
import { StyleService, type StyleOption } from '../../../core/services/style.service';
import { VoiceService, type SavedVoice } from '../../../core/services/voice.service';

type Tab = 'library' | 'manual' | 'ai';
type AiMode = 'prompt' | 'attrs';

const GENDERS = ['Feminino', 'Masculino', 'Outro', 'Não especificado'];
const BODY_TYPES = ['Magro', 'Médio', 'Atlético', 'Forte', 'Gordo'];
const SKIN_TONES = ['Clara', 'Morena', 'Negra'];

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
  private styleService = inject(StyleService);
  private voiceService = inject(VoiceService);
  private destroyRef = inject(DestroyRef);

  tab = signal<Tab>('library');
  characters = signal<CharacterOut[]>([]);
  projectStyle = signal('webtoon');
  projectColorMode = signal('tons-cinza');
  selectedIds = signal<Set<string>>(new Set());
  loading = signal(true);
  saving = signal(false);
  voices = signal<SavedVoice[]>([]);

  readonly genders = GENDERS;
  readonly bodyTypes = BODY_TYPES;
  readonly skinTones = SKIN_TONES;

  ethnicities = signal<AttrOption[]>([]);
  private styleCatalog = signal<StyleOption[]>([]);
  styleLabel = computed(() =>
    this.styleCatalog().find(s => s.id === this.projectStyle())?.label ?? this.projectStyle()
  );

  // Form manual
  mName = signal('');
  mRole = signal('Protagonista');
  mGender = signal('');
  mAge = signal('16');
  mHeight = signal('');
  mSummary = signal('');
  mOutfit = signal('');
  mTraits = signal('');
  mNarratorVoiceId = signal<string | null>(null);
  mSaving = signal(false);
  mGenerating = signal(false);
  mError = signal('');
  mCandidates = signal<AiCandidate[]>([]);
  mPicked = signal<string | null>(null);

  manualComplete = computed(() =>
    !!(this.mName().trim() && this.mRole().trim() && this.mGender() && this.mAge().trim()
       && this.mHeight().trim() && this.mSummary().trim() && this.mOutfit().trim() && this.mTraits().trim())
  );

  // IA
  aiMode = signal<AiMode>('prompt');
  aiGender = signal('');
  aiBodyType = signal('');
  aiSkinTone = signal('');
  aiEthnicity = signal('');
  aiPrompt = signal('Uma garota tímida de 16 anos, olhos grandes castanho-âmbar com brilho, franja reta, sempre carrega um caderno. Veste uniforme escolar.');
  aiAttrs = signal({ archetype: 'protagonista', age: '16', hair: 'preto, franja reta', eyes: 'âmbar, grandes', outfit: 'uniforme escolar', personality: 'tímida, curiosa', quirk: 'anota tudo em um caderno' });
  aiGenerating = signal(false);
  aiError = signal('');
  aiCandidates = signal<AiCandidate[]>([]);
  aiPicked = signal<string | null>(null);
  aiName = signal('');
  aiSaving = signal(false);

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
      next: groups => this.ethnicities.set(groups.find(g => g.id === 'ethnicity')?.options ?? []),
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

  // ── Manual form ──

  setField(sig: ReturnType<typeof signal<string>>, e: Event): void {
    sig.set((e.target as HTMLInputElement | HTMLTextAreaElement).value);
  }

  submitManual(): void {
    if (!this.mName().trim() || this.mSaving()) return;
    this.mSaving.set(true);
    const picked = this.mCandidates().find(c => c.id === this.mPicked());
    const req: CharacterCreate = {
      name: this.mName(),
      role: this.mRole() || 'Personagem',
      gender: this.mGender() || undefined,
      age: this.mAge() ? +this.mAge() : undefined,
      height: this.mHeight() || undefined,
      summary: this.mSummary() || undefined,
      outfit: this.mOutfit() || undefined,
      traits: this.mTraits().split(',').map(t => t.trim()).filter(Boolean),
      style: this.projectStyle(),
      narrator_voice_id: this.mNarratorVoiceId(),
    };
    if (picked) req.image_url = picked.imageUrl;
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
    this.mName.set(''); this.mRole.set('Protagonista'); this.mGender.set('');
    this.mAge.set('16'); this.mHeight.set('');
    this.mSummary.set(''); this.mOutfit.set(''); this.mTraits.set('');
    this.mNarratorVoiceId.set(null);
    this.mCandidates.set([]); this.mPicked.set(null); this.mError.set('');
  }

  private buildManualPrompt(): string {
    const v = (s: string) => s.trim();
    return [
      v(this.mName()),
      v(this.mRole()),
      v(this.mAge()) && `${v(this.mAge())} anos`,
      v(this.mHeight()) && `altura ${v(this.mHeight())}`,
      v(this.mSummary()),
      v(this.mOutfit()) && `figurino: ${v(this.mOutfit())}`,
      v(this.mTraits()) && `personalidade: ${v(this.mTraits())}`,
    ].filter(Boolean).join(', ');
  }

  generateManual(): void {
    if (!this.manualComplete() || this.mGenerating()) return;
    this.mGenerating.set(true);
    this.mError.set('');
    this.mCandidates.set([]);
    this.mPicked.set(null);
    this.portraitStream(this.buildManualPrompt(), this.mGender()).subscribe({
      next: job => {
        if (job.status === 'done') {
          this.mCandidates.set(this.toCandidates(job));
          this.mGenerating.set(false);
        } else if (job.status === 'error') {
          this.mError.set(job.detail || 'Erro ao gerar retratos.');
          this.mGenerating.set(false);
        }
      },
      error: err => {
        this.mGenerating.set(false);
        this.mError.set(err?.error?.detail ?? err?.message ?? 'Erro ao gerar retratos.');
      },
    });
  }

  pickManualCandidate(id: string): void {
    this.mPicked.set(this.mPicked() === id ? null : id);
  }

  // ── IA ──

  setAiAttr(key: string, e: Event): void {
    const value = (e.target as HTMLInputElement).value;
    this.aiAttrs.update(a => ({ ...a, [key]: value }));
  }

  private portraitStream(prompt: string, gender?: string, bodyType?: string, skinTone?: string, ethnicity?: string): Observable<PortraitJob> {
    return this.characterService.generatePortrait(prompt, this.projectStyle(), this.projectColorMode(), gender, bodyType, skinTone, ethnicity).pipe(
      switchMap(job =>
        timer(0, 3000).pipe(
          switchMap(() => this.characterService.pollPortraitJob(job.job_id)),
          takeWhile(j => j.status !== 'done' && j.status !== 'error', true),
        )
      ),
      takeUntilDestroyed(this.destroyRef),
    );
  }

  private toCandidates(job: PortraitJob): AiCandidate[] {
    return job.portraits.map(c => ({
      id: c.id,
      imageUrl: c.url.startsWith('http') ? c.url : `${environment.apiUrl}${c.url}`,
      notes: c.notes,
    }));
  }

  generateAi(): void {
    this.aiGenerating.set(true);
    this.aiError.set('');
    this.aiCandidates.set([]);
    this.aiPicked.set(null);

    const isAttrs = this.aiMode() === 'attrs';
    const prompt = isAttrs ? Object.values(this.aiAttrs()).filter(v => v.trim()).join(', ') : this.aiPrompt();
    const stream = isAttrs
      ? this.portraitStream(
          prompt,
          this.aiGender() || undefined,
          this.aiBodyType() || undefined,
          this.aiSkinTone() || undefined,
          this.aiEthnicity() || undefined,
        )
      : this.portraitStream(prompt);

    stream.subscribe({
      next: job => {
        if (job.status === 'done') {
          this.aiCandidates.set(this.toCandidates(job));
          this.aiGenerating.set(false);
        } else if (job.status === 'error') {
          this.aiError.set(job.detail || 'Erro ao gerar retratos.');
          this.aiGenerating.set(false);
        }
      },
      error: err => {
        this.aiGenerating.set(false);
        const msg = err?.error?.detail ?? err?.message ?? 'Erro ao gerar retratos.';
        this.aiError.set(msg);
      },
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
      gender: this.aiGender() || undefined,
      body_type: this.aiBodyType() || undefined,
      skin_tone: this.aiSkinTone() || undefined,
      ethnicity: this.aiEthnicity() || undefined,
      summary: this.aiMode() === 'prompt' ? this.aiPrompt() : Object.values(this.aiAttrs()).filter(v => v.trim()).join(', '),
      traits: ['gerado por IA'],
      style: this.projectStyle(),
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
    if (!force && ed && ed.project_count > 0) {
      this.eRegenWarn.set(true);
      return;
    }
    this.eRegenWarn.set(false);
    this.eGenerating.set(true);
    this.eError.set('');
    this.eCandidates.set([]);
    this.ePicked.set(null);

    this.portraitStream(this.eSummary(), this.eGender()).subscribe({
      next: job => {
        if (job.status === 'done') {
          this.eCandidates.set(this.toCandidates(job));
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

  saveEdit(): void {
    const current = this.editing();
    if (!current || !this.eName().trim() || this.eSaving()) return;
    this.eSaving.set(true);

    const picked = this.eCandidates().find(c => c.id === this.ePicked());
    const req: CharacterUpdate = {
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
