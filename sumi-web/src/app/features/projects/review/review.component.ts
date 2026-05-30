import { Component, DestroyRef, HostListener, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, debounceTime, switchMap } from 'rxjs';
import type { Bubble, PanelOut, PanelPatch } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { MangaPanelComponent } from '../manga-panel/manga-panel.component';

const FRAMINGS = [
  'Plano geral', 'Plano americano', 'Plano médio', 'Close-up',
  'Extreme close', 'Inserto', 'Detalhe', 'Plongée', 'Contra-plongée',
];

@Component({
  selector: 'app-review',
  standalone: true,
  imports: [MangaPanelComponent],
  templateUrl: './review.component.html',
  styleUrl: './review.component.scss',
})
export class ReviewComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private panelService = inject(PanelService);
  private destroyRef = inject(DestroyRef);

  readonly framings = FRAMINGS;

  projectId = signal('');
  panels = signal<PanelOut[]>([]);
  idx = signal(0);
  loading = signal(true);
  regenAnim = signal(false);
  showFramingPicker = signal(false);
  generatingImage = signal(false);

  private patchSubject = new Subject<{ id: string; patch: PanelPatch }>();

  get cur(): PanelOut | undefined { return this.panels()[this.idx()]; }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    const startPanel = +(this.route.snapshot.queryParams['panel'] ?? 0);
    this.projectId.set(id);

    this.panelService.list(id).subscribe({
      next: panels => {
        this.panels.set(panels);
        this.idx.set(Math.min(startPanel, Math.max(0, panels.length - 1)));
        this.loading.set(false);
      },
    });

    this.patchSubject.pipe(
      debounceTime(600),
      switchMap(({ id: pid, patch }) => this.panelService.update(pid, patch)),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe();
  }

  @HostListener('document:keydown', ['$event'])
  onKey(e: KeyboardEvent): void {
    if ((e.target as HTMLElement).tagName === 'TEXTAREA') return;
    if ((e.target as HTMLElement).tagName === 'INPUT') return;
    if (e.key === 'ArrowRight') this.next();
    else if (e.key === 'ArrowLeft') this.prev();
  }

  prev(): void { if (this.idx() > 0) this.idx.update(i => i - 1); }
  next(): void { if (this.idx() < this.panels().length - 1) this.idx.update(i => i + 1); }
  jumpTo(i: number): void { this.idx.set(i); }

  patchCur(patch: PanelPatch): void {
    const cur = this.cur;
    if (!cur) return;
    this.panels.update(ps => ps.map((p, i) => i === this.idx() ? { ...p, ...patch } : p));
    this.patchSubject.next({ id: cur.id, patch });
  }

  approve(): void {
    this.patchCur({ status: 'approved' });
    if (this.idx() < this.panels().length - 1) this.idx.update(i => i + 1);
  }

  regen(): void {
    const cur = this.cur;
    if (!cur) return;
    this.regenAnim.set(true);
    const tones: Record<string, string> = { dots: 'diag', diag: 'dense', dense: 'dots' };
    setTimeout(() => {
      this.patchCur({ tone: tones[cur.tone] ?? 'dots' });
      this.regenAnim.set(false);
    }, 900);
  }

  deletePanel(): void {
    if (this.panels().length <= 1) return;
    const cur = this.cur;
    if (!cur) return;
    this.panelService.delete(cur.id).subscribe({
      next: () => {
        const newPanels = this.panels()
          .filter(p => p.id !== cur.id)
          .map((p, i) => ({ ...p, index_order: i + 1 }));
        this.panels.set(newPanels);
        this.idx.set(Math.min(this.idx(), newPanels.length - 1));
      },
    });
  }

  movePanel(dir: -1 | 1): void {
    const j = this.idx() + dir;
    if (j < 0 || j >= this.panels().length) return;
    const ps = [...this.panels()];
    [ps[this.idx()], ps[j]] = [ps[j], ps[this.idx()]];
    const reindexed = ps.map((p, i) => ({ ...p, index_order: i + 1 }));
    this.panels.set(reindexed);
    this.idx.set(j);
    this.panelService.reorder(this.projectId(), reindexed.map(p => p.id)).subscribe();
  }

  insertPanel(): void {
    this.panelService.insert(this.projectId(), this.idx() + 1).subscribe({
      next: newPanel => {
        const ps = [
          ...this.panels().slice(0, this.idx() + 1),
          newPanel,
          ...this.panels().slice(this.idx() + 1),
        ].map((p, i) => ({ ...p, index_order: i + 1 }));
        this.panels.set(ps);
        this.idx.update(i => i + 1);
      },
    });
  }

  setCaption(e: Event): void {
    this.patchCur({ caption: (e.target as HTMLTextAreaElement).value });
  }

  setPrompt(e: Event): void {
    this.patchCur({ prompt: (e.target as HTMLTextAreaElement).value });
  }

  setFraming(f: string): void {
    this.patchCur({ framing: f });
    this.showFramingPicker.set(false);
  }

  addBubble(): void {
    const cur = this.cur;
    if (!cur) return;
    const bubble: Bubble = { text: 'Novo balão', kind: 'say', side: 'left', x: 8, y: 12 };
    this.patchCur({ bubbles: [...cur.bubbles, bubble] });
  }

  updateBubble(i: number, patch: Partial<Bubble>): void {
    const cur = this.cur;
    if (!cur) return;
    const updated = cur.bubbles.map((b, j) => j === i ? { ...b, ...patch } : b);
    this.patchCur({ bubbles: updated });
  }

  removeBubble(i: number): void {
    const cur = this.cur;
    if (!cur) return;
    this.patchCur({ bubbles: cur.bubbles.filter((_, j) => j !== i) });
  }

  padNum(n: number): string { return String(n).padStart(2, '0'); }

  progressDot(p: PanelOut): string {
    return p.status === 'approved' ? 'var(--mint)' : 'var(--ink-4)';
  }

  progressBg(i: number): string {
    return this.panels()[i]?.status === 'approved' ? 'var(--mint-soft)' : 'var(--paper-2)';
  }

  generateImage(): void {
    const cur = this.cur;
    if (!cur || this.generatingImage()) return;
    this.generatingImage.set(true);
    this.panelService.generateImage(cur.id).subscribe({
      next: updated => {
        this.panels.update(ps => ps.map(p => p.id === updated.id ? updated : p));
        this.generatingImage.set(false);
      },
      error: () => this.generatingImage.set(false),
    });
  }

  goScript(): void { void this.router.navigate(['/projects', this.projectId(), 'script']); }
  goEditor(): void { void this.router.navigate(['/projects', this.projectId(), 'editor']); }
  goFinal(): void { void this.router.navigate(['/projects', this.projectId(), 'final']); }
}
