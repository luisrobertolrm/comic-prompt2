import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { CharacterService } from '../../core/services/character.service';
import { ProjectDraftService } from '../../core/services/project-draft.service';
import { ProjectService } from '../../core/services/project.service';
import type { CharacterOut, ProjectOut } from '../../core/models/home.models';

type View = 'grid' | 'list';

const STATUSES = ['Todos', 'Rascunho', 'Roteiro', 'Em revisão', 'Concluído'] as const;

@Component({
  selector: 'app-home',
  standalone: true,
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent implements OnInit {
  private projectService = inject(ProjectService);
  private characterService = inject(CharacterService);
  private draft = inject(ProjectDraftService);
  private router = inject(Router);

  projects = signal<ProjectOut[]>([]);
  characters = signal<CharacterOut[]>([]);
  loading = signal(true);
  view = signal<View>('grid');
  filter = signal('Todos');

  readonly statuses = STATUSES;

  filteredProjects = computed(() => {
    const f = this.filter();
    return f === 'Todos' ? this.projects() : this.projects().filter(p => p.status === f);
  });

  ngOnInit(): void {
    this.projectService.list().subscribe({
      next: (data) => {
        this.projects.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });

    this.characterService.listAll().subscribe({
      next: (data) => this.characters.set(data.slice(0, 8)),
    });
  }

  goNewProject(): void {
    this.draft.projectId.set(null);
    this.draft.currentProjectTitle.set('');
    void this.router.navigate(['/projects', 'new']);
  }
  goLibrary(): void { void this.router.navigate(['/library']); }

  openProject(p: ProjectOut): void {
    // Script verifica se há quadros e gera automaticamente se não houver
    void this.router.navigate(['/projects', p.id, 'script']);
  }

  coverPattern(tone: string): string {
    if (tone === 'diag') {
      return 'repeating-linear-gradient(45deg,rgba(30,24,18,.18) 0 1px,transparent 1px 6px)';
    }
    if (tone === 'dense') {
      return 'radial-gradient(circle,rgba(30,24,18,.22) .7px,transparent 1px)';
    }
    return 'radial-gradient(circle,rgba(30,24,18,.18) .6px,transparent 1px)';
  }

  coverBgSize(tone: string): string {
    return tone === 'dense' ? '5px 5px' : '7px 7px';
  }

  formatDate(iso: string): string {
    const d = new Date(iso);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  initial(name: string): string {
    return name.charAt(0).toUpperCase();
  }
}
