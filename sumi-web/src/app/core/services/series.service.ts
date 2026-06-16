import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { SeriesCreate, SeriesOut, SeriesUpdate } from '../models/home.models';

@Injectable({ providedIn: 'root' })
export class SeriesService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  list(): Observable<SeriesOut[]> {
    return this.http.get<SeriesOut[]>(`${this.base}/series`);
  }

  get(id: string): Observable<SeriesOut> {
    return this.http.get<SeriesOut>(`${this.base}/series/${id}`);
  }

  create(req: SeriesCreate): Observable<SeriesOut> {
    return this.http.post<SeriesOut>(`${this.base}/series`, req);
  }

  update(id: string, req: SeriesUpdate): Observable<SeriesOut> {
    return this.http.patch<SeriesOut>(`${this.base}/series/${id}`, req);
  }

  remove(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/series/${id}`);
  }

  setProjects(seriesId: string, projectIds: string[]): Observable<void> {
    return this.http.put<void>(`${this.base}/series/${seriesId}/projects`, {
      project_ids: projectIds,
    });
  }
}
