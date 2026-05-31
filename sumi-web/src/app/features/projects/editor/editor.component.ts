import { Component, DestroyRef, HostListener, inject, OnInit, signal, computed } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { NgStyle } from '@angular/common';
import { Subject, debounceTime, switchMap } from 'rxjs';
import type { Bubble, PanelOut, PanelPatch } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { environment } from '../../../../environments/environment';

interface LayoutSlot { gridColumn: string; gridRow: string; }
interface Layout { label: string; cols: string; rows: string; gap: string; aspect: string; slots: LayoutSlot[]; }

const LAYOUTS: Record<string, Layout> = {
  'manga-vertical': {
    label: 'Mangá vertical', cols: '1fr', rows: '1.1fr 0.9fr 1fr 1.1fr',
    gap: '10px', aspect: '5/8',
    slots: [
      { gridColumn: '1', gridRow: '1' }, { gridColumn: '1', gridRow: '2' },
      { gridColumn: '1', gridRow: '3' }, { gridColumn: '1', gridRow: '4' },
    ],
  },
  'grid': {
    label: 'Grade ocidental', cols: '1fr 1fr', rows: '1fr 1fr 1fr',
    gap: '10px', aspect: '5/7',
    slots: [
      { gridColumn: '1 / span 2', gridRow: '1' }, { gridColumn: '1', gridRow: '2' },
      { gridColumn: '2', gridRow: '2' }, { gridColumn: '1', gridRow: '3' },
      { gridColumn: '2', gridRow: '3' },
    ],
  },
  'dynamic': {
    label: 'Dinâmico mangá', cols: '2fr 1fr 1.4fr', rows: '1.2fr 1fr 1fr',
    gap: '10px', aspect: '5/7',
    slots: [
      { gridColumn: '1 / span 2', gridRow: '1' }, { gridColumn: '3', gridRow: '1 / span 2' },
      { gridColumn: '1', gridRow: '2 / span 2' }, { gridColumn: '2', gridRow: '2' },
      { gridColumn: '2 / span 2', gridRow: '3' },
    ],
  },
};

const READING_DIRS = ['Ocidental →', 'Mangá ←', 'Vertical ↓'];

interface DragState { panelId: string; bubbleIdx: number; rect: DOMRect; }

@Component({
  selector: 'app-editor',
  standalone: true,
  imports: [NgStyle],
  templateUrl: './editor.component.html',
  styleUrl: './editor.component.scss',
})
export class EditorComponent implements OnInit {
  private route       = inject(ActivatedRoute);
  private router      = inject(Router);
  private panelService = inject(PanelService);
  private destroyRef  = inject(DestroyRef);

  readonly layoutKeys  = Object.keys(LAYOUTS);
  readonly readingDirs = READING_DIRS;
  readonly apiUrl      = environment.apiUrl;

  projectId  = signal('');
  panels     = signal<PanelOut[]>([]);
  loading    = signal(true);
  layout     = signal('manga-vertical');
  selectedId = signal('');
  readingDir = signal(READING_DIRS[0]);
  page       = signal(0);

  private dragging: DragState | null = null;
  private patchSubject = new Subject<{ id: string; patch: PanelPatch }>();

  get currentLayout(): Layout { return LAYOUTS[this.layout()]; }

  get slotsPerPage(): number { return this.currentLayout.slots.length; }

  totalPages = computed(() => Math.max(1, Math.ceil(this.panels().length / this.slotsPerPage)));

  visiblePanels = computed(() => {
    const start = this.page() * this.slotsPerPage;
    return this.panels().slice(start, start + this.slotsPerPage);
  });

