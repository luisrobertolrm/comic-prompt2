import { Component, ElementRef, OnInit, inject, signal, viewChild } from '@angular/core';
import {
  AdminService,
  ApiKeyName,
  ApiKeyStatus,
  AppSettingsUpdate,
  AppSettingsValues,
  ImageTestOut,
} from '../../core/services/admin.service';
import { DictationService } from '../../core/services/dictation.service';

type Field = keyof AppSettingsValues;
type TestKind = 'text' | 'image' | 'stt';

interface FieldDef {
  key: Field;
  label: string;
  options?: string[];
}

interface Section {
  title: string;
  hint: string;
  fields: FieldDef[];
  test?: TestKind;
}

const EMPTY: AppSettingsValues = {
  ai_text_provider: '',
  ai_text_model: '',
  ai_image_provider: '',
  ai_image_model: '',
  seedream_model: '',
  minimax_text_model: '',
  minimax_image_model: '',
  minimax_voice_model: '',
  minimax_video_model: '',
  minimax_group_id: '',
  stt_model: '',
  stt_language: '',
};

const NO_KEY: ApiKeyStatus = { source: '', hint: '' };

@Component({
  selector: 'app-app-settings',
  standalone: true,
  templateUrl: './app-settings.component.html',
})
export class AppSettingsComponent implements OnInit {
  private admin = inject(AdminService);
  protected dictation = inject(DictationService);
  private sttBox = viewChild<ElementRef<HTMLTextAreaElement>>('sttBox');

  readonly apiKeys: { key: ApiKeyName; label: string }[] = [
    { key: 'openai_api_key', label: 'OpenAI (texto, imagem e transcrição)' },
    { key: 'minimax_api_key', label: 'MiniMax (texto, imagem, voz e vídeo)' },
    { key: 'byteplus_api_key', label: 'BytePlus (imagem Seedream)' },
  ];

  readonly sections: Section[] = [
    {
      title: 'Texto',
      hint: 'Geração de sinopse, roteiro e metadados.',
      test: 'text',
      fields: [
        { key: 'ai_text_provider', label: 'Provider', options: ['openai', 'minimax'] },
        { key: 'ai_text_model', label: 'Modelo OpenAI' },
        { key: 'minimax_text_model', label: 'Modelo MiniMax' },
      ],
    },
    {
      title: 'Imagem',
      hint: 'Retratos, cenários e painéis. O teste gera 1 imagem e consome créditos.',
      test: 'image',
      fields: [
        { key: 'ai_image_provider', label: 'Provider', options: ['openai', 'minimax', 'comfyui', 'seedream'] },
        { key: 'ai_image_model', label: 'Modelo OpenAI' },
        { key: 'minimax_image_model', label: 'Modelo MiniMax' },
        { key: 'seedream_model', label: 'Modelo Seedream' },
      ],
    },
    {
      title: 'Voz para texto',
      hint: 'Ditado nos campos de texto (Ctrl+Shift+Espaço). Usa a chave da OpenAI.',
      test: 'stt',
      fields: [
        { key: 'stt_model', label: 'Modelo (ex.: gpt-4o-mini-transcribe, whisper-1)' },
        { key: 'stt_language', label: 'Idioma (código ISO, ex.: pt, en)' },
      ],
    },
    {
      title: 'MiniMax — voz e vídeo',
      hint: 'Narração e geração de vídeo.',
      fields: [
        { key: 'minimax_voice_model', label: 'Modelo de voz' },
        { key: 'minimax_video_model', label: 'Modelo de vídeo' },
        { key: 'minimax_group_id', label: 'Group ID' },
      ],
    },
  ];

  values = signal<AppSettingsValues>({ ...EMPTY });
  defaults = signal<AppSettingsValues>({ ...EMPTY });
  keyStatus = signal<Record<ApiKeyName, ApiKeyStatus>>({
    openai_api_key: NO_KEY,
    minimax_api_key: NO_KEY,
    byteplus_api_key: NO_KEY,
  });
  /** Chaves alteradas na tela: texto = nova, "" = remover. */
  keyEdits = signal<Partial<Record<ApiKeyName, string>>>({});

  loading = signal(true);
  saving = signal(false);
  saved = signal(false);
  error = signal('');

  testing = signal<TestKind | null>(null);
  textResult = signal('');
  textError = signal('');
  imageResult = signal<ImageTestOut | null>(null);
  imageError = signal('');

  ngOnInit(): void {
    this.admin.getAppSettings().subscribe({
      next: s => {
        this.values.set(s.values);
        this.defaults.set(s.defaults);
        this.keyStatus.set(s.keys);
        this.loading.set(false);
      },
      error: err => {
        this.error.set(this.detail(err));
        this.loading.set(false);
      },
    });
  }

  set(key: Field, value: string): void {
    this.values.update(v => ({ ...v, [key]: value }));
  }

  setKey(key: ApiKeyName, value: string): void {
    this.keyEdits.update(k => {
      const next = { ...k };
      if (value) next[key] = value;
      else delete next[key];
      return next;
    });
  }

  removeKey(key: ApiKeyName): void {
    this.keyEdits.update(k => ({ ...k, [key]: '' }));
  }

  keyLabel(key: ApiKeyName): string {
    const edit = this.keyEdits()[key];
    if (edit === '') return 'Será removida ao salvar';
    const st = this.keyStatus()[key];
    if (st.source === 'db') return `Salva no sistema (${st.hint})`;
    if (st.source === 'env') return `Do .env (${st.hint})`;
    return 'Não configurada';
  }

  private detail(err: unknown): string {
    return (err as { error?: { detail?: string } })?.error?.detail || 'Falha na operação.';
  }

  save(): void {
    if (this.saving()) return;
    this.saving.set(true);
    this.error.set('');
    this.saved.set(false);
    const payload: AppSettingsUpdate = { ...this.values(), ...this.keyEdits() };
    this.admin.updateAppSettings(payload).subscribe({
      next: s => {
        this.values.set(s.values);
        this.keyStatus.set(s.keys);
        this.keyEdits.set({});
        this.saving.set(false);
        this.saved.set(true);
        setTimeout(() => this.saved.set(false), 2000);
      },
      error: err => {
        this.error.set(this.detail(err));
        this.saving.set(false);
      },
    });
  }

  testText(): void {
    this.testing.set('text');
    this.textResult.set('');
    this.textError.set('');
    this.admin.testText().subscribe({
      next: r => {
        if (r.status === 'ok') {
          this.textResult.set(`✓ ${r.provider} · ${r.model} · ${r.elapsed_ms} ms — “${r.response}”`);
        } else {
          this.textError.set(`${r.provider} · ${r.model}: ${r.detail}`);
        }
        this.testing.set(null);
      },
      error: err => {
        this.textError.set(this.detail(err));
        this.testing.set(null);
      },
    });
  }

  testStt(): void {
    this.dictation.toggle(this.sttBox()?.nativeElement ?? null);
  }

  testImage(): void {
    this.testing.set('image');
    this.imageResult.set(null);
    this.imageError.set('');
    this.admin.testImage().subscribe({
      next: r => {
        this.imageResult.set(r);
        this.testing.set(null);
      },
      error: err => {
        this.imageError.set(this.detail(err));
        this.testing.set(null);
      },
    });
  }
}
