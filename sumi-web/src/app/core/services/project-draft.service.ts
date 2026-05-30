import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ProjectDraftService {
  projectId          = signal<string | null>(null);
  currentProjectTitle = signal<string>('');
}
