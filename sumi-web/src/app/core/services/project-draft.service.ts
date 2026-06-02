import { Injectable, effect, signal } from '@angular/core';

const KEY = 'sumi.draftProjectId';

@Injectable({ providedIn: 'root' })
export class ProjectDraftService {
  projectId          = signal<string | null>(sessionStorage.getItem(KEY));
  currentProjectTitle = signal<string>('');

  constructor() {
    effect(() => {
      const id = this.projectId();
      if (id) sessionStorage.setItem(KEY, id);
      else sessionStorage.removeItem(KEY);
    });
  }
}
