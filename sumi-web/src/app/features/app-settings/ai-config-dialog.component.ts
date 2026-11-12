import { Component, ElementRef, inject, output, signal, viewChild } from '@angular/core';
import { Observable } from 'rxjs';
import { AiConfig, AiConfigApi } from '../../core/services/ai-config.api';
import { AiTab } from './ai-kinds';

interface Form {
  name: string;
  kind: string;
  base_url: string;
  api_key: string;
  model: string;
  language: string;
  active: boolean;
}

@Component({
  selector: 'app-ai-config-dialog',
  standalone: true,
  templateUrl: './ai-config-dialog.component.html',
  styleUrl: './app-settings.component.scss',
})
export class AiConfigDialogComponent {
  private api = inject(AiConfigApi);
  private dialog = viewChild.required<ElementRef<HTMLDialogElement>>('dialog');

  saved = output<void>();

  tab = signal<AiTab | null>(null);
  editing = signal<AiConfig | null>(null);
  /** Nome da configuração ativa hoje, para avisar que ela será desativada. */
  currentActive = signal('');
  form = signal<Form>(this.empty());
  saving = signal(false);
  error = signal('');

  open(tab: AiTab, config: AiConfig | null, currentActive: string): void {
    this.tab.set(tab);
    this.editing.set(config);
    this.currentActive.set(config?.active ? '' : currentActive);
    this.error.set('');
    this.form.set(config
      ? { ...config, api_key: '' }
      : { ...this.empty(), kind: tab.kinds[0].kind, base_url: tab.kinds[0].defaultUrl });
    this.dialog().nativeElement.showModal();
  }

  close(): void {
    this.dialog().nativeElement.close();
  }

  set<K extends keyof Form>(key: K, value: Form[K]): void {
    this.form.update(f => ({ ...f, [key]: value }));
  }

  changeKind(kind: string): void {
    const kinds = this.tab()?.kinds ?? [];
    const previous = kinds.find(k => k.kind === this.form().kind);
    const next = kinds.find(k => k.kind === kind);
    this.form.update(f => {
      const urlUntouched = !f.base_url.trim() || f.base_url === previous?.defaultUrl;
      return { ...f, kind, base_url: urlUntouched && next ? next.defaultUrl : f.base_url };
    });
  }

  save(): void {
    const tab = this.tab();
    if (!tab || this.saving()) return;
    const f = this.form();
    const current = this.editing();
    this.saving.set(true);
    this.error.set('');
    const request: Observable<unknown> = current
      ? this.api.update(tab.type, current.id, { ...f, api_key: f.api_key || null })
      : this.api.create(tab.type, f);
    request.subscribe({
      next: () => {
        this.saving.set(false);
        this.close();
        this.saved.emit();
      },
      error: err => {
        this.saving.set(false);
        this.error.set(errorDetail(err));
      },
    });
  }

  private empty(): Form {
    return { name: '', kind: '', base_url: '', api_key: '', model: '', language: '', active: false };
  }
}

export function errorDetail(err: unknown): string {
  const detail = (err as { error?: { detail?: unknown } })?.error?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map(d => (d as { msg?: string }).msg ?? '').filter(Boolean).join(' · ') || 'Dados inválidos.';
  }
  return 'Falha na operação.';
}
