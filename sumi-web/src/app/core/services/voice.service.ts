import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface SavedVoice {
  id: string;
  name: string;
  voice_id: string;
  age_start: number | null;
  age_end: number | null;
  sex: string | null;
  details: string | null;
}

export interface SavedVoiceInput {
  name: string;
  voice_id: string;
  age_start: number | null;
  age_end: number | null;
  sex: string | null;
  details: string | null;
}

@Injectable({ providedIn: 'root' })
export class VoiceService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  synthesize(text: string, voiceId: string): Observable<Blob> {
    return this.http.post(
      `${this.base}/voice/test`,
      { text, voice_id: voiceId },
      { responseType: 'blob' },
    );
  }

  list(): Observable<SavedVoice[]> {
    return this.http.get<SavedVoice[]>(`${this.base}/voice`);
  }

  create(voice: SavedVoiceInput): Observable<SavedVoice> {
    return this.http.post<SavedVoice>(`${this.base}/voice`, voice);
  }

  update(id: string, voice: SavedVoiceInput): Observable<SavedVoice> {
    return this.http.patch<SavedVoice>(`${this.base}/voice/${id}`, voice);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/voice/${id}`);
  }
}
