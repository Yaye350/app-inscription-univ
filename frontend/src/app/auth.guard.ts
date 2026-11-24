import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.token || !auth.user()) {
    return router.createUrlTree(['/login']);
  }
  return true;
};

export const roleGuard: CanActivateFn = (route) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const roles = route.data['roles'] as string[] | undefined;
  const user = auth.user();
  if (!user) {
    return router.createUrlTree(['/login']);
  }
  if (roles && !roles.includes(user.role)) {
    return router.createUrlTree(['/']);
  }
  return true;
};
