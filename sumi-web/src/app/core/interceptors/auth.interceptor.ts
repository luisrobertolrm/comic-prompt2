import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const token = auth.getToken();
  const authed = token
    ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : req;

  return next(authed).pipe(
    catchError(err => {
      // Não invalida a sessão em rotas de auth — 401 aí significa credenciais erradas
      if (err?.status === 401 && !req.url.includes('/auth/')) auth.handleUnauthorized();
      return throwError(() => err);
    }),
  );
};
