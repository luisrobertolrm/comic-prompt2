import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import type { ProjectDetailOut } from '../../../core/models/home.models';
import type { PanelOut } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';
import { StyleService, type StyleOption } from '../../../core/services/style.service';
import { MangaPanelComponent } from '../manga-panel/manga-panel.component';

@Component({
  selector: 'app-final',
  standalone: true,
  imports: [MangaPanelComponent],
  templateUrl: './final.component.html',
  styleUrl: './final.component.scss',
})
export class FinalComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private draft = inject(ProjectDraftService);
  private projectService = inject(ProjectService);
  private panelService = inject(PanelService);
  private styleService = inject(StyleService);

  projectId = signal('');
  project = signal<ProjectDetailOut | null>(null);
  panels = signal<PanelOut[]>([]);
  styleOptions = signal<StyleOption[]>([]);
  loading = signal(true);

  pages = computed<PanelOut[][]>(() => {
    const ps = this.panels();
    const result: PanelOut[][] = [];
    for (let i = 0; i < ps.length; i += 4) result.push(ps.slice(i, i + 4));
    return result;
  });

  approvedCount = computed(() => this.panels().filter(p => p.status === 'approved').length);
  styleLabel = computed(() =>
    this.styleOptions().find(s => s.id === this.project()?.style)?.label ?? '—');
  isPublic = computed(() => this.project()?.status === 'Público');
  togglingPublic = signal(false);

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.projectId.set(id);
    this.styleService.catalog().subscribe({ next: c => this.styleOptions.set(c.styles) });
    this.projectService.get(id).subscribe({ next: p => { this.project.set(p); this.draft.currentProjectTitle.set(p.title); } });
    this.panelService.list(id).subscribe({
      next: ps => { this.panels.set(ps); this.loading.set(false); },
    });
  }

  padNum(n: number): string { return String(n).padStart(2, '0'); }

  togglePublic(): void {
    const proj = this.project();
    if (!proj || this.togglingPublic()) return;
    const status = this.isPublic() ? 'Rascunho' : 'Público';
    this.togglingPublic.set(true);
    this.projectService.update(this.projectId(), { status }).subscribe({
      next: res => {
        this.project.update(p => p ? { ...p, status: res.status } : p);
        this.togglingPublic.set(false);
      },
      error: () => this.togglingPublic.set(false),
    });
  }

  goEditor(): void { void this.router.navigate(['/projects', this.projectId(), 'editor']); }
  goHome(): void { void this.router.navigate(['/home']); }
  goVideo(): void { void this.router.navigate(['/projects', this.projectId(), 'video']); }
}
