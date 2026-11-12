import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { environment } from '../../../environments/environment';

type DictationState = 'idle' | 'recording' | 'transcribing';
type TextField = HTMLInputElement | HTMLTextAreaElement;

const TEXT_INPUT_TYPES = ['text', 'search', ''];

/**
 * Ditado global: Ctrl+Shift+Espaço num input/textarea grava o microfone;
 * repetir o atalho transcreve e insere o texto no cursor. Esc cancela.
 */
@Injectable({ providedIn: 'root' })
export class DictationService {
  private http = inject(HttpClient);

  state = signal<DictationState>('idle');
  error = signal('');

  private recorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private target: TextField | null = null;
  private selection: [number, number] = [0, 0];
  private cancelled = false;

  listen(): void {
    document.addEventListener('keydown', e => this.onKeydown(e), true);
  }

  private onKeydown(e: KeyboardEvent): void {
    if (e.key === 'Escape' && this.state() === 'recording') {
      e.preventDefault();
      this.cancelled = true;
      this.recorder?.stop();
      return;
    }
    if (!(e.ctrlKey && e.shiftKey && e.code === 'Space')) return;
    e.preventDefault();
    const field = asTextField(document.activeElement);
    if (field || this.state() === 'recording') this.toggle(field);
  }

  /** Inicia a gravação para `field` ou, se já estiver gravando, conclui. */
  toggle(field: TextField | null): void {
    if (this.state() === 'recording') this.recorder?.stop();
    else if (this.state() === 'idle' && field) void this.start(field);
  }

  private async start(field: TextField): Promise<void> {
    this.error.set('');
    this.target = field;
    this.selection = [field.selectionStart ?? field.value.length, field.selectionEnd ?? field.value.length];
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      this.showError('Microfone indisponível ou sem permissão.');
      return;
    }
    this.chunks = [];
    this.cancelled = false;
    this.recorder = new MediaRecorder(stream);
    this.recorder.ondataavailable = ev => { if (ev.data.size) this.chunks.push(ev.data); };
    this.recorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      const type = this.recorder?.mimeType || 'audio/webm';
      this.recorder = null;
      if (this.cancelled || !this.chunks.length) {
        this.state.set('idle');
        return;
      }
      this.send(new Blob(this.chunks, { type }));
    };
    this.recorder.start();
    this.state.set('recording');
  }

  private send(audio: Blob): void {
    this.state.set('transcribing');
    const ext = audio.type.includes('mp4') ? 'mp4' : audio.type.includes('ogg') ? 'ogg' : 'webm';
    const form = new FormData();
    form.append('file', audio, `audio.${ext}`);
    this.http.post<{ text: string }>(`${environment.apiUrl}/speech/transcribe`, form).subscribe({
      next: ({ text }) => {
        this.state.set('idle');
        if (text && this.target) insertAt(this.target, text, this.selection);
      },
      error: err => {
        this.state.set('idle');
        this.showError(err?.error?.detail || 'Falha ao transcrever o áudio.');
      },
    });
  }

  /** Grava o microfone até `stop` ser chamado e devolve o áudio cru, sem transcrever. */
  async recordBlob(): Promise<{ stop: () => void; audio: Promise<Blob> }> {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    const chunks: Blob[] = [];
    recorder.ondataavailable = ev => { if (ev.data.size) chunks.push(ev.data); };
    const audio = new Promise<Blob>(resolve => {
      recorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        resolve(new Blob(chunks, { type: recorder.mimeType || 'audio/webm' }));
      };
    });
    recorder.start();
    return { stop: () => recorder.stop(), audio };
  }

  private showError(msg: string): void {
    this.error.set(msg);
    setTimeout(() => this.error.set(''), 4000);
  }
}

function asTextField(el: Element | null): TextField | null {
  if (el instanceof HTMLTextAreaElement) return el.readOnly || el.disabled ? null : el;
  if (el instanceof HTMLInputElement && TEXT_INPUT_TYPES.includes(el.getAttribute('type') ?? '')) {
    return el.readOnly || el.disabled ? null : el;
  }
  return null;
}

function insertAt(field: TextField, text: string, [start, end]: [number, number]): void {
  const before = field.value.slice(0, start);
  const chunk = before && !/\s$/.test(before) ? ` ${text}` : text;
  field.focus();
  field.setRangeText(chunk, start, end, 'end');
  // Avisa [value]/(input), ngModel e reactive forms.
  field.dispatchEvent(new Event('input', { bubbles: true }));
}
