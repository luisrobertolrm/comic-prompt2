import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'auth',
    loadComponent: () =>
      import('./features/auth/auth-screen/auth-screen.component').then(m => m.AuthScreenComponent),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/shell/shell.component').then(m => m.ShellComponent),
    children: [
      { path: '', redirectTo: 'home', pathMatch: 'full' },
      {
        path: 'home',
        loadComponent: () =>
          import('./features/home/home.component').then(m => m.HomeComponent),
      },
      {
        path: 'library',
        loadComponent: () =>
          import('./features/library/library.component').then(m => m.LibraryComponent),
      },
      {
        path: 'voice-test',
        loadComponent: () =>
          import('./features/voice-test/voice-test.component').then(m => m.VoiceTestComponent),
      },
      {
        path: 'projects/new',
        loadComponent: () =>
          import('./features/projects/new/new-project.component').then(m => m.NewProjectComponent),
      },
      {
        path: 'projects/new/characters',
        loadComponent: () =>
          import('./features/projects/characters/characters-screen.component').then(m => m.CharactersScreenComponent),
      },
      {
        path: 'projects/:id/script',
        loadComponent: () =>
          import('./features/projects/script/script.component').then(m => m.ScriptComponent),
      },
      {
        path: 'projects/:id/review',
        loadComponent: () =>
          import('./features/projects/review/review.component').then(m => m.ReviewComponent),
      },
      {
        path: 'projects/:id/editor',
        loadComponent: () =>
          import('./features/projects/editor/editor.component').then(m => m.EditorComponent),
      },
      {
        path: 'projects/:id/final',
        loadComponent: () =>
          import('./features/projects/final/final.component').then(m => m.FinalComponent),
      },
      {
        path: 'projects/:id/video',
        loadComponent: () =>
          import('./features/projects/video/video.component').then(m => m.VideoComponent),
      },
    ],
  },
];