  get selectedPanel(): PanelOut | undefined {
    return this.panels().find(p => p.id === this.selectedId());
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.projectId.set(id);

    this.panelService.list(id).subscribe({
      next: ps => {
        this.panels.set(ps);
        if (ps.length) this.selectedId.set(ps[0].id);
        this.loading.set(false);
      },
    });

    this.patchSubject.pipe(
      debounceTime(500),
      switchMap(({ id: pid, patch }) => this.panelService.update(pid, patch)),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe();
  }

  // ── Layout ──

  setLayout(key: string): void {
    this.layout.set(key);
    this.page.set(0);
  }

  layoutLabel(key: string): string { return LAYOUTS[key]?.label ?? key; }

  slotStyle(i: number): Record<string, string> {
    return this.currentLayout.slots[i] as unknown as Record<string, string>;
  }

  stageStyle(): Record<string, string> {
    const l = this.currentLayout;
    return { 'grid-template-columns': l.cols, 'grid-template-rows': l.rows, gap: l.gap, 'aspect-ratio': l.aspect };
  }

  // ── Paginação ──

  prevPage(): void { if (this.page() > 0) this.page.update(p => p - 1); }
  nextPage(): void { if (this.page() < this.totalPages() - 1) this.page.update(p => p + 1); }

  // ── Seleção ──

  isSelected(id: string): boolean { return this.selectedId() === id; }

  selectPanel(id: string, listIndex: number): void {
    this.selectedId.set(id);
    this.page.set(Math.floor(listIndex / this.slotsPerPage));
  }

  padNum(n: number): string { return String(n).padStart(2, '0'); }

  // ── Drag de balões ──

  startDrag(panelId: string, bubbleIdx: number, event: MouseEvent): void {
    event.stopPropagation();
    event.preventDefault(); // evita drag nativo do browser no texto
    const bubbleEl = event.currentTarget as HTMLElement;
    const containerEl = bubbleEl.parentElement!;
    this.dragging = { panelId, bubbleIdx, rect: containerEl.getBoundingClientRect() };
  }

  @HostListener('document:mousemove', ['$event'])
  onMouseMove(e: MouseEvent): void {
    if (!this.dragging) return;
    const { rect, panelId, bubbleIdx } = this.dragging;
    const x = Math.max(0, Math.min(80, ((e.clientX - rect.left) / rect.width) * 100 - 8));
    const y = Math.max(0, Math.min(85, ((e.clientY - rect.top) / rect.height) * 100 - 6));
    this.panels.update(ps => ps.map(p => p.id !== panelId ? p : {
      ...p,
      bubbles: p.bubbles.map((b, i) => i === bubbleIdx ? { ...b, x: Math.round(x), y: Math.round(y) } : b),
    }));
  }

  @HostListener('document:mouseup')
  onMouseUp(): void {
    if (!this.dragging) return;
    const panel = this.panels().find(p => p.id === this.dragging!.panelId);
    if (panel) this.patchSubject.next({ id: panel.id, patch: { bubbles: panel.bubbles } });
    this.dragging = null;
  }

  // ── Estilos ──

  bubbleStyle(b: Bubble): Record<string, string> {
    return {
      left:  b.side === 'left'  ? `${b.x}%` : 'auto',
      right: b.side === 'right' ? `${b.x}%` : 'auto',
      top:   `${b.y}%`,
    };
  }

  tonePattern(tone: string): string {
    const alpha = tone === 'dense' ? '.22' : '.18';
    return `radial-gradient(circle,rgba(30,24,18,${alpha}) .6px,transparent 1px)`;
  }

  toneBgSize(tone: string): string { return tone === 'dense' ? '4px 4px' : '6px 6px'; }

  bubbleClass(b: Bubble): string {
    return ['bubble', b.kind === 'thought' ? 'thought' : b.kind === 'shout' ? 'shout' : '']
      .filter(Boolean).join(' ');
  }

  imageUrl(panel: PanelOut): string {
    return panel.image_url ? `${this.apiUrl}${panel.image_url}` : '';
  }

  goReview(): void { void this.router.navigate(['/projects', this.projectId(), 'review']); }
  goFinal(): void  { void this.router.navigate(['/projects', this.projectId(), 'final']); }
}
