import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { API_URL, AuthService } from './auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  let request = req;
  if (auth.token && req.url.startsWith(API_URL)) {
    request = req.clone({ setHeaders: { Authorization: `Bearer ${auth.token}` } });
  }
  return next(request).pipe(
    catchError((err) => {
      if (err.status === 401 && !req.url.endsWith('/auth/login') && !req.url.endsWith('/auth/register')) {
        auth.logout();
        void router.navigateByUrl('/login');
      }
      return throwError(() => err);
    }),
  );
};
