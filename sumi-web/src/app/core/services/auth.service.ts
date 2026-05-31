import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserOut,
} from '../models/auth.models';

const TOKEN_KEY = 'sumi_token';
const USER_KEY  = 'sumi_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http   = inject(HttpClient);
  private router = inject(Router);
  private base   = environment.apiUrl;

  currentUser = signal<UserOut | null>(this.loadStoredUser());

  login(req: LoginRequest): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.base}/auth/login`, req).pipe(
      tap((res) => this.persist(res)),
      catchError(this.handleError),
    );
  }

  register(req: RegisterRequest): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.base}/auth/register`, req).pipe(
      tap((res) => this.persist(res)),
      catchError(this.handleError),
    );
  }

  loginAsGuest(): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${this.base}/auth/oauth/guest`, {}).pipe(
      tap((res) => this.persist(res)),
      catchError(this.handleError),
    );
  }

  requestPasswordReset(email: string): Observable<{ detail: string }> {
    return this.http
      .post<{ detail: string }>(`${this.base}/auth/password-reset/request`, { email })
      .pipe(catchError(this.handleError));
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.currentUser.set(null);
    void this.router.navigate(['/auth']);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  handleUnauthorized(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.currentUser.set(null);
    void this.router.navigate(['/auth']);
  }

  private persist(res: TokenResponse): void {
    localStorage.setItem(TOKEN_KEY, res.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    this.currentUser.set(res.user);
  }

  private loadStoredUser(): UserOut | null {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return null;
    try {
      const [, payload] = token.split('.');
      const decoded = JSON.parse(atob(payload)) as { exp: number };
      if (decoded.exp * 1000 < Date.now()) {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        return null;
      }
      const stored = localStorage.getItem(USER_KEY);
      return stored ? (JSON.parse(stored) as UserOut) : null;
    } catch {
      return null;
    }
  }

  private handleError(err: HttpErrorResponse): Observable<never> {
    const message: string =
      (err.error as { detail?: string })?.detail ?? 'Erro inesperado. Tente novamente.';
    return throwError(() => new Error(message));
  }
}
