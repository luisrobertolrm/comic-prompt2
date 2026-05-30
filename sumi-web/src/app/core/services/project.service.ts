import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { ProjectCreate, ProjectDetailOut, ProjectOut } from '../models/home.models';

@Injectable({ providedIn: 'root' })
export class ProjectService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  list(): Observable<ProjectOut[]> {
    return this.http.get<ProjectOut[]>(`${this.base}/projects`);
  }

  get(id: string): Observable<ProjectDetailOut> {
    return this.http.get<ProjectDetailOut>(`${this.base}/projects/${id}`);
  }

  create(req: ProjectCreate): Observable<ProjectOut> {
    return this.http.post<ProjectOut>(`${this.base}/projects`, req);
  }

  setCharacters(projectId: string, characterIds: string[]): Observable<void> {
    return this.http.put<void>(`${this.base}/projects/${projectId}/characters`, {
      character_ids: characterIds,
    });
  }
}
