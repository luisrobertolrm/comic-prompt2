import { Component, ElementRef, OnInit, computed, inject, signal, viewChild } from '@angular/core';
import { Observable, map } from 'rxjs';
import { AiConfig, AiConfigApi, AiType, HttpAiConfigApi } from '../../core/services/ai-config.api';
import { DictationService } from '../../core/services/dictation.service';
import { AiConfigDialogComponent, errorDetail } from './ai-config-dialog.component';
import { AI_TABS, AiTab, kindLabel } from './ai-kinds';

interface TestResult {
  ok: boolean;
  message: string;
  image?: string;
  audio?: string;
}

@Component({
  selector: 'app-app-settings',
  standalone: true,
  imports: [AiConfigDialogComponent],
  providers: [{ provide: AiConfigApi, useClass: HttpAiConfigApi }],
  templateUrl: './app-settings.component.html',
  styleUrl: './app-settings.component.scss',
})
export class AppSettingsComponent implements OnInit {
  private api = inject(AiConfigApi);
  private dictation = inject(DictationService);
  private editor = viewChild.required(AiConfigDialogComponent);
  private confirmDialog = viewChild.required<ElementRef<HTMLDialogElement>>('confirmDialog');

  readonly tabs = AI_TABS;
  readonly kindLabel = kindLabel;

  tab = signal<AiTab>(AI_TABS[0]);
  configs = signal<AiConfig[]>([]);
  loading = signal(true);
  error = signal('');
  hasActive = computed(() => this.configs().some(c => c.active));

  busyId = signal<number | null>(null);
  testingId = signal<number | null>(null);
  recordingId = signal<number | null>(null);
  results = signal<Record<number, TestResult>>({});
  toDelete = signal<AiConfig | null>(null);

  private stopRecording: (() => void) | null = null;

  ngOnInit(): void {
    this.load();
  }

  selectTab(tab: AiTab): void {
    if (tab === this.tab()) return;
    this.tab.set(tab);
    this.results.set({});
    this.load();
  }

  load(): void {
    const type = this.tab().type;
    this.loading.set(true);
    this.error.set('');
    this.api.list(type).subscribe({
      next: list => {
        if (type !== this.tab().type) return;
        this.configs.set(list);
        this.loading.set(false);
      },
      error: err => {
        this.error.set(errorDetail(err));
        this.loading.set(false);
      },
    });
  }

  openNew(): void {
    this.editor().open(this.tab(), null, this.activeName());
  }

  openEdit(config: AiConfig): void {
    this.editor().open(this.tab(), config, this.activeName());
  }

  toggleActive(config: AiConfig): void {
    if (this.busyId() !== null) return;
    this.busyId.set(config.id);
    this.error.set('');
    this.api.setActive(this.tab().type, config.id, !config.active).subscribe({
      next: list => {
        this.configs.set(list);
        this.busyId.set(null);
      },
      error: err => {
        this.error.set(errorDetail(err));
        this.busyId.set(null);
      },
    });
  }

  askDelete(config: AiConfig): void {
    this.toDelete.set(config);
    this.confirmDialog().nativeElement.showModal();
  }

  cancelDelete(): void {
    this.confirmDialog().nativeElement.close();
    this.toDelete.set(null);
  }

  confirmDelete(): void {
    const config = this.toDelete();
    if (!config) return;
    this.cancelDelete();
    this.api.remove(this.tab().type, config.id).subscribe({
      next: () => this.load(),
      error: err => this.error.set(errorDetail(err)),
    });
  }

  test(config: AiConfig): void {
    const type = this.tab().type;
    if (type === 'transcription') {
      void this.testTranscription(config);
      return;
    }
    this.testingId.set(config.id);
    this.setResult(config.id, null);
    this.request(type, config.id).subscribe({
      next: result => {
        this.setResult(config.id, result);
        this.testingId.set(null);
      },
      error: err => {
        this.setResult(config.id, { ok: false, message: errorDetail(err) });
        this.testingId.set(null);
      },
    });
  }

  testLabel(config: AiConfig): string {
    if (this.recordingId() === config.id) return '■ Parar e transcrever';
    if (this.testingId() !== config.id) return this.tab().type === 'transcription' ? '🎙 Testar' : 'Testar';
    return this.tab().type === 'image' ? 'Gerando…' : 'Testando…';
  }

  host(url: string): string {
    try {
      return new URL(url).host;
    } catch {
      return url;
    }
  }

  private activeName(): string {
    return this.configs().find(c => c.active)?.name ?? '';
  }

  private request(type: Exclude<AiType, 'transcription'>, id: number): Observable<TestResult> {
    switch (type) {
      case 'text':
        return this.api.testText(id).pipe(
          map(r => ({ ok: true, message: `✓ ${r.model} · ${r.elapsed_ms} ms — “${r.response}”` })),
        );
      case 'image':
        return this.api.testImage(id).pipe(
          map(r => ({ ok: true, message: `✓ ${r.model} · ${r.elapsed_ms} ms`, image: r.image })),
        );
      case 'voice':
        return this.api.testVoice(id).pipe(
          map(r => ({ ok: true, message: `✓ ${r.model} · ${r.elapsed_ms} ms`, audio: r.audio })),
        );
      case 'video':
        return this.api.testVideo(id).pipe(
          map(r => ({ ok: true, message: `✓ Conexão OK · ${r.model} · ${r.elapsed_ms} ms` })),
        );
    }
  }

  private async testTranscription(config: AiConfig): Promise<void> {
    if (this.recordingId() === config.id) {
      this.stopRecording?.();
      return;
    }
    if (this.recordingId() !== null || this.testingId() !== null) return;
    this.setResult(config.id, null);
    let recording: Awaited<ReturnType<DictationService['recordBlob']>>;
    try {
      recording = await this.dictation.recordBlob();
    } catch {
      this.setResult(config.id, { ok: false, message: 'Microfone indisponível ou sem permissão.' });
      return;
    }
    this.stopRecording = recording.stop;
    this.recordingId.set(config.id);
    const audio = await recording.audio;
    this.stopRecording = null;
    this.recordingId.set(null);
    this.testingId.set(config.id);
    this.api.testTranscription(config.id, audio).subscribe({
      next: r => {
        this.setResult(config.id, { ok: true, message: `✓ ${r.model} · ${r.elapsed_ms} ms — “${r.text}”` });
        this.testingId.set(null);
      },
      error: err => {
        this.setResult(config.id, { ok: false, message: errorDetail(err) });
        this.testingId.set(null);
      },
    });
  }

  private setResult(id: number, result: TestResult | null): void {
    this.results.update(r => {
      const next = { ...r };
      if (result) next[id] = result;
      else delete next[id];
      return next;
    });
  }
}
