import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { from, of } from 'rxjs';
import { catchError, finalize, map, mergeMap } from 'rxjs/operators';
import type { ProjectDetailOut } from '../../../core/models/home.models';
import type { PanelOut } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { ProjectService } from '../../../core/services/project.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { StyleService, StyleOption } from '../../../core/services/style.service';
import { MangaPanelComponent } from '../manga-panel/manga-panel.component';
import { SynopsisPanelComponent, SynopsisSelection, SynopsisRange } from './synopsis-panel/synopsis-panel.component';
import { PanelCardComponent } from './panel-card/panel-card.component';

@Component({
  selector: 'app-script',
  standalone: true,
  imports: [MangaPanelComponent, SynopsisPanelComponent, PanelCardComponent],
  templateUrl: './script.component.html',
  styleUrl: './script.component.scss',
})
export class ScriptComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private projectService = inject(ProjectService);
  private panelService = inject(PanelService);
  private draft = inject(ProjectDraftService);
  private styleService = inject(StyleService);

  styles = signal<StyleOption[]>([]);
  colorModes = signal<StyleOption[]>([]);

  projectId = signal('');
  project = signal<ProjectDetailOut | null>(null);
  panels = signal<PanelOut[]>([]);
  generating = signal(false);
  generatingImages = signal(false);
  generatingPanelIds = signal<Set<string>>(new Set());
  imagesDone = signal(0);
  targetPanels = signal<number | null>(null);

  private readonly IMAGE_CONCURRENCY = 3;
  skeletons = [1, 2, 3, 4, 5, 6, 7];
  generatingSynopsis = signal(false);
  selectedTrecho = signal<SynopsisSelection | null>(null);
  trechoHighlight = signal<SynopsisRange | null>(null);

  synopsisText(): string {
    const p = this.project();
    return p ? (p.synopsis || p.premise || p.title || '') : '';
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.projectId.set(id);
    this.projectService.get(id).subscribe({ next: p => { this.project.set(p); this.draft.currentProjectTitle.set(p.title); } });
    this.styleService.catalog().subscribe({
      next: c => { this.styles.set(c.styles); this.colorModes.set(c.color_modes); },
    });
    this.loadPanels(id);
  }

  styleLabel(): string {
    const p = this.project();
    if (!p) return '';
    const style = this.styles().find(s => s.id === p.style)?.label ?? p.style;
    const color = this.colorModes().find(c => c.id === p.color_mode)?.label ?? p.color_mode;
    return color ? `${style} · ${color}` : style;
  }

  private loadPanels(id: string): void {
    this.panelService.list(id).subscribe({
      next: panels => this.panels.set(panels),
    });
  }

  runGenerate(): void {
    this.generating.set(true);
    this.panels.set([]);
    this.panelService.generate(this.projectId(), this.targetPanels()).subscribe({
      next: panels => {
        this.panels.set(panels);
        this.targetPanels.set(panels.length);
        this.generating.set(false);
      },
      error: () => this.generating.set(false),
    });
  }

  insertAfter(i: number): void {
    const after = this.panels()[i].index_order;
    this.panelService.insert(this.projectId(), after).subscribe({
      next: newPanel => {
        const ps = [...this.panels().slice(0, i + 1), newPanel, ...this.panels().slice(i + 1)]
          .map((p, idx) => ({ ...p, index_order: idx + 1 }));
        this.panels.set(ps);
        this.targetPanels.set(ps.length);
      },
    });
  }

  insertAtStart(): void {
    this.panelService.insert(this.projectId(), 0).subscribe({
      next: newPanel => {
        const ps = [newPanel, ...this.panels()].map((p, idx) => ({ ...p, index_order: idx + 1 }));
        this.panels.set(ps);
        this.targetPanels.set(ps.length);
      },
    });
  }

  removePanel(i: number): void {
    if (this.panels().length <= 1) return;
    const panel = this.panels()[i];
    this.panelService.delete(panel.id).subscribe({
      next: () => {
        const ps = this.panels()
          .filter(p => p.id !== panel.id)
          .map((p, idx) => ({ ...p, index_order: idx + 1 }));
        this.panels.set(ps);
        this.targetPanels.set(ps.length);
      },
    });
  }

  openReview(panelIndex = 0): void {
    void this.router.navigate(['/projects', this.projectId(), 'review'], {
      queryParams: { panel: panelIndex },
    });
  }

  generateAllImages(): void {
    if (this.generatingImages() || this.generating()) return;
    const panels = this.panels();
    if (panels.length === 0) return;

    this.generatingImages.set(true);
    this.imagesDone.set(0);
    this.generatingPanelIds.set(new Set(panels.map(p => p.id)));

    from(panels).pipe(
      mergeMap(
        panel => this.panelService.generateImage(panel.id).pipe(
          map(updated => ({ id: panel.id, updated: updated as PanelOut | null })),
          catchError(() => of({ id: panel.id, updated: null as PanelOut | null })),
        ),
        this.IMAGE_CONCURRENCY,
      ),
      finalize(() => {
        this.generatingImages.set(false);
        this.generatingPanelIds.set(new Set());
      }),
    ).subscribe(({ id, updated }) => {
      this.imagesDone.update(n => n + 1);
      if (updated) {
        this.panels.update(list => list.map(p => p.id === updated.id ? updated : p));
      }
      this.generatingPanelIds.update(set => {
        const next = new Set(set);
        next.delete(id);
        return next;
      });
    });
  }

  saveSynopsis(text: string): void {
    const value = text.trim();
    if (!value) return;
    this.projectService.update(this.projectId(), { synopsis: value }).subscribe({
      next: () => {
        this.project.update(p => p ? { ...p, synopsis: value } : p);
        this.selectedTrecho.set(null);
      },
    });
  }

  regenSynopsis(): void {
    if (this.generatingSynopsis()) return;
    this.generatingSynopsis.set(true);
    this.projectService.generateSynopsis(this.projectId()).subscribe({
      next: p => {
        this.project.set(p);
        this.selectedTrecho.set(null);
        this.generatingSynopsis.set(false);
      },
      error: () => this.generatingSynopsis.set(false),
    });
  }

  onTrechoSelected(sel: SynopsisSelection | null): void {
    this.selectedTrecho.set(sel);
    this.trechoHighlight.set(sel ? { start: sel.start, end: sel.end } : null);
  }

  onCardHighlight(range: SynopsisRange | null): void {
    const sel = this.selectedTrecho();
    this.trechoHighlight.set(range ?? (sel ? { start: sel.start, end: sel.end } : null));
  }

  linkTrecho(panel: PanelOut): void {
    const sel = this.selectedTrecho();
    if (!sel) return;
    this.panelService.update(panel.id, { synopsis_start: sel.start, synopsis_end: sel.end }).subscribe({
      next: updated => {
        this.panels.update(list => list.map(p => p.id === updated.id ? updated : p));
        this.selectedTrecho.set(null);
        this.trechoHighlight.set(null);
      },
    });
  }

  back(): void {
    void this.router.navigate(['/projects/new/characters']);
  }
}
