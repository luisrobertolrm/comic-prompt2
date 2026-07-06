import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface AppSettings {
  local_ai_url: string;
  local_ai_model: string;
  local_ai_enabled: boolean;
}

@Injectable({ providedIn: 'root' })
export class SettingsService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  get(): Observable<AppSettings> {
    return this.http.get<AppSettings>(`${this.base}/settings`);
  }

  update(patch: Partial<AppSettings>): Observable<AppSettings> {
    return this.http.put<AppSettings>(`${this.base}/settings`, patch);
  }

  /** Lista os modelos do Ollama na URL informada (ou na salva). Também testa a conexão. */
  listModels(url?: string): Observable<{ models: string[] }> {
    let params = new HttpParams();
    if (url) params = params.set('url', url);
    return this.http.get<{ models: string[] }>(`${this.base}/settings/local-ai/models`, { params });
  }
}
