import { ChangeDetectorRef, Component } from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { PatientService } from '../../../core/services/patient';


@Component({
  selector: 'app-patient-create',
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './patient-create.html',
  styleUrl: './patient-create.css'
})
export class PatientCreate {

  nombres = '';
  apellidos = '';
  numeroDocumento = '';
  fechaNacimiento = '';
  sexo = '';

  telefono = '';
  correo = '';
  direccion = '';

  saving = false;
  errorMessage = '';

  displayName =
    localStorage.getItem('display_name') ?? 'Establecimiento';


  constructor(
    private router: Router,
    private patientService: PatientService,
    private cdr: ChangeDetectorRef
  ) {
  }


  registerPatient(): void {

    if (
      !this.nombres.trim() ||
      !this.apellidos.trim() ||
      !this.numeroDocumento.trim() ||
      !this.fechaNacimiento ||
      !this.sexo
    ) {
      this.errorMessage =
        'Complete todos los campos obligatorios.';

      return;
    }

    this.saving = true;
    this.errorMessage = '';

    this.patientService
      .createPatient({
        numero_documento:
          this.numeroDocumento.trim(),

        nombres:
          this.nombres.trim(),

        apellidos:
          this.apellidos.trim(),

        fecha_nacimiento:
          this.fechaNacimiento,

        sexo:
          this.sexo,

        telefono:
          this.telefono.trim() || null,

        correo:
          this.correo.trim() || null,

        direccion:
          this.direccion.trim() || null
      })
      .subscribe({

        next: (response) => {

          this.saving = false;

          this.router.navigate([
            '/patients',
            response.id_paciente
          ]);
        },

        error: (error) => {

          this.saving = false;

          if (error.status === 401) {

            this.logout();

          } else if (error.status === 409) {

            this.errorMessage =
              'El paciente ya se encuentra registrado en el establecimiento.';

          } else if (error.status === 422) {

            this.errorMessage =
              'Verifique los datos ingresados.';

          } else {

            this.errorMessage =
              'No se pudo registrar el paciente.';
          }

          this.cdr.markForCheck();
        }
      });
  }


  cancel(): void {
    this.router.navigate(['/patients']);
  }


  logout(): void {

    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }
}
