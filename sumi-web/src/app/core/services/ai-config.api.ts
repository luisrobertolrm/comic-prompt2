import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export type AiType = 'text' | 'image' | 'transcription' | 'voice' | 'video';

export interface AiConfig {
  id: number;
  name: string;
  kind: string;
  base_url: string;
  model: string;
  language: string;
  key_hint: string;
  active: boolean;
  updated_at: string;
}

export interface AiConfigIn {
  name: string;
  kind: string;
  base_url: string;
  api_key: string;
  model: string;
  language: string;
  active: boolean;
}

/** `api_key: null` mantém a chave salva. */
export interface AiConfigUpdate extends Omit<AiConfigIn, 'api_key'> {
  api_key: string | null;
}

export interface TextTestOut { response: string; model: string; elapsed_ms: number; }
export interface ImageTestOut { image: string; model: string; elapsed_ms: number; }
export interface TranscriptionTestOut { text: string; model: string; elapsed_ms: number; }
export interface VoiceTestOut { audio: string; model: string; elapsed_ms: number; }
export interface VideoTestOut { status: string; model: string; elapsed_ms: number; }

export abstract class AiConfigApi {
  abstract list(type: AiType): Observable<AiConfig[]>;
  abstract create(type: AiType, data: AiConfigIn): Observable<AiConfig>;
  abstract update(type: AiType, id: number, data: AiConfigUpdate): Observable<AiConfig>;
  /** Retorna a lista inteira do tipo, já com a troca de ativa aplicada. */
  abstract setActive(type: AiType, id: number, active: boolean): Observable<AiConfig[]>;
  abstract remove(type: AiType, id: number): Observable<void>;
  abstract testText(id: number): Observable<TextTestOut>;
  abstract testImage(id: number): Observable<ImageTestOut>;
  abstract testTranscription(id: number, audio: Blob): Observable<TranscriptionTestOut>;
  abstract testVoice(id: number): Observable<VoiceTestOut>;
  abstract testVideo(id: number): Observable<VideoTestOut>;
}

@Injectable()
export class HttpAiConfigApi extends AiConfigApi {
  private http = inject(HttpClient);
  private base = `${environment.apiUrl}/admin/ai-configs`;

  list(type: AiType): Observable<AiConfig[]> {
    return this.http.get<AiConfig[]>(`${this.base}/${type}`);
  }

  create(type: AiType, data: AiConfigIn): Observable<AiConfig> {
    return this.http.post<AiConfig>(`${this.base}/${type}`, data);
  }

  update(type: AiType, id: number, data: AiConfigUpdate): Observable<AiConfig> {
    return this.http.put<AiConfig>(`${this.base}/${type}/${id}`, data);
  }

  setActive(type: AiType, id: number, active: boolean): Observable<AiConfig[]> {
    return this.http.patch<AiConfig[]>(`${this.base}/${type}/${id}/active`, { active });
  }

  remove(type: AiType, id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/${type}/${id}`);
  }

  testText(id: number): Observable<TextTestOut> {
    return this.http.post<TextTestOut>(`${this.base}/text/${id}/test`, {});
  }

  testImage(id: number): Observable<ImageTestOut> {
    return this.http.post<ImageTestOut>(`${this.base}/image/${id}/test`, {});
  }

  testTranscription(id: number, audio: Blob): Observable<TranscriptionTestOut> {
    const ext = audio.type.includes('mp4') ? 'mp4' : audio.type.includes('ogg') ? 'ogg' : 'webm';
    const form = new FormData();
    form.append('file', audio, `audio.${ext}`);
    return this.http.post<TranscriptionTestOut>(`${this.base}/transcription/${id}/test`, form);
  }

  testVoice(id: number): Observable<VoiceTestOut> {
    return this.http.post<VoiceTestOut>(`${this.base}/voice/${id}/test`, {});
  }

  testVideo(id: number): Observable<VideoTestOut> {
    return this.http.post<VideoTestOut>(`${this.base}/video/${id}/test`, {});
  }
}
