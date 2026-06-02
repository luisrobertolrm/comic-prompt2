import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import type { ProjectDetailOut } from '../../../core/models/home.models';
import type { PanelOut } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { ProjectService } from '../../../core/services/project.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { MangaPanelComponent } from '../manga-panel/manga-panel.component';

@Component({
  selector: 'app-script',
  standalone: true,
  imports: [MangaPanelComponent],
  templateUrl: './script.component.html',
  styleUrl: './script.component.scss',
})
export class ScriptComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private projectService = inject(ProjectService);
  private panelService = inject(PanelService);
  private draft = inject(ProjectDraftService);

  projectId = signal('');
  project = signal<ProjectDetailOut | null>(null);
  panels = signal<PanelOut[]>([]);
  generating = signal(false);
  generatingImages = signal(false);
  skeletons = [1, 2, 3, 4, 5, 6, 7];
  editingSynopsis = signal(false);
  synopsisEdit = signal('');

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.projectId.set(id);
    this.projectService.get(id).subscribe({ next: p => { this.project.set(p); this.draft.currentProjectTitle.set(p.title); } });
    this.loadPanels(id);
  }

  private loadPanels(id: string): void {
    this.panelService.list(id).subscribe({
      next: panels => {
        if (panels.length === 0) this.runGenerate();
        else this.panels.set(panels);
      },
    });
  }

  runGenerate(): void {
    this.generating.set(true);
    this.panels.set([]);
    this.panelService.generate(this.projectId()).subscribe({
      next: panels => { this.panels.set(panels); this.generating.set(false); },
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
    this.generatingImages.set(true);
    this.panelService.generateAllImages(this.projectId()).subscribe({
      next: panels => { this.panels.set(panels); this.generatingImages.set(false); },
      error: () => this.generatingImages.set(false),
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

  back(): void {
    void this.router.navigate(['/projects/new/characters']);
  }
}
