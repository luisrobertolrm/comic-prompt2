import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { ProjectCreate, ProjectDetailOut, ProjectOut, ProjectUpdate } from '../models/home.models';

export interface YtMeta {
  yt_title: string;
  yt_description: string;
  yt_tags: string[];
  yt_category_id: string;
  privacy_status: 'public' | 'unlisted' | 'private';
  publish_at: string | null;
  thumbnail_panel_id: string | null;
}

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

  update(id: string, req: ProjectUpdate): Observable<ProjectOut> {
    return this.http.patch<ProjectOut>(`${this.base}/projects/${id}`, req);
  }

  setCharacters(projectId: string, characterIds: string[]): Observable<void> {
    return this.http.put<void>(`${this.base}/projects/${projectId}/characters`, {
      character_ids: characterIds,
    });
  }

  getYtMeta(projectId: string): Observable<YtMeta> {
    return this.http.get<YtMeta>(`${this.base}/projects/${projectId}/youtube-metadata`);
  }

  saveYtMeta(projectId: string, meta: YtMeta): Observable<YtMeta> {
    return this.http.put<YtMeta>(`${this.base}/projects/${projectId}/youtube-metadata`, meta);
  }

  generateYtMeta(projectId: string): Observable<YtMeta> {
    return this.http.post<YtMeta>(`${this.base}/projects/${projectId}/youtube-metadata/generate`, {});
  }
}
