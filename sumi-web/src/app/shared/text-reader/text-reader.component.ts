import { Component, EventEmitter, HostListener, Input, Output } from '@angular/core';

@Component({
  selector: 'app-text-reader',
  standalone: true,
  template: `
    <div class="reader-backdrop" (click)="close.emit()">
      <div class="reader-card" (click)="$event.stopPropagation()">
        <div class="reader-head">
          <span class="reader-title">{{ title }}</span>
          <button class="reader-close" (click)="close.emit()" title="Fechar (Esc)">✕</button>
        </div>
        <div class="reader-body">
          @if (text.trim()) {
            <p class="reader-text">{{ text }}</p>
          } @else {
            <p class="reader-empty">Sem texto ainda.</p>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .reader-backdrop {
      position: fixed; inset: 0; z-index: 1000;
      background: rgba(20, 16, 12, 0.55);
      display: flex; align-items: center; justify-content: center;
      padding: 32px;
    }
    .reader-card {
      background: var(--paper, #fdfaf4);
      border-radius: 16px;
      box-shadow: 0 24px 64px rgba(0, 0, 0, 0.3);
      width: min(820px, 100%); max-height: 88vh;
      display: flex; flex-direction: column;
    }
    .reader-head {
      display: flex; align-items: center; justify-content: space-between;
      padding: 18px 24px; border-bottom: 1px solid var(--ink-4, #e6ddcf);
    }
    .reader-title {
      font-size: 13px; letter-spacing: 0.12em; text-transform: uppercase;
      color: var(--muted, #8a7d6b);
    }
    .reader-close {
      border: none; background: transparent; cursor: pointer;
      font-size: 18px; line-height: 1; color: var(--muted, #8a7d6b);
      padding: 4px 8px; border-radius: 8px;
    }
    .reader-close:hover { background: var(--paper-2, #f3ecdf); }
    .reader-body { overflow-y: auto; padding: 28px 32px; }
    .reader-text {
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 20px; line-height: 1.7; color: var(--ink, #2a241c);
      white-space: pre-wrap; margin: 0;
    }
    .reader-empty { color: var(--muted, #8a7d6b); font-style: italic; }
  `],
})
export class TextReaderComponent {
  @Input() text = '';
  @Input() title = 'Leitura';
  @Output() close = new EventEmitter<void>();

  @HostListener('document:keydown.escape')
  onEsc(): void { this.close.emit(); }
}
