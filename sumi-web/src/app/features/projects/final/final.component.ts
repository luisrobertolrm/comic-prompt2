import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import type { ProjectDetailOut } from '../../../core/models/home.models';
import type { PanelOut } from '../../../core/models/panel.models';
import { PanelService } from '../../../core/services/panel.service';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';
import { MangaPanelComponent } from '../manga-panel/manga-panel.component';

const STYLES: Record<string, string> = {
  'classic-shoujo': 'Shojo clássico',
  'modern-line': 'Linha moderna limpa',
  'ink-heavy': 'Tinta marcada',
};

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

  projectId = signal('');
  project = signal<ProjectDetailOut | null>(null);
  panels = signal<PanelOut[]>([]);
  loading = signal(true);

  pages = computed<PanelOut[][]>(() => {
    const ps = this.panels();
    const result: PanelOut[][] = [];
    for (let i = 0; i < ps.length; i += 4) result.push(ps.slice(i, i + 4));
    return result;
  });

  approvedCount = computed(() => this.panels().filter(p => p.status === 'approved').length);
  styleLabel = computed(() => STYLES[this.project()?.style ?? ''] ?? '—');

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id') ?? '';
    this.projectId.set(id);
    this.projectService.get(id).subscribe({ next: p => { this.project.set(p); this.draft.currentProjectTitle.set(p.title); } });
    this.panelService.list(id).subscribe({
      next: ps => { this.panels.set(ps); this.loading.set(false); },
    });
  }

  padNum(n: number): string { return String(n).padStart(2, '0'); }

  goEditor(): void { void this.router.navigate(['/projects', this.projectId(), 'editor']); }
  goHome(): void { void this.router.navigate(['/home']); }
  goVideo(): void { void this.router.navigate(['/projects', this.projectId(), 'video']); }
}
