import { Component, EventEmitter, HostListener, Input, Output } from '@angular/core';
import { NgStyle } from '@angular/common';
import type { Bubble } from '../../../core/models/panel.models';
import { environment } from '../../../../environments/environment';

const PALETTES = ['#F4D6D7', '#F6DEC2', '#DBEADF', '#E1D8EC', '#D8E2EC'];

function toneFor(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = ((h * 31) + name.charCodeAt(i)) >>> 0;
  return PALETTES[h % PALETTES.length];
}

@Component({
  selector: 'app-manga-panel',
  standalone: true,
  imports: [NgStyle],
  templateUrl: './manga-panel.component.html',
  styleUrl: './manga-panel.component.scss',
})
export class MangaPanelComponent {
  @Input() index = 1;
  @Input() label = '';
  @Input() aspect = '4-3';
  @Input() tone = 'dots';
  @Input() characterName: string | null = null;
  @Input() bubbles: Bubble[] = [];
  @Input() isLoading = false;
  @Input() imageUrl: string | null = null;
  @Input() interactive = false;

  @Output() bubbleDrag = new EventEmitter<{ idx: number; x: number; y: number }>();
  @Output() bubbleDragEnd = new EventEmitter<{ idx: number; x: number; y: number }>();

  private dragging: { idx: number; rect: DOMRect; lastX: number; lastY: number } | null = null;

  get fullImageUrl(): string | null {
    return this.imageUrl ? `${environment.apiUrl}${this.imageUrl}` : null;
  }

  get aspectRatio(): string {
    const map: Record<string, string> = { '4-3': '4/3', '3-4': '3/4', '16-9': '16/9', '1-1': '1/1' };
    return map[this.aspect] ?? '4/3';
  }

  get patternBg(): string {
    if (this.tone === 'diag') return 'repeating-linear-gradient(45deg,rgba(30,24,18,.18) 0 1px,transparent 1px 6px)';
    if (this.tone === 'dense') return 'radial-gradient(circle,rgba(30,24,18,.22) .7px,transparent 1px)';
    return 'radial-gradient(circle,rgba(30,24,18,.18) .6px,transparent 1px)';
  }

  get patternSize(): string { return this.tone === 'dense' ? '5px 5px' : '7px 7px'; }
  get charColor(): string { return this.characterName ? toneFor(this.characterName) : '#F4D6D7'; }
  get charInitial(): string { return this.characterName ? this.characterName.charAt(0).toUpperCase() : '?'; }

  bubbleClass(b: Bubble): string {
    return [
      'bubble',
      b.kind !== 'say' ? b.kind : '',
      b.side === 'right' ? 'right' : '',
      b.tail !== 'none' ? `tail-${b.tail}` : '',
    ].filter(Boolean).join(' ');
  }

  bubbleStyle(b: Bubble): Record<string, string> {
    const style: Record<string, string> = { top: `${b.y}%` };
    if (b.side === 'right') style['right'] = `${b.x}%`;
    else style['left'] = `${b.x}%`;
    if (this.interactive) style['cursor'] = 'grab';
    return style;
  }

  indexLabel(): string {
    return `PANEL · ${String(this.index).padStart(2, '0')}${this.label ? ' · ' + this.label : ''}`;
  }

  onBubbleMousedown(idx: number, event: MouseEvent): void {
    if (!this.interactive) return;
    event.preventDefault();
    event.stopPropagation();
    const el = event.currentTarget as HTMLElement;
    const container = el.closest('.panel-wrap') as HTMLElement;
    const { lastX, lastY } = this.posFromEvent(event, container.getBoundingClientRect());
    this.dragging = { idx, rect: container.getBoundingClientRect(), lastX, lastY };
  }

  @HostListener('document:mousemove', ['$event'])
  onMouseMove(e: MouseEvent): void {
    if (!this.dragging) return;
    const { rect, idx } = this.dragging;
    const { lastX, lastY } = this.posFromEvent(e, rect);
    this.dragging.lastX = lastX;
    this.dragging.lastY = lastY;
    this.bubbleDrag.emit({ idx, x: lastX, y: lastY });
  }

  @HostListener('document:mouseup')
  onMouseUp(): void {
    if (!this.dragging) return;
    this.bubbleDragEnd.emit({ idx: this.dragging.idx, x: this.dragging.lastX, y: this.dragging.lastY });
    this.dragging = null;
  }

  private posFromEvent(e: MouseEvent, rect: DOMRect): { lastX: number; lastY: number } {
    const lastX = Math.max(0, Math.min(80, ((e.clientX - rect.left) / rect.width) * 100 - 5));
    const lastY = Math.max(0, Math.min(78, ((e.clientY - rect.top) / rect.height) * 100 - 5));
    return { lastX: Math.round(lastX), lastY: Math.round(lastY) };
  }
}
