import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { MINIMAX_VOICES } from '../../core/data/minimax-voices';
import { SavedVoice, VoiceService } from '../../core/services/voice.service';
import { VoicePreviewButtonComponent } from '../../shared/voice-preview-button/voice-preview-button.component';

@Component({
  selector: 'app-voice-test',
  standalone: true,
  imports: [VoicePreviewButtonComponent],
  templateUrl: './voice-test.component.html',
})
export class VoiceTestComponent implements OnInit {
  private voiceService = inject(VoiceService);

  search = signal('');
  selectedId = signal(MINIMAX_VOICES[0].id);
  text = signal('Olá! Esta é uma voz de teste do MiniMax.');
  loading = signal(false);
  error = signal('');
  audioUrl = signal<string | null>(null);

  saved = signal<SavedVoice[]>([]);
  formName = signal('');
  formAgeStart = signal('');
  formAgeEnd = signal('');
  formSex = signal('');
  formDetails = signal('');
  saving = signal(false);
  saveError = signal('');
  editingId = signal<string | null>(null);

  private objectUrl: string | null = null;

  filtered = computed(() => {
    const q = this.search().trim().toLowerCase();
    if (!q) return MINIMAX_VOICES;
    return MINIMAX_VOICES.filter(
      v => v.id.toLowerCase().includes(q) || v.name.toLowerCase().includes(q),
    );
  });

  selectedLabel = computed(() => {
    const v = MINIMAX_VOICES.find(x => x.id === this.selectedId());
    return v ? `${v.name} · ${v.id}` : this.selectedId();
  });

  ngOnInit(): void {
    this.loadSaved();
  }

  private loadSaved(): void {
    this.voiceService.list().subscribe({
      next: voices => this.saved.set(voices),
      error: () => this.saved.set([]),
    });
  }

  selectVoice(id: string): void {
    this.selectedId.set(id);

    const minimaxVoice = MINIMAX_VOICES.find(v => v.id === id);
    const voiceName = minimaxVoice?.name ?? id;

    const existing = this.saved().find(v => v.voice_id === id);
    if (existing) {
      this.editingId.set(existing.id);
      this.formName.set(existing.name);
      this.formAgeStart.set(existing.age_start != null ? String(existing.age_start) : '');
      this.formAgeEnd.set(existing.age_end != null ? String(existing.age_end) : '');
      this.formSex.set(existing.sex ?? '');
      this.formDetails.set(existing.details ?? '');
    } else {
      this.editingId.set(null);
      this.formName.set(voiceName);
      this.formAgeStart.set('');
      this.formAgeEnd.set('');
      this.formSex.set('');
      this.formDetails.set('');
    }
    this.saveError.set('');
  }

  editSaved(v: SavedVoice): void {
    this.selectedId.set(v.voice_id);
    this.editingId.set(v.id);
    this.formName.set(v.name);
    this.formAgeStart.set(v.age_start != null ? String(v.age_start) : '');
    this.formAgeEnd.set(v.age_end != null ? String(v.age_end) : '');
    this.formSex.set(v.sex ?? '');
    this.formDetails.set(v.details ?? '');
    this.saveError.set('');
  }

  generate(): void {
    const text = this.text().trim();
    if (!text || this.loading()) return;
    this.loading.set(true);
    this.error.set('');
    this.voiceService.synthesize(text, this.selectedId()).subscribe({
      next: blob => {
        if (this.objectUrl) URL.revokeObjectURL(this.objectUrl);
        this.objectUrl = URL.createObjectURL(blob);
        this.audioUrl.set(this.objectUrl);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Falha ao gerar o áudio. Verifique a configuração do MiniMax.');
        this.loading.set(false);
      },
    });
  }

  save(): void {
    const name = this.formName().trim();
    if (!name || this.saving()) {
      if (!name) this.saveError.set('Informe o nome da voz.');
      return;
    }
    this.saving.set(true);
    this.saveError.set('');
    const ageStart = this.formAgeStart().trim();
    const ageEnd = this.formAgeEnd().trim();
    const payload = {
      name,
      voice_id: this.selectedId(),
      age_start: ageStart ? Number(ageStart) : null,
      age_end: ageEnd ? Number(ageEnd) : null,
      sex: this.formSex() || null,
      details: this.formDetails().trim() || null,
    };

    const editingId = this.editingId();
    if (editingId) {
      this.voiceService.update(editingId, payload).subscribe({
        next: updated => {
          this.saved.update(list =>
            list.map(v => (v.id === editingId ? updated : v)).sort((a, b) => a.name.localeCompare(b.name)),
          );
          this.resetForm();
          this.saving.set(false);
        },
        error: () => {
          this.saveError.set('Falha ao atualizar a voz.');
          this.saving.set(false);
        },
      });
    } else {
      this.voiceService.create(payload).subscribe({
        next: voice => {
          this.saved.update(list => [...list, voice].sort((a, b) => a.name.localeCompare(b.name)));
          this.resetForm();
          this.saving.set(false);
        },
        error: () => {
          this.saveError.set('Falha ao salvar a voz.');
          this.saving.set(false);
        },
      });
    }
  }

  remove(id: string): void {
    this.voiceService.delete(id).subscribe({
      next: () => {
        this.saved.update(list => list.filter(v => v.id !== id));
        if (this.editingId() === id) this.resetForm();
      },
    });
  }

  resetForm(): void {
    this.editingId.set(null);
    this.formName.set('');
    this.formAgeStart.set('');
    this.formAgeEnd.set('');
    this.formSex.set('');
    this.formDetails.set('');
    this.saveError.set('');
  }

  ageLabel(v: SavedVoice): string {
    if (v.age_start != null && v.age_end != null) return `${v.age_start}–${v.age_end} anos`;
    if (v.age_start != null) return `${v.age_start}+ anos`;
    if (v.age_end != null) return `até ${v.age_end} anos`;
    return '';
  }
}
