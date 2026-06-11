import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface StyleOption {
  id: string;
  label: string;
  note: string;
}

export interface StyleCatalog {
  styles: StyleOption[];
  color_modes: StyleOption[];
  default_style: string;
  default_color_mode: string;
}

@Injectable({ providedIn: 'root' })
export class StyleService {
  private http = inject(HttpClient);
  private catalog$: Observable<StyleCatalog> | null = null;

  catalog(): Observable<StyleCatalog> {
    this.catalog$ ??= this.http
      .get<StyleCatalog>(`${environment.apiUrl}/styles`)
      .pipe(shareReplay(1));
    return this.catalog$;
  }
}
