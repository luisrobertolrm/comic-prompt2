import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { PublicProjectOut } from '../models/home.models';
import type { PanelOut } from '../models/panel.models';

export interface PublicProjectDetailOut extends PublicProjectOut {
  panels: PanelOut[];
  minha_reacao: boolean | null;
}

export interface ReactionOut {
  quantidade_positiva: number;
  quantidade_negativa: number;
  minha_reacao: boolean | null;
}

@Injectable({ providedIn: 'root' })
export class PublicService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  list(): Observable<PublicProjectOut[]> {
    return this.http.get<PublicProjectOut[]>(`${this.base}/public/projects`);
  }

  get(id: string): Observable<PublicProjectDetailOut> {
    return this.http.get<PublicProjectDetailOut>(`${this.base}/public/projects/${id}`);
  }

  react(id: string, positivo: boolean): Observable<ReactionOut> {
    return this.http.post<ReactionOut>(`${this.base}/public/projects/${id}/reaction`, { positivo });
  }
}
