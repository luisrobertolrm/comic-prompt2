import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { from, of } from 'rxjs';
import { catchError, finalize, map, mergeMap } from 'rxjs/operators';
import type { ProjectDetailOut } from '../../../core/models/home.models';
import type { PanelOut } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { ProjectService } from '../../../core/services/project.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { SettingsService } from '../../../core/services/settings.service';
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
  private settingsService = inject(SettingsService);

  styles = signal<StyleOption[]>([]);
  colorModes = signal<StyleOption[]>([]);

  useLocalAi = signal(false);
  localAiConfigured = signal(false);

  projectId = signal('');
  project = signal<ProjectDetailOut | null>(null);
  panels = signal<PanelOut[]>([]);
  generating = signal(false);
  generatingImages = signal(false);
  generatingPanelIds = signal<Set<string>>(new Set());
  generatingContentIds = signal<Set<string>>(new Set());
  imagesDone = signal(0);
  targetPanels = signal<number | null>(null);
  generateError = signal<string | null>(null);

  private readonly IMAGE_CONCURRENCY = 3;
  private readonly CONTENT_CONCURRENCY = 3;
  skeletons = [1, 2, 3, 4, 5, 6, 7];
  generatingSynopsis = signal(false);
  synopsisError = signal<string | null>(null);
  selectedTrecho = signal<SynopsisSelection | null>(null);
  trechoHighlight = signal<SynopsisRange | null>(null);

  selectMode = signal(false);
  selectedIds = signal<Set<string>>(new Set());
  deleting = signal(false);

  synopsisTemperature = signal(0.8);
  panelsTemperature = signal(0.4);

  synopsisText(): string {
    const p = this.project();
    return p ? (p.synopsis || p.premise || p.title || '') : '';
  }

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.projectId.set(id);
    this.projectService.get(id).subscribe({ next: p => {
      this.project.set(p);
      this.draft.currentProjectTitle.set(p.title);
      this.synopsisTemperature.set(p.synopsis_temperature);
      this.panelsTemperature.set(p.panels_temperature);
      // Sugere ~3 quadros por página (limites do campo) e informa ao modelo.
      this.targetPanels.set(Math.min(30, Math.max(5, p.pages * 3)));
    } });
    this.styleService.catalog().subscribe({
      next: c => { this.styles.set(c.styles); this.colorModes.set(c.color_modes); },
    });
    this.settingsService.get().subscribe({
      next: s => {
        this.localAiConfigured.set(!!s.local_ai_url && !!s.local_ai_model);
        this.useLocalAi.set(s.local_ai_enabled && this.localAiConfigured());
      },
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
    if (this.generating()) return;
    this.generating.set(true);
    this.generateError.set(null);
    this.panels.set([]);
    // Passo 1: a IA divide o roteiro inteiro em quadros 'pending' (retorno rápido).
    this.panelService.generate(this.projectId(), this.targetPanels(), this.useLocalAi()).subscribe({
      next: slots => {
        this.panels.set(slots);
        this.targetPanels.set(slots.length);
        this.generating.set(false);
        this.fillPanelsContent(slots);
      },
      error: err => {
        this.generating.set(false);
        this.generateError.set(this.errorMessage(err));
      },
    });
  }

  private errorMessage(err: unknown): string {
    const detail = (err as { error?: { detail?: string } })?.error?.detail;
    return detail || 'Não foi possível gerar os quadros agora. Tente novamente.';
  }

  /** Passo 2: gera o conteúdo de cada quadro individualmente, em paralelo. */
  private fillPanelsContent(slots: PanelOut[]): void {
    if (slots.length === 0) return;
    this.generatingContentIds.set(new Set(slots.map(p => p.id)));
    from(slots).pipe(
      mergeMap(
        panel => this.panelService.generateContent(panel.id, this.useLocalAi()).pipe(
          map(updated => ({ id: panel.id, updated: updated as PanelOut | null })),
          catchError(() => of({ id: panel.id, updated: null as PanelOut | null })),
        ),
        this.CONTENT_CONCURRENCY,
      ),
    ).subscribe(({ id, updated }) => {
      if (updated) {
        this.panels.update(list => list.map(p => p.id === updated.id ? updated : p));
      }
      this.generatingContentIds.update(s => { const n = new Set(s); n.delete(id); return n; });
    });
  }

  generateContent(panel: PanelOut): void {
    if (this.generatingContentIds().has(panel.id)) return;
    this.generatingContentIds.update(s => new Set(s).add(panel.id));
    this.panelService.generateContent(panel.id, this.useLocalAi()).subscribe({
      next: updated => {
        this.panels.update(list => list.map(p => p.id === updated.id ? updated : p));
        this.generatingContentIds.update(s => { const n = new Set(s); n.delete(panel.id); return n; });
      },
      error: err => {
        this.generateError.set(this.errorMessage(err));
        this.generatingContentIds.update(s => { const n = new Set(s); n.delete(panel.id); return n; });
      },
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

  toggleSelectMode(): void {
    this.selectMode.update(v => !v);
    if (!this.selectMode()) this.selectedIds.set(new Set());
  }

  togglePanelSelect(id: string): void {
    this.selectedIds.update(set => {
      const next = new Set(set);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  selectAll(): void {
    this.selectedIds.set(new Set(this.panels().map(p => p.id)));
  }

  clearSelection(): void {
    this.selectedIds.set(new Set());
  }

  deleteSelected(): void {
    this.removePanels([...this.selectedIds()]);
  }

  deleteAll(): void {
    this.removePanels(this.panels().map(p => p.id));
  }

  private removePanels(ids: string[]): void {
    if (this.deleting() || ids.length === 0) return;
    this.deleting.set(true);
    this.panelService.deleteMany(this.projectId(), ids).subscribe({
      next: () => {
        const idSet = new Set(ids);
        const ps = this.panels()
          .filter(p => !idSet.has(p.id))
          .map((p, idx) => ({ ...p, index_order: idx + 1 }));
        this.panels.set(ps);
        this.targetPanels.set(ps.length || null);
        this.selectedIds.set(new Set());
        this.selectMode.set(false);
        this.deleting.set(false);
      },
      error: () => this.deleting.set(false),
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

  /** Converte o texto do input em temperatura válida (0–2) ou null se não for número. */
  private parseTemperature(value: string): number | null {
    if (value.trim() === '') return null;
    const n = Number(value);
    if (!Number.isFinite(n)) return null;
    return Math.min(2, Math.max(0, n));
  }

  setSynopsisTemperature(value: string): void {
    const t = this.parseTemperature(value);
    if (t === null) return;
    this.synopsisTemperature.set(t);
    this.project.update(p => p ? { ...p, synopsis_temperature: t } : p);
    this.projectService.update(this.projectId(), { synopsis_temperature: t }).subscribe();
  }

  setPanelsTemperature(value: string): void {
    const t = this.parseTemperature(value);
    if (t === null) return;
    this.panelsTemperature.set(t);
    this.project.update(p => p ? { ...p, panels_temperature: t } : p);
    this.projectService.update(this.projectId(), { panels_temperature: t }).subscribe();
  }

  regenSynopsis(): void {
    if (this.generatingSynopsis()) return;
    this.generatingSynopsis.set(true);
    this.synopsisError.set(null);
    this.projectService.generateSynopsis(this.projectId()).subscribe({
      next: p => {
        this.project.set(p);
        this.selectedTrecho.set(null);
        this.generatingSynopsis.set(false);
      },
      error: err => {
        this.generatingSynopsis.set(false);
        this.synopsisError.set(this.synopsisErrorMessage(err));
      },
    });
  }

  private synopsisErrorMessage(err: unknown): string {
    const detail = (err as { error?: { detail?: string } })?.error?.detail;
    return detail || 'Não foi possível gerar a sinopse. Tente novamente.';
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
