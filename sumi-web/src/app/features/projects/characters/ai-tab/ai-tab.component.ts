import { Component, DestroyRef, EventEmitter, Input, Output, inject, signal } from '@angular/core';
import type { AttrOption, CharacterCreate, CharacterOut } from '../../../../core/models/home.models';
import { CharacterService } from '../../../../core/services/character.service';
import { AiCandidate, portraitStream, toCandidates } from '../shared/portrait-stream';

type AiMode = 'prompt' | 'attrs';

@Component({
  selector: 'app-ai-tab',
  standalone: true,
  templateUrl: './ai-tab.component.html',
  styleUrl: './ai-tab.component.scss',
})
export class AiTabComponent {
  @Input({ required: true }) style!: string;
  @Input({ required: true }) colorMode!: string;
  @Input() genders: string[] = [];
  @Input() ethnicities: AttrOption[] = [];
  @Input() ageRanges: AttrOption[] = [];

  @Output() created = new EventEmitter<CharacterOut>();

  private characterService = inject(CharacterService);
  private destroyRef = inject(DestroyRef);

  mode = signal<AiMode>('prompt');
  name = signal('');
  gender = signal('');
  ageRange = signal('');
  ethnicity = signal('');
  hair = signal('preto, longo');
  extra = signal('');
  prompt = signal('Uma garota tímida de 16 anos, olhos grandes castanho-âmbar com brilho, franja reta, sempre carrega um caderno. Veste uniforme escolar.');
  generating = signal(false);
  error = signal('');
  candidates = signal<AiCandidate[]>([]);
  picked = signal<string | null>(null);
  saving = signal(false);

  setField(sig: ReturnType<typeof signal<string>>, e: Event): void {
    sig.set((e.target as HTMLInputElement | HTMLTextAreaElement).value);
  }

  generate(): void {
    this.generating.set(true);
    this.error.set('');
    this.candidates.set([]);
    this.picked.set(null);

    const isAttrs = this.mode() === 'attrs';
    const stream = isAttrs
      ? portraitStream(this.characterService, this.destroyRef, {
          style: this.style,
          colorMode: this.colorMode,
          gender: this.gender() || undefined,
          ageRange: this.ageRange() || undefined,
          ethnicity: this.ethnicity() || undefined,
          hair: this.hair() || undefined,
          extra: this.extra() || undefined,
        })
      : portraitStream(this.characterService, this.destroyRef, {
          style: this.style,
          colorMode: this.colorMode,
          prompt: this.prompt(),
          raw: true,
        });

    stream.subscribe({
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

  confirm(): void {
    if (!this.picked() || !this.name().trim() || this.saving()) return;
    const picked = this.candidates().find(c => c.id === this.picked());
    this.saving.set(true);
    const req: CharacterCreate = {
      name: this.name(),
      role: 'Personagem',
      gender: this.gender() || undefined,
      ethnicity: this.ethnicity() || undefined,
      summary: this.mode() === 'prompt'
        ? this.prompt()
        : [this.hair(), this.extra()].filter(v => v.trim()).join(', '),
      traits: ['gerado por IA'],
      style: this.style,
      image_url: picked?.imageUrl,
    };
    this.characterService.create(req).subscribe({
      next: char => {
        this.created.emit(char);
        this.candidates.set([]); this.picked.set(null); this.name.set('');
        this.saving.set(false);
      },
      error: () => this.saving.set(false),
    });
  }
}
