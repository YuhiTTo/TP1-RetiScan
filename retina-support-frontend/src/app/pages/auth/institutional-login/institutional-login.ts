import { ChangeDetectorRef, Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';

import { AuthService } from '../../../core/services/auth';


@Component({
  selector: 'app-institutional-login',
  imports: [CommonModule, FormsModule],
  templateUrl: './institutional-login.html',
  styleUrl: './institutional-login.css'
})
export class InstitutionalLogin {

  email = '';
  password = '';

  errorMessage = '';
  loading = false;

  showPassword = false;

  constructor(
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {
  }

  togglePassword(): void {
    this.showPassword = !this.showPassword;
  }

  login(): void {

    this.errorMessage = '';
    this.loading = true;

    this.authService.login({
      email: this.email,
      password: this.password
    }).subscribe({

      next: (response) => {

        this.loading = false;

        if (response.account_type !== 'INSTITUTIONAL') {
          this.errorMessage =
            'Esta cuenta no corresponde a un acceso institucional.';
          return;
        }

        localStorage.setItem(
          'access_token',
          response.access_token
        );

        localStorage.setItem(
          'account_type',
          response.account_type
        );

        if (response.establishment_id !== null) {
          localStorage.setItem(
            'establishment_id',
            response.establishment_id.toString()
          );
        }

        localStorage.setItem(
          'display_name',
          response.display_name
        );

        console.log('Inicio de sesión correcto');

        this.router.navigate(['/patients']);
      },

      error: (error) => {

        this.loading = false;

        if (error.status === 401) {
          this.errorMessage =
            'Correo electrónico o contraseña incorrectos.';
        } else if (error.status === 403) {

          this.errorMessage =
            'La cuenta se encuentra inactiva. Contacte al administrador.';

        } else {

          this.errorMessage =
            'No se pudo conectar con el servidor.';
        }

        this.cdr.markForCheck();
      }
    });
  }
}