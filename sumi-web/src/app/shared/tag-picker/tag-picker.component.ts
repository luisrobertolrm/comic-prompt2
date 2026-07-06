import { Component, EventEmitter, Output, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { TagCatalogService, TagSuggestion } from '../../core/services/tag-catalog.service';

@Component({
  selector: 'app-tag-picker',
  standalone: true,
  templateUrl: './tag-picker.component.html',
  styleUrl: './tag-picker.component.scss',
})
export class TagPickerComponent {
  @Output() confirm = new EventEmitter<string[]>();
  @Output() cancel = new EventEmitter<void>();

  private catalog = inject(TagCatalogService);
  private query$ = new Subject<string>();

  query = signal('');
  suggestions = signal<TagSuggestion[]>([]);
  selected = signal<string[]>([]);
  active = signal(-1);

  constructor() {
    this.query$
      .pipe(
        debounceTime(200),
        distinctUntilChanged(),
        switchMap(q => this.catalog.search(q)),
        takeUntilDestroyed(),
      )
      .subscribe(s => {
        this.suggestions.set(s);
        this.active.set(s.length ? 0 : -1);
      });
  }

  onInput(e: Event): void {
    const v = (e.target as HTMLInputElement).value;
    this.query.set(v);
    this.query$.next(v);
  }

  onKeydown(e: KeyboardEvent): void {
    const s = this.suggestions();
    if (e.key === 'ArrowDown' && s.length) {
      e.preventDefault();
      this.active.set((this.active() + 1) % s.length);
    } else if (e.key === 'ArrowUp' && s.length) {
      e.preventDefault();
      this.active.set((this.active() - 1 + s.length) % s.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const a = this.active();
      if (a >= 0 && s[a]) this.pick(s[a].name);
      else if (this.query().trim()) this.pick(this.query().trim().toLowerCase());
    } else if (e.key === 'Escape') {
      this.clearQuery();
    }
  }

  pick(name: string): void {
    if (!this.selected().includes(name)) this.selected.update(l => [...l, name]);
    this.clearQuery();
  }

  remove(name: string): void {
    this.selected.update(l => l.filter(t => t !== name));
  }

  ok(): void {
    if (this.selected().length) this.confirm.emit(this.selected());
    this.reset();
  }

  onCancel(): void {
    this.reset();
    this.cancel.emit();
  }

  fmtCount(n: number): string {
    return n >= 1000 ? `${Math.round(n / 1000)}k` : String(n);
  }

  private clearQuery(): void {
    this.query.set('');
    this.suggestions.set([]);
    this.active.set(-1);
  }

  private reset(): void {
    this.clearQuery();
    this.selected.set([]);
  }
}
