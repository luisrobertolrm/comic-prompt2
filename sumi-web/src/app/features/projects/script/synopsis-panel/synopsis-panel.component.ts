import { Component, ElementRef, EventEmitter, Input, Output, ViewChild, signal } from '@angular/core';
import { TextReaderComponent } from '../../../../shared/text-reader/text-reader.component';

export interface SynopsisSelection {
  start: number;
  end: number;
  text: string;
}

export interface SynopsisRange {
  start: number;
  end: number;
}

@Component({
  selector: 'app-synopsis-panel',
  standalone: true,
  imports: [TextReaderComponent],
  templateUrl: './synopsis-panel.component.html',
  styleUrl: './synopsis-panel.component.scss',
})
export class SynopsisPanelComponent {
  @Input() text = '';
  @Input() hasSynopsis = false;
  @Input() generating = false;
  @Input() temperature = 0.8;

  /** Trecho a destacar (ex.: o quadro vinculado sob o mouse). */
  @Input() set highlight(value: SynopsisRange | null) {
    this.activeRange.set(value && value.end > value.start ? { start: value.start, end: value.end } : null);
  }

  @Output() textChange = new EventEmitter<string>();
  @Output() regen = new EventEmitter<void>();
  @Output() temperatureChange = new EventEmitter<string>();
  @Output() selectionChange = new EventEmitter<SynopsisSelection | null>();

  @ViewChild('body') bodyRef?: ElementRef<HTMLElement>;

  editing = signal(false);
  draft = signal('');
  showReader = signal(false);
  protected activeRange = signal<SynopsisRange | null>(null);

  /** Faixa de destaque já validada contra o texto atual. */
  hl(): SynopsisRange | null {
    const r = this.activeRange();
    if (!r) return null;
    const len = this.text.length;
    const start = Math.max(0, Math.min(r.start, len));
    const end = Math.max(start, Math.min(r.end, len));
    return end > start ? { start, end } : null;
  }

  startEdit(): void {
    this.draft.set(this.text);
    this.editing.set(true);
  }

  save(): void {
    const value = this.draft().trim();
    this.editing.set(false);
    if (value && value !== this.text) this.textChange.emit(value);
  }

  cancel(): void {
    this.editing.set(false);
  }

  onSelect(): void {
    const sel = window.getSelection();
    const body = this.bodyRef?.nativeElement;
    if (!sel || !body || sel.rangeCount === 0) return;
    const range = sel.getRangeAt(0);
    if (range.collapsed || !body.contains(range.commonAncestorContainer)) return;

    const start = this.offsetWithin(body, range.startContainer, range.startOffset);
    const end = this.offsetWithin(body, range.endContainer, range.endOffset);
    if (end <= start) return;

    this.activeRange.set({ start, end });
    this.selectionChange.emit({ start, end, text: this.text.slice(start, end) });
  }

  clearSelection(): void {
    this.activeRange.set(null);
    this.selectionChange.emit(null);
  }

  /** Posição (em caracteres) de um ponto da seleção dentro do container. */
  private offsetWithin(container: HTMLElement, node: Node, offset: number): number {
    const r = document.createRange();
    r.selectNodeContents(container);
    r.setEnd(node, offset);
    return r.toString().length;
  }
}
