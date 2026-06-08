import { Component, computed, signal } from '@angular/core';
import { inject } from '@angular/core';
import { MINIMAX_VOICES } from '../../core/data/minimax-voices';
import { VoiceService } from '../../core/services/voice.service';

@Component({
  selector: 'app-voice-test',
  standalone: true,
  templateUrl: './voice-test.component.html',
})
export class VoiceTestComponent {
  private voiceService = inject(VoiceService);

  search = signal('');
  selectedId = signal(MINIMAX_VOICES[0].id);
  text = signal('Olá! Esta é uma voz de teste do MiniMax.');
  loading = signal(false);
  error = signal('');
  audioUrl = signal<string | null>(null);

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

  selectVoice(id: string): void {
    this.selectedId.set(id);
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
}
