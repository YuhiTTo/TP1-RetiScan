import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

export const adminGuard: CanActivateFn = () => {
  const router = inject(Router);
  const loginRoute = router.createUrlTree(['/admin/login']);

  const token = localStorage.getItem('access_token');
  const accountType = localStorage.getItem('account_type');

  // Sin token o con una cuenta institucional:
  // no permitir abrir pantallas administrativas.
  if (!token || accountType !== 'ADMIN') {
    return loginRoute;
  }

  try {
    const parts = token.split('.');

    if (parts.length !== 3) {
      throw new Error('Token invalido');
    }

    const encodedPayload = parts[1]
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const payload = JSON.parse(atob(encodedPayload)) as {
      account_type?: string;
      exp?: number;
    };

    const expired =
      typeof payload.exp !== 'number' ||
      payload.exp * 1000 <= Date.now();

    if (payload.account_type !== 'ADMIN' || expired) {
      throw new Error('Sesion invalida o expirada');
    }

    return true;

  } catch {
    // Limpiar una sesion administrativa invalida.
    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    return loginRoute;
  }
};
