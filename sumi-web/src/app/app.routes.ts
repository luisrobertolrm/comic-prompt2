import { Routes } from '@angular/router';
import { adminGuard } from './core/guards/admin.guard';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: 'auth',
    loadComponent: () =>
      import('./features/auth/auth-screen/auth-screen.component').then(m => m.AuthScreenComponent),
  },
  // Galeria pública — tela padrão, sem shell/menu lateral
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () =>
      import('./features/gallery/gallery.component').then(m => m.GalleryComponent),
  },
  {
    path: 'p/:id',
    loadComponent: () =>
      import('./features/gallery/gallery-reader.component').then(m => m.GalleryReaderComponent),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/shell/shell.component').then(m => m.ShellComponent),
    children: [
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
        path: 'series',
        loadComponent: () =>
          import('./features/series/series.component').then(m => m.SeriesComponent),
      },
      {
        path: 'voice-test',
        loadComponent: () =>
          import('./features/voice-test/voice-test.component').then(m => m.VoiceTestComponent),
      },
      {
        path: 'image-test',
        loadComponent: () =>
          import('./features/image-test/image-test.component').then(m => m.ImageTestComponent),
      },
      {
        path: 'settings',
        loadComponent: () =>
          import('./features/settings/settings.component').then(m => m.SettingsComponent),
      },
      {
        path: 'admin',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/admin/admin.component').then(m => m.AdminComponent),
      },
      {
        path: 'app-settings',
        canActivate: [adminGuard],
        loadComponent: () =>
          import('./features/app-settings/app-settings.component').then(m => m.AppSettingsComponent),
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
        path: 'projects/new/scenarios',
        loadComponent: () =>
          import('./features/projects/scenarios/scenarios-screen.component').then(m => m.ScenariosScreenComponent),
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
