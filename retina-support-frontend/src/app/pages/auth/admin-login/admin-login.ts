import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../../core/services/auth';


@Component({
  selector: 'app-admin-login',
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './admin-login.html',
  styleUrl: './admin-login.css'
})
export class AdminLogin {

  email = '';
  password = '';

  showPassword = false;

  loading = false;
  errorMessage = '';

  constructor(
    private authService: AuthService,
    private router: Router
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

        if (response.account_type !== 'ADMIN') {

          this.errorMessage =
            'Esta cuenta no corresponde a un acceso administrativo.';

          return;
        }

        sessionStorage.setItem(
          'access_token',
          response.access_token
        );

        sessionStorage.setItem(
          'account_type',
          response.account_type
        );

        sessionStorage.setItem(
          'display_name',
          response.display_name
        );

        this.router.navigate(['/admin']);
      },

      error: (error) => {

        this.loading = false;

        if (error.status === 401) {

          this.errorMessage =
            'Correo electrónico o contraseña incorrectos.';

        } else {

          this.errorMessage =
            'No se pudo conectar con el servidor.';
        }
      }
    });
  }
}