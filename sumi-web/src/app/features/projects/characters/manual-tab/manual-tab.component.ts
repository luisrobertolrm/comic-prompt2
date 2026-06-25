import { Component, DestroyRef, EventEmitter, Input, Output, computed, inject, signal } from '@angular/core';
import type { CharacterCreate, CharacterOut } from '../../../../core/models/home.models';
import { CharacterService } from '../../../../core/services/character.service';
import type { SavedVoice } from '../../../../core/services/voice.service';
import { AiCandidate, portraitStream, toCandidates } from '../shared/portrait-stream';

@Component({
  selector: 'app-manual-tab',
  standalone: true,
  templateUrl: './manual-tab.component.html',
  styleUrl: './manual-tab.component.scss',
})
export class ManualTabComponent {
  @Input({ required: true }) style!: string;
  @Input({ required: true }) colorMode!: string;
  @Input() voices: SavedVoice[] = [];
  @Input() genders: string[] = [];

  @Output() created = new EventEmitter<CharacterOut>();

  private characterService = inject(CharacterService);
  private destroyRef = inject(DestroyRef);

  name = signal('');
  role = signal('Protagonista');
  gender = signal('');
  age = signal('16');
  height = signal('');
  summary = signal('');
  outfit = signal('');
  traits = signal('');
  narratorVoiceId = signal<string | null>(null);
  saving = signal(false);
  generating = signal(false);
  error = signal('');
  candidates = signal<AiCandidate[]>([]);
  picked = signal<string | null>(null);

  complete = computed(() =>
    !!(this.name().trim() && this.role().trim() && this.gender() && this.age().trim()
       && this.height().trim() && this.summary().trim() && this.outfit().trim() && this.traits().trim())
  );

  setField(sig: ReturnType<typeof signal<string>>, e: Event): void {
    sig.set((e.target as HTMLInputElement | HTMLTextAreaElement).value);
  }

  initial(name: string): string {
    return name.charAt(0).toUpperCase();
  }

  voiceMeta(v: SavedVoice): string {
    const parts: string[] = [];
    if (v.sex) parts.push(v.sex);
    if (v.age_start != null || v.age_end != null) {
      parts.push(`${v.age_start ?? '?'}–${v.age_end ?? '?'} anos`);
    }
    return parts.join(' · ');
  }

  private buildPrompt(): string {
    const v = (s: string) => s.trim();
    return [
      v(this.name()),
      v(this.role()),
      v(this.age()) && `${v(this.age())} anos`,
      v(this.height()) && `altura ${v(this.height())}`,
      v(this.summary()),
      v(this.outfit()) && `figurino: ${v(this.outfit())}`,
      v(this.traits()) && `personalidade: ${v(this.traits())}`,
    ].filter(Boolean).join(', ');
  }

  generate(): void {
    if (!this.complete() || this.generating()) return;
    this.generating.set(true);
    this.error.set('');
    this.candidates.set([]);
    this.picked.set(null);
    portraitStream(this.characterService, this.destroyRef, {
      style: this.style,
      colorMode: this.colorMode,
      gender: this.gender(),
      extra: this.buildPrompt(),
    }).subscribe({
      next: job => {
        if (job.status === 'done') {
          this.candidates.set(toCandidates(job));
          this.generating.set(false);
        } else if (job.status === 'error') {
          this.error.set(job.detail || 'Erro ao gerar retratos.');
          this.generating.set(false);
        }
      },
      error: err => {
        this.generating.set(false);
        this.error.set(err?.error?.detail ?? err?.message ?? 'Erro ao gerar retratos.');
      },
    });
  }

  pickCandidate(id: string): void {
    this.picked.set(this.picked() === id ? null : id);
  }

  submit(): void {
    if (!this.name().trim() || this.saving()) return;
    this.saving.set(true);
    const picked = this.candidates().find(c => c.id === this.picked());
    const req: CharacterCreate = {
      name: this.name(),
      role: this.role() || 'Personagem',
      gender: this.gender() || undefined,
      age: this.age() ? +this.age() : undefined,
      height: this.height() || undefined,
      summary: this.summary() || undefined,
      outfit: this.outfit() || undefined,
      traits: this.traits().split(',').map(t => t.trim()).filter(Boolean),
      style: this.style,
      narrator_voice_id: this.narratorVoiceId(),
    };
    if (picked) req.image_url = picked.imageUrl;
    this.characterService.create(req).subscribe({
      next: char => {
        this.created.emit(char);
        this.reset();
        this.saving.set(false);
      },
      error: () => this.saving.set(false),
    });
  }

  private reset(): void {
    this.name.set(''); this.role.set('Protagonista'); this.gender.set('');
    this.age.set('16'); this.height.set('');
    this.summary.set(''); this.outfit.set(''); this.traits.set('');
    this.narratorVoiceId.set(null);
    this.candidates.set([]); this.picked.set(null); this.error.set('');
  }
}
