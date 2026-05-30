import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { CharacterCreate, CharacterOut } from '../models/home.models';

@Injectable({ providedIn: 'root' })
export class CharacterService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  listAll(): Observable<CharacterOut[]> {
    return this.http.get<CharacterOut[]>(`${this.base}/characters`);
  }

  create(req: CharacterCreate): Observable<CharacterOut> {
    return this.http.post<CharacterOut>(`${this.base}/characters`, req);
  }
}
