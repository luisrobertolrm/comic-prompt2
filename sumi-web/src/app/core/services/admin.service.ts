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
  minimax_text_model: string;
  minimax_image_model: string;
  minimax_voice_model: string;
  minimax_video_model: string;
  minimax_group_id: string;
  stt_model: string;
  stt_language: string;
}

export type ApiKeyName = 'openai_api_key' | 'minimax_api_key' | 'byteplus_api_key';

export interface ApiKeyStatus {
  source: 'db' | 'env' | '';
  hint: string;
}

export interface AppSettingsOut {
  values: AppSettingsValues;
  /** Valores do .env, usados quando o campo está vazio. */
  defaults: AppSettingsValues;
  keys: Record<ApiKeyName, ApiKeyStatus>;
}

/** Chave ausente = mantém a salva; "" = remove; texto = grava a nova. */
export type AppSettingsUpdate = AppSettingsValues & Partial<Record<ApiKeyName, string>>;

export interface TextTestOut {
  status: 'ok' | 'error';
  provider: string;
  model: string;
  response?: string;
  detail?: string;
  elapsed_ms?: string;
}

export interface ImageTestOut {
  provider: string;
  model: string;
  image: string;
  elapsed_ms: number;
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

  updateAppSettings(values: AppSettingsUpdate): Observable<AppSettingsOut> {
    return this.http.put<AppSettingsOut>(`${this.base}/admin/app-settings`, values);
  }

  testText(): Observable<TextTestOut> {
    return this.http.get<TextTestOut>(`${this.base}/health/ai`);
  }

  testImage(): Observable<ImageTestOut> {
    return this.http.post<ImageTestOut>(`${this.base}/admin/app-settings/test-image`, {});
  }
}
