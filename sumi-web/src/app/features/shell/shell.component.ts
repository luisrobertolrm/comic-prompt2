import { Component, computed, effect, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink, RouterOutlet } from '@angular/router';
import { filter, map, startWith } from 'rxjs';
import { AuthService } from '../../core/services/auth.service';
import { ProjectDraftService } from '../../core/services/project-draft.service';
import { ProjectService } from '../../core/services/project.service';

const ICON_PATHS: Record<string, string> = {
  home:     'M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1z',
  book:     'M4 4h7a3 3 0 0 1 3 3v13M20 4h-3a3 3 0 0 0-3 3v13M4 4v15h7M20 4v15h-6',
  spark:    'M12 3l1.8 4.7L18 9l-4.2 1.8L12 15l-1.8-4.2L6 9l4.2-1.3L12 3z',
  users:    'M16 11a4 4 0 1 0-8 0 4 4 0 0 0 8 0zM3 21v-1a6 6 0 0 1 6-6h6a6 6 0 0 1 6 6v1',
  scroll:   'M4 4h12a3 3 0 0 1 3 3v10a3 3 0 0 0 3 3H8a3 3 0 0 1-3-3V4z',
  eye:      'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  layout:   'M3 4h18v6H3zM3 12h8v8H3zM13 12h8v8h-8z',
  download: 'M12 4v12m0 0l-4-4m4 4l4-4M5 20h14',
  film:     'M4 4h16v16H4zM4 9h16M4 15h16M9 4v16M15 4v16',
  image:    'M3 5h18v14H3zM3 16l5-5 4 4 3-3 5 5M9 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z',
  star:     'M12 3l2.6 6.3 6.4.5-5 4.3 1.6 6.5L12 17l-5.6 3.6L8 14.1l-5-4.3 6.4-.5L12 3z',
  search:   'M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zM21 21l-4.3-4.3',
  mic:      'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3',
  logout:   'M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9',
  gear:     'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z',
};

const STEPS = [
  { id: 'new',        label: 'Ideia',       icon: 'spark'    },
  { id: 'characters', label: 'Personagens', icon: 'users'    },
  { id: 'scenarios',  label: 'Cenários',    icon: 'image'    },
  { id: 'script',     label: 'Roteiro',     icon: 'scroll'   },
  { id: 'review',     label: 'Revisão',     icon: 'eye'      },
  { id: 'editor',     label: 'Editor',      icon: 'layout'   },
  { id: 'final',      label: 'Finalizar',   icon: 'download' },
  { id: 'video',      label: 'Vídeo',       icon: 'film'     },
];

const STEP_IDS = STEPS.map(s => s.id);

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
})
export class ShellComponent {
  private router          = inject(Router);
  private projectService  = inject(ProjectService);
  auth                    = inject(AuthService);
  draft                   = inject(ProjectDraftService);

  readonly steps = STEPS;
  popoverOpen    = signal(false);
  sidebarOpen    = signal(false);
  deleteOpen     = signal(false);
  deleteCode     = signal('');
  deleteInput    = signal('');
  deleting       = signal(false);
  private lastFetchedId = '';

