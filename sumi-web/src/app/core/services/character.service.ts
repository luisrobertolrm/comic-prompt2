import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { CharacterCreate, CharacterOut, CharacterUpdate, PortraitJob } from '../models/home.models';

@Injectable({ providedIn: 'root' })
export class CharacterService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  listAll(): Observable<CharacterOut[]> {
    return this.http.get<CharacterOut[]>(`${this.base}/characters`);
  }

  create(req: CharacterCreate): Observable<CharacterOut> {
    return this.http.post<CharacterOut>(`${this.base}/characters`, req);
  }

  update(id: string, req: CharacterUpdate): Observable<CharacterOut> {
    return this.http.patch<CharacterOut>(`${this.base}/characters/${id}`, req);
  }

  deleteUnused(ids: string[]): Observable<{ deleted: number }> {
    return this.http.post<{ deleted: number }>(`${this.base}/characters/delete-unused`, { ids });
  }

  generatePortrait(prompt: string, style: string, gender?: string): Observable<PortraitJob> {
    return this.http.post<PortraitJob>(`${this.base}/characters/generate-portrait`, { prompt, style, gender });
  }

  pollPortraitJob(jobId: string): Observable<PortraitJob> {
    return this.http.get<PortraitJob>(`${this.base}/characters/portrait-job/${jobId}`);
  }
}
