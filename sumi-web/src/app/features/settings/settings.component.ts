import { Component, OnInit, inject, signal } from '@angular/core';
import { AppSettings, SettingsService } from '../../core/services/settings.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  templateUrl: './settings.component.html',
})
export class SettingsComponent implements OnInit {
  private settingsService = inject(SettingsService);

  url = signal('');
  model = signal('');
  enabled = signal(false);

  models = signal<string[]>([]);
  loading = signal(true);
  testing = signal(false);
  saving = signal(false);
  testOk = signal(false);
  error = signal('');
  saved = signal(false);

  ngOnInit(): void {
    this.settingsService.get().subscribe({
      next: s => {
        this.url.set(s.local_ai_url);
        this.model.set(s.local_ai_model);
        this.enabled.set(s.local_ai_enabled);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  private detail(err: unknown): string {
    return (err as { error?: { detail?: string } })?.error?.detail || 'Falha na operação.';
  }

  fetchModels(): void {
    if (this.testing()) return;
    this.testing.set(true);
    this.error.set('');
    this.testOk.set(false);
    this.settingsService.listModels(this.url().trim()).subscribe({
      next: ({ models }) => {
        this.models.set(models);
        this.testOk.set(true);
        if (models.length && !models.includes(this.model())) this.model.set(models[0]);
        this.testing.set(false);
      },
      error: err => {
        this.models.set([]);
        this.error.set(this.detail(err));
        this.testing.set(false);
      },
    });
  }

  save(): void {
    if (this.saving()) return;
    this.saving.set(true);
    this.error.set('');
    this.saved.set(false);
    const patch: Partial<AppSettings> = {
      local_ai_url: this.url().trim(),
      local_ai_model: this.model().trim(),
      local_ai_enabled: this.enabled(),
    };
    this.settingsService.update(patch).subscribe({
      next: () => {
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