  // URL reativa — atualiza em cada navegação
  url = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      map(e => e.urlAfterRedirects),
      startWith(this.router.url),
    ),
    { initialValue: this.router.url },
  );

  // Seção ativa derivada da URL
  section = computed(() => {
    const u = this.url();
    if (u === '/home' || u === '/') return 'home';
    if (u.startsWith('/library'))           return 'library';
    if (u.startsWith('/series'))            return 'series';
    if (u.startsWith('/voice-test'))        return 'voice-test';
    if (u.startsWith('/settings'))          return 'settings';
    if (u.endsWith('/new'))                 return 'new';
    if (u.endsWith('/characters'))          return 'characters';
    if (u.endsWith('/scenarios'))           return 'scenarios';
    const m = u.match(/\/projects\/[^/]+\/(.+)/);
    return m?.[1] ?? '';
  });

  inCreation = computed(() => this.url().startsWith('/projects'));

  projectId = computed(() => {
    const m = this.url().match(/\/projects\/([^/]+)(?:\/|$)/);
    const id = m?.[1] ?? '';
    return id === 'new' ? '' : id;
  });

  constructor() {
    // Busca o título do projeto sempre que o projectId mudar na URL
    effect(() => {
      const pid = this.projectId();
      if (pid && pid !== this.lastFetchedId) {
        this.lastFetchedId = pid;
        this.projectService.get(pid).subscribe({
          next: p => this.draft.currentProjectTitle.set(p.title),
          error: () => {},
        });
      }
      if (!pid) {
        this.lastFetchedId = '';
        // Não limpa o título — mantém visível enquanto navega entre steps
      }
    });
  }

  currentStepIdx = computed(() => STEP_IDS.indexOf(this.section()));

  breadcrumbs = computed(() => {
    const s = this.section();
    const stepLabels: Record<string, string> = {
      new: 'Ideia', characters: 'Personagens', scenarios: 'Cenários', script: 'Roteiro',
      review: 'Revisão', editor: 'Editor', final: 'Finalizar', video: 'Vídeo',
    };
    if (s === 'home')    return [{ label: 'Projetos',   route: '' }];
    if (s === 'library') return [{ label: 'Biblioteca', route: '' }];
    if (s === 'series')  return [{ label: 'Séries',     route: '' }];
    const title = this.draft.currentProjectTitle() || 'Projeto';
    return [
      { label: 'Projetos', route: '/home' },
      { label: title,      route: ''      },
      { label: stepLabels[s] ?? s, route: '' },
    ];
  });

  iconPath(name: string): string { return ICON_PATHS[name] ?? ''; }

  isActive(sectionId: string): boolean { return this.section() === sectionId; }

  isDone(stepIdx: number): boolean {
    return this.inCreation() && stepIdx < this.currentStepIdx();
  }

  user = computed(() => this.auth.currentUser());

  initial = computed(() => {
    const name = this.user()?.name ?? 'U';
    return name.charAt(0).toUpperCase();
  });

  toggleSidebar(): void { this.sidebarOpen.update(v => !v); }
  closeSidebar(): void  { this.sidebarOpen.set(false); }

  navigateTo(path: string): void { this.closeSidebar(); void this.router.navigate([path]); }

  navigateToStep(stepId: string): void {
    const pid = this.projectId();

    if (stepId === 'new') {
      if (pid) this.draft.projectId.set(pid);
      void this.router.navigate(['/projects/new']);
      this.closeSidebar();
      return;
    }

    if (stepId === 'characters') {
      if (pid) this.draft.projectId.set(pid);
      void this.router.navigate(['/projects/new/characters']);
      this.closeSidebar();
      return;
    }

    if (stepId === 'scenarios') {
      if (pid) this.draft.projectId.set(pid);
      void this.router.navigate(['/projects/new/scenarios']);
      this.closeSidebar();
      return;
    }

    const targetId = pid || this.draft.projectId();
    if (targetId) void this.router.navigate(['/projects', targetId, stepId]);
    this.closeSidebar();
  }

  logout(): void {
    this.popoverOpen.set(false);
    this.auth.logout();
  }

  togglePopover(): void { this.popoverOpen.update(v => !v); }

  closePopover(): void { this.popoverOpen.set(false); }

  canDeleteProject = computed(() => !!this.projectId());

  canConfirmDelete = computed(
    () => this.deleteInput().trim().toUpperCase() === this.deleteCode() && !this.deleting(),
  );

  openDelete(): void {
    if (!this.projectId()) return;
    const code = Array.from({ length: 6 }, () =>
      'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'[Math.floor(Math.random() * 32)],
    ).join('');
    this.deleteCode.set(code);
    this.deleteInput.set('');
    this.deleting.set(false);
    this.deleteOpen.set(true);
  }

  closeDelete(): void {
    if (this.deleting()) return;
    this.deleteOpen.set(false);
  }

  onDeleteInput(value: string): void { this.deleteInput.set(value); }

  confirmDelete(): void {
    const id = this.projectId();
    if (!id || !this.canConfirmDelete()) return;
    this.deleting.set(true);
    this.projectService.delete(id).subscribe({
      next: () => {
        this.deleteOpen.set(false);
        this.deleting.set(false);
        if (this.draft.projectId() === id) this.draft.projectId.set(null);
        this.draft.currentProjectTitle.set('');
        this.closeSidebar();
        void this.router.navigate(['/home']);
      },
      error: () => { this.deleting.set(false); },
    });
  }
}
