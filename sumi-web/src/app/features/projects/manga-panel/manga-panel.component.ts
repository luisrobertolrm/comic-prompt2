import { Component, Input } from '@angular/core';
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

  get patternSize(): string {
    return this.tone === 'dense' ? '5px 5px' : '7px 7px';
  }

  get charColor(): string {
    return this.characterName ? toneFor(this.characterName) : '#F4D6D7';
  }

  get charInitial(): string {
    return this.characterName ? this.characterName.charAt(0).toUpperCase() : '?';
  }

  bubbleClass(b: Bubble): string {
    return ['bubble', b.kind === 'thought' ? 'thought' : b.kind === 'shout' ? 'shout' : '', b.side === 'right' ? 'right' : ''].filter(Boolean).join(' ');
  }

  bubbleStyle(b: Bubble): Record<string, string> {
    return {
      top: `${b.y}%`,
      ...(b.side === 'right' ? { right: `${b.x}%` } : { left: `${b.x}%` }),
    };
  }

  indexLabel(): string {
    return `PANEL · ${String(this.index).padStart(2, '0')}${this.label ? ' · ' + this.label : ''}`;
  }
}
