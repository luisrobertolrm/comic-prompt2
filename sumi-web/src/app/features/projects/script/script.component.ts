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
import { TextReaderComponent } from '../../../shared/text-reader/text-reader.component';

@Component({
  selector: 'app-script',
  standalone: true,
  imports: [MangaPanelComponent, TextReaderComponent],
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
  editingSynopsis = signal(false);
  synopsisEdit = signal('');
  generatingSynopsis = signal(false);
  showSynopsisReader = signal(false);

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

  openReview(panelIndex = 0): void {
    void this.router.navigate(['/projects', this.projectId(), 'review'], {
      queryParams: { panel: panelIndex },
    });
  }

  statusColor(status: string): string {
    return status === 'approved' ? 'var(--mint)' : 'var(--peach-soft)';
  }

  statusLabel(status: string): string {
    return status === 'approved' ? 'OK' : 'REVISAR';
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

  startEditSynopsis(): void {
    const p = this.project();
    this.synopsisEdit.set(p?.synopsis ?? p?.premise ?? '');
    this.editingSynopsis.set(true);
  }

  saveSynopsis(): void {
    const text = this.synopsisEdit().trim();
    if (!text) { this.editingSynopsis.set(false); return; }
    this.projectService.update(this.projectId(), { synopsis: text }).subscribe({
      next: () => {
        this.project.update(p => p ? { ...p, synopsis: text } : p);
        this.editingSynopsis.set(false);
      },
    });
  }

  cancelEditSynopsis(): void {
    this.editingSynopsis.set(false);
  }

  regenSynopsis(): void {
    if (this.generatingSynopsis()) return;
    this.generatingSynopsis.set(true);
    this.projectService.generateSynopsis(this.projectId()).subscribe({
      next: p => {
        this.project.set(p);
        this.editingSynopsis.set(false);
        this.generatingSynopsis.set(false);
      },
      error: () => this.generatingSynopsis.set(false),
    });
  }

  back(): void {
    void this.router.navigate(['/projects/new/characters']);
  }
}
