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
  importing = signal(false);
  view = signal<View>('grid');
  filter = signal('Todos');

  importFile = signal<File | null>(null);
  importProjectId = signal('');
  importError = signal('');

  exportingId = signal<string | null>(null);
  exportTitle = signal('');
  exportError = signal('');

  importToast = signal<{ kind: 'info' | 'success' | 'error'; msg: string } | null>(null);

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

  exportProject(p: ProjectOut, ev: Event): void {
    ev.stopPropagation();
    if (this.exportingId()) return;
    this.exportError.set('');
    this.exportTitle.set(p.title);
    this.exportingId.set(p.id);
    this.projectService.exportBackup(p.id).subscribe({
      next: (blob) => {
        this.exportingId.set(null);
        this.downloadBlob(blob, `sumi-backup-${p.title}.zip`);
      },
      error: async (err) => {
        this.exportingId.set(null);
        this.exportError.set(await this.extractError(err));
      },
    });
  }

  private async extractError(err: unknown): Promise<string> {
    const e = err as { error?: unknown };
    try {
      if (e?.error instanceof Blob) {
        const parsed = JSON.parse(await e.error.text());
        if (parsed?.detail) return parsed.detail;
      }
    } catch { /* corpo não-JSON */ }
    return 'Falha ao gerar o backup. Tente novamente.';
  }

  onImportFile(ev: Event): void {
    const input = ev.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (!file) return;
    this.importFile.set(file);
    this.importProjectId.set(this.newGuid());
    this.importError.set('');
  }

  regenProjectId(): void {
    this.importProjectId.set(this.newGuid());
  }

  cancelImport(): void {
    this.importFile.set(null);
    this.importError.set('');
  }

  confirmImport(): void {
    const file = this.importFile();
    if (!file) return;
    const pid = this.importProjectId().trim();
    if (!this.isGuid(pid)) {
      this.importError.set('ID inválido. Use um GUID ou gere outro.');
      return;
    }
    this.importing.set(true);
    this.importError.set('');
    this.importToast.set({ kind: 'info', msg: 'Importação iniciada… isso pode demorar.' });
    this.projectService.importBackup(file, pid).subscribe({
      next: (proj) => {
        this.importing.set(false);
        this.importFile.set(null);
        this.projects.update((list) => [proj, ...list]);
        this.importToast.set({ kind: 'success', msg: `Projeto “${proj.title}” importado com sucesso.` });
        setTimeout(() => {
          if (this.importToast()?.kind === 'success') this.importToast.set(null);
        }, 5000);
      },
      error: (err) => {
        this.importing.set(false);
        const detail = err?.error?.detail ?? 'Falha ao importar. Verifique se o arquivo é um .zip válido do Sumi.';
        this.importToast.set({ kind: 'error', msg: detail });
      },
    });
  }

  private newGuid(): string {
    return crypto.randomUUID();
  }

  private isGuid(v: string): boolean {
    return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
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
