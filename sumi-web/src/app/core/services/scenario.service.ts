import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { AttrGroup, ScenarioCreate, ScenarioOut, ScenarioUpdate, SceneJob } from '../models/home.models';

@Injectable({ providedIn: 'root' })
export class ScenarioService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;
  private options$: Observable<AttrGroup[]> | null = null;

  listAll(): Observable<ScenarioOut[]> {
    return this.http.get<ScenarioOut[]>(`${this.base}/scenarios`);
  }

  options(): Observable<AttrGroup[]> {
    this.options$ ??= this.http
      .get<AttrGroup[]>(`${this.base}/scenario-options`)
      .pipe(shareReplay(1));
    return this.options$;
  }

  create(req: ScenarioCreate): Observable<ScenarioOut> {
    return this.http.post<ScenarioOut>(`${this.base}/scenarios`, req);
  }

  update(id: string, req: ScenarioUpdate): Observable<ScenarioOut> {
    return this.http.patch<ScenarioOut>(`${this.base}/scenarios/${id}`, req);
  }

  deleteUnused(ids: string[]): Observable<{ deleted: number }> {
    return this.http.post<{ deleted: number }>(`${this.base}/scenarios/delete-unused`, { ids });
  }

  generateScene(req: {
    style: string;
    colorMode: string;
    location?: string;
    timeOfDay?: string;
    weather?: string;
    atmosphere?: string;
    extra?: string;
    prompt?: string;
    raw?: boolean;
  }): Observable<SceneJob> {
    return this.http.post<SceneJob>(`${this.base}/scenarios/generate-scene`, {
      style: req.style,
      color_mode: req.colorMode,
      location: req.location,
      time_of_day: req.timeOfDay,
      weather: req.weather,
      atmosphere: req.atmosphere,
      extra: req.extra,
      prompt: req.prompt,
      raw: req.raw ?? false,
    });
  }

  pollSceneJob(jobId: string): Observable<SceneJob> {
    return this.http.get<SceneJob>(`${this.base}/scenarios/scene-job/${jobId}`);
  }
}
