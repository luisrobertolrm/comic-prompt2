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

  generatePortrait(
    prompt: string,
    style: string,
    colorMode: string,
    gender?: string,
    bodyType?: string,
    skinTone?: string,
    ethnicity?: string,
  ): Observable<PortraitJob> {
    return this.http.post<PortraitJob>(`${this.base}/characters/generate-portrait`, {
      prompt,
      style,
      color_mode: colorMode,
      gender,
      body_type: bodyType,
      skin_tone: skinTone,
      ethnicity,
    });
  }

  pollPortraitJob(jobId: string): Observable<PortraitJob> {
    return this.http.get<PortraitJob>(`${this.base}/characters/portrait-job/${jobId}`);
  }
}
