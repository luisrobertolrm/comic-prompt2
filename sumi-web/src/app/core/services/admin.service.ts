import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { PendingUserOut } from '../models/auth.models';

export interface AppSettingsValues {
  ai_text_provider: string;
  ai_text_model: string;
  ai_image_provider: string;
  ai_image_model: string;
  seedream_model: string;
  stt_model: string;
  stt_language: string;
}

export interface AppSettingsOut {
  values: AppSettingsValues;
  /** Valores do .env, usados quando o campo está vazio. */
  defaults: AppSettingsValues;
}

@Injectable({ providedIn: 'root' })
export class AdminService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  listPending(): Observable<PendingUserOut[]> {
    return this.http.get<PendingUserOut[]>(`${this.base}/admin/users/pending`);
  }

  approve(id: string): Observable<void> {
    return this.http.post<void>(`${this.base}/admin/users/${id}/approve`, {});
  }

  reject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/admin/users/${id}`);
  }

  getAppSettings(): Observable<AppSettingsOut> {
    return this.http.get<AppSettingsOut>(`${this.base}/admin/app-settings`);
  }

  updateAppSettings(values: AppSettingsValues): Observable<AppSettingsOut> {
    return this.http.put<AppSettingsOut>(`${this.base}/admin/app-settings`, values);
  }
}
