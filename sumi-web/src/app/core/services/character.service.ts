import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { AttrGroup, CharacterCreate, CharacterOut, CharacterUpdate, PortraitJob } from '../models/home.models';

@Injectable({ providedIn: 'root' })
export class CharacterService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;
  private options$: Observable<AttrGroup[]> | null = null;

  listAll(): Observable<CharacterOut[]> {
    return this.http.get<CharacterOut[]>(`${this.base}/characters`);
  }

  options(): Observable<AttrGroup[]> {
    this.options$ ??= this.http
      .get<AttrGroup[]>(`${this.base}/character-options`)
      .pipe(shareReplay(1));
    return this.options$;
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

  generatePortrait(req: {
    style: string;
    colorMode: string;
    gender?: string;
    ageRange?: string;
    ethnicity?: string;
    hair?: string;
    extra?: string;
    prompt?: string;
    raw?: boolean;
  }): Observable<PortraitJob> {
    return this.http.post<PortraitJob>(`${this.base}/characters/generate-portrait`, {
      style: req.style,
      color_mode: req.colorMode,
      gender: req.gender,
      age_range: req.ageRange,
      ethnicity: req.ethnicity,
      hair: req.hair,
      extra: req.extra,
      prompt: req.prompt,
      raw: req.raw ?? false,
    });
  }

  pollPortraitJob(jobId: string): Observable<PortraitJob> {
    return this.http.get<PortraitJob>(`${this.base}/characters/portrait-job/${jobId}`);
  }
}
