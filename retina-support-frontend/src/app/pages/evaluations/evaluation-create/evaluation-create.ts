import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable } from 'rxjs';
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
  editEvaluationId: number | null = null;
  editReady = false;
  eyeLocked = false;

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

    const editParam = this.route.snapshot.paramMap.get(
      'evaluationId'
    );

    if (editParam !== null) {
      this.editEvaluationId = Number(editParam);

      if (
        !Number.isInteger(this.editEvaluationId) ||
        this.editEvaluationId <= 0
      ) {
        this.errorMessage = 'Identificador de evaluación no válido.';
        this.loading = false;
        return;
      }
    }

    if (!this.patientId) {

      this.errorMessage =
        'Identificador de paciente no válido.';

      this.loading = false;

      return;
    }

    this.loadPatient();
  }


  private loadExistingEvaluation(): void {
    const id = this.editEvaluationId;

    if (id === null) {
      return;
    }

    this.evaluationService.getEvaluationDetail(id).subscribe({
      next: (evaluation) => {
        if (evaluation.id_paciente !== this.patientId) {
          this.errorMessage =
            'La evaluación no corresponde a este paciente.';
          this.loading = false;
          this.cdr.markForCheck();
          return;
        }

        if (evaluation.estado !== 'PENDIENTE') {
          this.errorMessage =
            'Solo se pueden editar evaluaciones pendientes.';
          this.loading = false;
          this.cdr.markForCheck();
          return;
        }

        this.fechaEvaluacion =
          evaluation.fecha_evaluacion.slice(0, 10);
        this.ojoEvaluado = evaluation.ojo_evaluado;
        this.medicoResponsable = evaluation.medico_responsable;

        this.evaluationService.getRetinographyResume(id)
          .subscribe({
            next: (metadata) => {
              if (metadata.estado !== 'CARGADA') {
                this.editReady = false;
                this.errorMessage =
                  'La retinografía ya no permite editar estos datos.';
              } else {
                this.eyeLocked = true;
                this.editReady = true;
              }

              this.loading = false;
              this.cdr.markForCheck();
            },
            error: (error) => {
              if (error.status === 401) {
                this.logout();
                return;
              }

              if (error.status === 404) {
                this.eyeLocked = false;
                this.editReady = true;
              } else {
                this.editReady = false;
                this.errorMessage =
                  'No se pudo verificar la retinografía existente.';
              }

              this.loading = false;
              this.cdr.markForCheck();
            }
          });
      },
      error: (error) => {
        if (error.status === 401) {
          this.logout();
          return;
        }

        this.errorMessage = error.status === 404
          ? 'La evaluación no fue encontrada.'
          : 'No se pudieron recuperar los datos de la evaluación.';

        this.loading = false;
        this.cdr.markForCheck();
      }
    });
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

          if (this.editEvaluationId !== null) {
            this.loadExistingEvaluation();
          } else {
            this.loading = false;
          }

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

    if (
      !this.patient ||
      this.saving ||
      (this.editEvaluationId !== null && !this.editReady)
    ) {
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

    const data = {
      fecha_evaluacion: this.fechaEvaluacion,
      ojo_evaluado: this.ojoEvaluado,
      medico_responsable: this.medicoResponsable.trim()
    };

    const request: Observable<{ id_evaluacion: number }> =
      this.editEvaluationId !== null
        ? this.evaluationService.updateEvaluation(
          this.editEvaluationId, data
        )
        : this.evaluationService.createEvaluation(
          this.patientId, data
        );

    request.subscribe({

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

          this.errorMessage = this.editEvaluationId !== null
            ? 'La evaluación no fue encontrada.'
            : 'El paciente no fue encontrado.';

        } else if (error.status === 409) {

          const detail = error.error?.detail;

          const knownMessages = [
            'Existen varios registros con el mismo nombre de médico. Verifique su identidad.',
            'El médico está inactivo en el establecimiento.',
            'No se puede cambiar el ojo evaluado porque ya existe una retinografía cargada.',
            'La evaluación ya inició el análisis de IA o no se encuentra pendiente.'
          ];

          this.errorMessage =
            typeof detail === 'string' &&
              knownMessages.includes(detail)
              ? detail
              : 'No se pudo registrar la evaluación por un conflicto de datos.';

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
    this.router.navigate(
      ['/patients', this.patientId],
      { state: { patientTab: 'evaluations' } }
    );
  }


  goBack(): void {
    this.router.navigate(
      ['/patients', this.patientId],
      { state: { patientTab: 'evaluations' } }
    );
  }

  goHome(): void {
    this.router.navigate(['/home']);
  }

  logout(): void {

    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }
}
