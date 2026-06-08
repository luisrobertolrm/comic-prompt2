import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

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
}
