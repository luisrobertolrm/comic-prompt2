import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { environment } from '../../../environments/environment';

const DEFAULT_PAYLOAD = {
  model: 'image-01',
  prompt:
    'Classic shoujo manga style, black and white screentone, character portrait, ' +
    'a teenage girl with black hair and blunt bangs, school uniform, detailed face',
  aspect_ratio: '1:1',
  response_format: 'base64',
  n: 1,
  prompt_optimizer: true,
};

@Component({
  selector: 'app-image-test',
  standalone: true,
  templateUrl: './image-test.component.html',
})
export class ImageTestComponent {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  json = signal(JSON.stringify(DEFAULT_PAYLOAD, null, 2));
  loading = signal(false);
  error = signal('');
  images = signal<string[]>([]);
  elapsed = signal<number | null>(null);

  setJson(ev: Event): void {
    this.json.set((ev.target as HTMLTextAreaElement).value);
  }

  generate(): void {
    let payload: unknown;
    try {
      payload = JSON.parse(this.json());
    } catch (e) {
      this.error.set(`JSON inválido: ${(e as Error).message}`);
      return;
    }
    this.loading.set(true);
    this.error.set('');
    this.images.set([]);
    this.elapsed.set(null);
    const t0 = performance.now();
    this.http.post<{ urls: string[]; b64: string[] }>(`${this.base}/image-test`, payload).subscribe({
      next: r => {
        this.images.set([...r.b64.map(b => `data:image/png;base64,${b}`), ...r.urls]);
        this.elapsed.set(Math.round((performance.now() - t0) / 100) / 10);
        this.loading.set(false);
        if (!r.b64.length && !r.urls.length) this.error.set('MiniMax não retornou imagens.');
      },
      error: err => {
        this.error.set(err?.error?.detail ?? err?.message ?? 'Erro ao gerar.');
        this.loading.set(false);
      },
    });
  }
}
