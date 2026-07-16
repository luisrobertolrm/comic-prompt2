import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { PendingUserOut } from '../models/auth.models';

@Injectable({ providedIn: 'root' })
export class AdminService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  listPending(): Observable<PendingUserOut[]> {
    return this.http.get<PendingUserOut[]>(`${this.base}/admin/users/pending`);
  }

  approve(id: string): Observable<void> {
    return this.http.post<void>(`${this.base}/admin/users/${id}/approve`, {});
  }

  reject(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/admin/users/${id}`);
  }
}
