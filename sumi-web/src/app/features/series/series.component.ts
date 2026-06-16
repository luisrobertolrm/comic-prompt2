import { Component, inject, OnInit, signal } from '@angular/core';
import type { ProjectOut, SeriesOut } from '../../core/models/home.models';
import { ProjectService } from '../../core/services/project.service';
import { SeriesService } from '../../core/services/series.service';

@Component({
  selector: 'app-series',
  standalone: true,
  templateUrl: './series.component.html',
  styleUrl: './series.component.scss',
})
export class SeriesComponent implements OnInit {
  private seriesService = inject(SeriesService);
  private projectService = inject(ProjectService);

  seriesList = signal<SeriesOut[]>([]);
  projects = signal<ProjectOut[]>([]);
  loading = signal(true);
  saving = signal(false);

  // null = nenhum formulário aberto; '' = criando nova; id = editando
  editingId = signal<string | null>(null);
  name = signal('');
  description = signal('');
  selectedProjectIds = signal<Set<string>>(new Set());

  ngOnInit(): void {
    this.projectService.list().subscribe({ next: ps => this.projects.set(ps) });
    this.reload();
  }

  private reload(): void {
    this.loading.set(true);
    this.seriesService.list().subscribe({
      next: s => { this.seriesList.set(s); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  projectTitle(id: string): string {
    return this.projects().find(p => p.id === id)?.title ?? '—';
  }

  startNew(): void {
    this.editingId.set('');
    this.name.set('');
    this.description.set('');
    this.selectedProjectIds.set(new Set());
  }

  edit(s: SeriesOut): void {
    this.editingId.set(s.id);
    this.name.set(s.name);
    this.description.set(s.description ?? '');
    this.selectedProjectIds.set(new Set(s.project_ids));
  }

  cancel(): void {
    this.editingId.set(null);
  }

  setName(e: Event): void { this.name.set((e.target as HTMLInputElement).value); }
  setDescription(e: Event): void { this.description.set((e.target as HTMLTextAreaElement).value); }

  isSelected(id: string): boolean { return this.selectedProjectIds().has(id); }

  toggleProject(id: string): void {
    this.selectedProjectIds.update(set => {
      const next = new Set(set);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }

  save(): void {
    if (!this.name().trim() || this.saving()) return;
    this.saving.set(true);
    const id = this.editingId();
    const payload = { name: this.name(), description: this.description() || null };
    const projectIds = [...this.selectedProjectIds()];

    if (id) {
      this.seriesService.update(id, payload).subscribe({
        next: () => this.seriesService.setProjects(id, projectIds).subscribe({
          next: () => this.afterSave(),
          error: () => this.saving.set(false),
        }),
        error: () => this.saving.set(false),
      });
    } else {
      this.seriesService.create(payload).subscribe({
        next: s => this.seriesService.setProjects(s.id, projectIds).subscribe({
          next: () => this.afterSave(),
          error: () => this.saving.set(false),
        }),
        error: () => this.saving.set(false),
      });
    }
  }

  private afterSave(): void {
    this.saving.set(false);
    this.editingId.set(null);
    this.reload();
  }

  remove(s: SeriesOut): void {
    if (!confirm(`Excluir a série "${s.name}"?`)) return;
    this.seriesService.remove(s.id).subscribe({ next: () => this.reload() });
  }
}
