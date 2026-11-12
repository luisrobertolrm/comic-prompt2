import { Component, OnInit, inject, signal } from '@angular/core';
import { AdminService, AppSettingsValues } from '../../core/services/admin.service';

type Field = keyof AppSettingsValues;

interface FieldDef {
  key: Field;
  label: string;
  options?: string[];
}

const EMPTY: AppSettingsValues = {
  ai_text_provider: '',
  ai_text_model: '',
  ai_image_provider: '',
  ai_image_model: '',
  seedream_model: '',
  stt_model: '',
  stt_language: '',
};

@Component({
  selector: 'app-app-settings',
  standalone: true,
  templateUrl: './app-settings.component.html',
})
export class AppSettingsComponent implements OnInit {
  private admin = inject(AdminService);

  readonly sections: { title: string; hint: string; fields: FieldDef[] }[] = [
    {
      title: 'Texto',
      hint: 'Geração de sinopse, roteiro e metadados.',
      fields: [
        { key: 'ai_text_provider', label: 'Provider', options: ['openai', 'minimax'] },
        { key: 'ai_text_model', label: 'Modelo (OpenAI)' },
      ],
    },
    {
      title: 'Imagem',
      hint: 'Retratos, cenários e painéis.',
      fields: [
        { key: 'ai_image_provider', label: 'Provider', options: ['openai', 'minimax', 'comfyui', 'seedream'] },
        { key: 'ai_image_model', label: 'Modelo (OpenAI)' },
        { key: 'seedream_model', label: 'Modelo (Seedream)' },
      ],
    },
    {
      title: 'Voz para texto',
      hint: 'Ditado nos campos de texto (Ctrl+Shift+Espaço). Usa a OpenAI.',
      fields: [
        { key: 'stt_model', label: 'Modelo (ex.: gpt-4o-mini-transcribe, whisper-1)' },
        { key: 'stt_language', label: 'Idioma (código ISO, ex.: pt, en)' },
      ],
    },
  ];

  values = signal<AppSettingsValues>({ ...EMPTY });
  defaults = signal<AppSettingsValues>({ ...EMPTY });
  loading = signal(true);
  saving = signal(false);
  saved = signal(false);
  error = signal('');

  ngOnInit(): void {
    this.admin.getAppSettings().subscribe({
      next: s => {
        this.values.set(s.values);
        this.defaults.set(s.defaults);
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

  private detail(err: unknown): string {
    return (err as { error?: { detail?: string } })?.error?.detail || 'Falha na operação.';
  }

  save(): void {
    if (this.saving()) return;
    this.saving.set(true);
    this.error.set('');
    this.saved.set(false);
    this.admin.updateAppSettings(this.values()).subscribe({
      next: s => {
        this.values.set(s.values);
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
}
