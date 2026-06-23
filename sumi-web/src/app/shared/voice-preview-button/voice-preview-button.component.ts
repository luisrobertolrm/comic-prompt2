import { Component, Input, OnDestroy, inject, signal } from '@angular/core';
import { VoiceService } from '../../core/services/voice.service';

@Component({
  selector: 'app-voice-preview-button',
  standalone: true,
  template: `
    <button type="button" class="voice-preview-btn" (click)="toggle($event)"
            [disabled]="loading()" [title]="playing() ? 'Parar' : 'Ouvir a voz'">
      @if (loading()) { ⏳ } @else if (playing()) { ⏸ } @else { ▶ }
    </button>
  `,
  styles: [`
    .voice-preview-btn {
      flex-shrink: 0;
      width: 30px;
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      line-height: 1;
      border: 1px solid var(--rule, #e5e0d8);
      border-radius: 999px;
      background: var(--paper, #fdfaf4);
      color: var(--ink, #2a241c);
      cursor: pointer;
      transition: background .15s ease, color .15s ease;
    }
    .voice-preview-btn:hover:not(:disabled) { background: var(--ink, #2a241c); color: var(--paper, #fdfaf4); }
    .voice-preview-btn:disabled { opacity: .5; cursor: default; }
  `],
})
export class VoicePreviewButtonComponent implements OnDestroy {
  private voiceService = inject(VoiceService);

  @Input({ required: true }) voiceId!: string;
  @Input() sampleText = 'Olá! Esta é uma prévia da minha voz para a narração.';

  loading = signal(false);
  playing = signal(false);

  private audio: HTMLAudioElement | null = null;
  private objectUrl: string | null = null;

  toggle(e: Event): void {
    e.stopPropagation();
    if (this.playing()) { this.stop(); return; }
    if (this.loading()) return;

    this.loading.set(true);
    this.voiceService.synthesize(this.sampleText, this.voiceId).subscribe({
      next: blob => {
        this.cleanup();
        this.objectUrl = URL.createObjectURL(blob);
        this.audio = new Audio(this.objectUrl);
        this.audio.onended = () => this.playing.set(false);
        void this.audio.play();
        this.playing.set(true);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  private stop(): void {
    if (this.audio) { this.audio.pause(); this.audio.currentTime = 0; }
    this.playing.set(false);
  }

  private cleanup(): void {
    if (this.audio) { this.audio.pause(); this.audio = null; }
    if (this.objectUrl) { URL.revokeObjectURL(this.objectUrl); this.objectUrl = null; }
  }

  ngOnDestroy(): void {
    this.cleanup();
  }
}
