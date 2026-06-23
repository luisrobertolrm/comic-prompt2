import { Component, EventEmitter, HostListener, Input, Output, signal } from '@angular/core';
import { MangaPanelComponent } from '../../manga-panel/manga-panel.component';
import type { PanelOut } from '../../../../core/models/panel.models';
import type { SynopsisRange } from '../synopsis-panel/synopsis-panel.component';

@Component({
  selector: 'app-script-panel-card',
  standalone: true,
  imports: [MangaPanelComponent],
  templateUrl: './panel-card.component.html',
  styleUrl: './panel-card.component.scss',
})
export class PanelCardComponent {
  @Input({ required: true }) panel!: PanelOut;
  @Input() loading = false;
  @Input() generatingContent = false;
  @Input() canRemove = true;
  @Input() canLink = false;
  @Input() selectable = false;
  @Input() selected = false;
  @Input() synopsisText = '';

  showTrecho = signal(false);

  @Output() open = new EventEmitter<void>();
  @Output() insertAfter = new EventEmitter<void>();
  @Output() remove = new EventEmitter<void>();
  @Output() generate = new EventEmitter<void>();
  @Output() highlight = new EventEmitter<SynopsisRange | null>();
  @Output() link = new EventEmitter<void>();
  @Output() toggleSelect = new EventEmitter<void>();

  hasLink(): boolean {
    return this.panel.synopsis_start != null && this.panel.synopsis_end != null;
  }

  trechoText(): string {
    const s = this.panel.synopsis_start;
    const e = this.panel.synopsis_end;
    if (s == null || e == null) return '';
    const len = this.synopsisText.length;
    const start = Math.max(0, Math.min(s, len));
    const end = Math.max(start, Math.min(e, len));
    return this.synopsisText.slice(start, end);
  }

  toggleTrecho(): void {
    this.showTrecho.update(v => !v);
  }

  statusColor(): string {
    return this.panel.status === 'approved' ? 'var(--mint)' : 'var(--peach-soft)';
  }

  statusLabel(): string {
    return this.panel.status === 'approved' ? 'OK' : 'REVISAR';
  }

  @HostListener('mouseenter')
  onEnter(): void {
    if (this.hasLink()) {
      this.highlight.emit({ start: this.panel.synopsis_start!, end: this.panel.synopsis_end! });
    }
  }

  @HostListener('mouseleave')
  onLeave(): void {
    this.highlight.emit(null);
    this.showTrecho.set(false);
  }
}
