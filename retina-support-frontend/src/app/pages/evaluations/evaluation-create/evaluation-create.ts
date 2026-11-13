import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { Patient, PatientService } from '../../../core/services/patient';
import { EvaluationService } from '../../../core/services/evaluation';


@Component({
  selector: 'app-evaluation-create',
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './evaluation-create.html',
  styleUrl: './evaluation-create.css'
})
export class EvaluationCreate implements OnInit {

  patient: Patient | null = null;

  patientId = 0;

  loading = true;
  saving = false;

  errorMessage = '';

  displayName =
    localStorage.getItem('display_name') ?? 'Establecimiento';

  fechaEvaluacion = this.getTodayLocal();

  ojoEvaluado = 'OD';

  medicoResponsable = '';


  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private patientService: PatientService,
    private evaluationService: EvaluationService,
    private cdr: ChangeDetectorRef
  ) {
  }


  ngOnInit(): void {

    this.patientId = Number(
      this.route.snapshot.paramMap.get('id')
    );

    if (!this.patientId) {

      this.errorMessage =
        'Identificador de paciente no válido.';

      this.loading = false;

      return;
    }

    this.loadPatient();
  }


  private getTodayLocal(): string {

    const today = new Date();

    const year =
      today.getFullYear();

    const month =
      String(today.getMonth() + 1)
        .padStart(2, '0');

    const day =
      String(today.getDate())
        .padStart(2, '0');

    return `${year}-${month}-${day}`;
  }


  loadPatient(): void {

    this.loading = true;
    this.errorMessage = '';

    this.patientService
      .getPatientById(this.patientId)
      .subscribe({

        next: (response) => {

          this.patient = response;
          this.loading = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.loading = false;

          if (error.status === 401) {

            this.logout();

          } else if (error.status === 404) {

            this.errorMessage =
              'El paciente no fue encontrado.';

          } else {

            this.errorMessage =
              'No se pudo cargar la información del paciente.';
          }

          this.cdr.markForCheck();
        }
      });
  }


  calculateAge(
    birthDate: string
  ): number {

    const birth = new Date(birthDate);
    const today = new Date();

    let age =
      today.getFullYear() -
      birth.getFullYear();

    const monthDifference =
      today.getMonth() -
      birth.getMonth();

    if (
      monthDifference < 0 ||
      (
        monthDifference === 0 &&
        today.getDate() < birth.getDate()
      )
    ) {
      age--;
    }

    return age;
  }


  continueWithRetinography(): void {

    if (!this.patient) {
      return;
    }

    if (!this.fechaEvaluacion) {

      this.errorMessage =
        'Seleccione la fecha de evaluación.';

      return;
    }

    if (
      this.ojoEvaluado !== 'OD' &&
      this.ojoEvaluado !== 'OI'
    ) {

      this.errorMessage =
        'Seleccione el ojo evaluado.';

      return;
    }

    if (!this.medicoResponsable.trim()) {

      this.errorMessage =
        'Ingrese el médico responsable.';

      return;
    }

    this.saving = true;
    this.errorMessage = '';

    this.evaluationService
      .createEvaluation(
        this.patientId,
        {
          fecha_evaluacion:
            this.fechaEvaluacion,

          ojo_evaluado:
            this.ojoEvaluado,

          medico_responsable:
            this.medicoResponsable.trim()
        }
      )
      .subscribe({

        next: (response) => {

          this.saving = false;

          this.router.navigate([
            '/evaluations',
            response.id_evaluacion,
            'retinography'
          ]);
        },

        error: (error) => {

          this.saving = false;

          if (error.status === 401) {

            this.logout();

          } else if (error.status === 404) {

            this.errorMessage =
              'El paciente o médico responsable no fue encontrado.';

          } else if (error.status === 422) {

            this.errorMessage =
              'Verifique los datos de la evaluación.';

          } else {

            this.errorMessage =
              'No se pudo registrar la evaluación.';
          }

          this.cdr.markForCheck();
        }
      });
  }


  cancel(): void {

    this.router.navigate([
      '/patients',
      this.patientId
    ]);
  }


  goBack(): void {

    this.router.navigate([
      '/patients',
      this.patientId
    ]);
  }


  logout(): void {

    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }
}
