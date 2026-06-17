import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MangaPanelComponent } from '../../manga-panel/manga-panel.component';
import type { PanelOut } from '../../../../core/models/panel.models';

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
  @Input() canRemove = true;

  @Output() open = new EventEmitter<void>();
  @Output() insertAfter = new EventEmitter<void>();
  @Output() remove = new EventEmitter<void>();

  statusColor(): string {
    return this.panel.status === 'approved' ? 'var(--mint)' : 'var(--peach-soft)';
  }

  statusLabel(): string {
    return this.panel.status === 'approved' ? 'OK' : 'REVISAR';
  }
}
