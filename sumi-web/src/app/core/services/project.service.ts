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

export interface VideoJob {
  job_id: string;
  status: 'pending' | 'running' | 'done' | 'error';
  progress: number;
  video_url: string | null;
  detail: string;
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

  generateSynopsis(id: string): Observable<ProjectDetailOut> {
    return this.http.post<ProjectDetailOut>(`${this.base}/projects/${id}/synopsis/generate`, {});
  }

  setCharacters(projectId: string, characterIds: string[]): Observable<void> {
    return this.http.put<void>(`${this.base}/projects/${projectId}/characters`, {
      character_ids: characterIds,
    });
  }

  setScenarios(projectId: string, scenarioIds: string[]): Observable<void> {
    return this.http.put<void>(`${this.base}/projects/${projectId}/scenarios`, {
      scenario_ids: scenarioIds,
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

  startVideoExport(projectId: string): Observable<VideoJob> {
    return this.http.post<VideoJob>(`${this.base}/projects/${projectId}/export/video`, {});
  }

  pollVideoJob(projectId: string, jobId: string): Observable<VideoJob> {
    return this.http.get<VideoJob>(`${this.base}/projects/${projectId}/export/video/${jobId}`);
  }

  exportBackup(projectId: string): Observable<Blob> {
    return this.http.get(`${this.base}/projects/${projectId}/backup`, { responseType: 'blob' });
  }

  importBackup(file: File, projectId?: string): Observable<ProjectOut> {
    const fd = new FormData();
    fd.append('file', file);
    if (projectId) {
      fd.append('project_id', projectId);
    }
    return this.http.post<ProjectOut>(`${this.base}/projects/import`, fd);
  }
}
