import {
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import {
  AIEvaluationResultsResponse,
  EvaluationDetail as EvaluationDetailData,
  EvaluationService
} from '../../../core/services/evaluation';

@Component({
  selector: 'app-evaluation-detail',
  imports: [CommonModule, FormsModule],
  templateUrl: './evaluation-detail.html',
  styleUrls: [
    '../evaluation-results/evaluation-results.css',
    './evaluation-detail.css'
  ]
})
export class EvaluationDetail implements OnInit, OnDestroy {

  evaluationId = 0;

  evaluation: EvaluationDetailData | null = null;
  analysis: AIEvaluationResultsResponse | null = null;

  prioritySuggested: string | null = null;

  get priorityStyleClass(): string {
    switch (this.prioritySuggested?.trim().toUpperCase()) {
      case 'BAJA':
        return 'priority-level--baja';
      case 'MEDIA':
        return 'priority-level--media';
      case 'ALTA':
        return 'priority-level--alta';
      default:
        return 'priority-level--neutral';
    }
  }

  get priorityRecommendation(): string {
    switch (this.prioritySuggested?.trim().toUpperCase()) {
      case 'BAJA':
        return 'Se sugiere continuar con el seguimiento oftalmológico habitual y revisar los hallazgos según el criterio del especialista.';

      case 'MEDIA':
        return 'Se sugiere una valoración oftalmológica oportuna para revisar los hallazgos y considerar una evaluación complementaria.';

      case 'ALTA':
        return 'Se sugiere una revisión oftalmológica prioritaria para valorar los hallazgos y definir las acciones pertinentes.';

      default:
        return 'La prioridad debe revisarse con el médico oftalmólogo.';
    }
  }

  loadingEvaluation = false;
  loadingResults = false;
  loadingRetinography = false;

  errorMessage = '';
  resultsPending = false;
  retinographyError = '';

  retinographyUrl: string | null = null;

  observationText = '';
  savingObservation = false;
  observationSuccess = '';
  observationError = '';

  displayName =
    localStorage.getItem('display_name') ?? 'Establecimiento';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private evaluationService: EvaluationService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.evaluationId = Number(
      this.route.snapshot.paramMap.get('evaluationId')
    );

    if (
      !Number.isInteger(this.evaluationId) ||
      this.evaluationId <= 0
    ) {
      this.errorMessage = 'Identificador de evaluación no válido.';
      return;
    }

    this.loadEvaluation();
    this.loadResults();
    this.loadRetinographyImage();
  }

  get canEditObservation(): boolean {
    return (
      this.evaluation?.estado === 'FINALIZADA' &&
      this.analysis !== null
    );
  }

  loadEvaluation(): void {
    this.loadingEvaluation = true;

    this.evaluationService
      .getEvaluationDetail(this.evaluationId)
      .subscribe({
        next: (response) => {
          this.evaluation = response;
          this.observationText = response.observacion_medica ?? '';
          this.loadingEvaluation = false;
          this.cdr.markForCheck();
        },
        error: (error) => {
          this.loadingEvaluation = false;

          if (error.status === 401) {
            this.logout();
            return;
          }

          this.errorMessage =
            'No se pudo obtener la información de la evaluación.';

          this.cdr.markForCheck();
        }
      });
  }

  loadResults(): void {
    this.loadingResults = true;

    this.evaluationService
      .getStoredEvaluationResults(this.evaluationId)
      .subscribe({
        next: (response) => {
          this.analysis = response;
          this.prioritySuggested =
            response.prioridad_sugerida;

          this.loadingResults = false;
          this.cdr.markForCheck();
        },
        error: (error) => {
          this.loadingResults = false;
          this.analysis = null;

          if (error.status === 401) {
            this.logout();
            return;
          }

          if (error.status === 409) {
            this.resultsPending = true;
            this.errorMessage = '';
          } else {
            this.errorMessage =
              'No se pudieron recuperar los resultados de la evaluación.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  loadRetinographyImage(): void {
    this.loadingRetinography = true;
    this.retinographyError = '';

    this.evaluationService
      .getRetinographyImage(this.evaluationId)
      .subscribe({
        next: (imageBlob: Blob) => {
          if (this.retinographyUrl) {
            URL.revokeObjectURL(this.retinographyUrl);
          }

          this.retinographyUrl =
            URL.createObjectURL(imageBlob);

          this.loadingRetinography = false;
          this.cdr.markForCheck();
        },
        error: (error) => {
          this.loadingRetinography = false;

          if (error.status === 401) {
            this.logout();
            return;
          }

          if (error.status === 404) {
            this.retinographyError =
              'Esta evaluación todavía no tiene una retinografía registrada.';
          } else {
            this.retinographyError =
              'No se pudo cargar la retinografía evaluada.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  saveObservation(): void {
    this.observationSuccess = '';
    this.observationError = '';

    if (!this.canEditObservation || this.savingObservation) {
      this.observationError =
        'Solo se pueden modificar observaciones de evaluaciones finalizadas con resultados disponibles.';
      return;
    }

    const observation = this.observationText.trim();

    if (!observation) {
      this.observationError =
        'Escribe una observación médica antes de guardar.';
      return;
    }

    if (observation.length > 1000) {
      this.observationError =
        'La observación no puede superar los 1000 caracteres.';
      return;
    }

    this.savingObservation = true;

    this.evaluationService
      .updateMedicalObservation(this.evaluationId, observation)
      .subscribe({
        next: (response) => {
          this.savingObservation = false;
          this.observationText = response.observacion_medica;

          if (this.evaluation) {
            this.evaluation = {
              ...this.evaluation,
              observacion_medica: response.observacion_medica
            };
          }

          this.observationSuccess =
            'Observación médica guardada correctamente.';

          this.cdr.markForCheck();
        },
        error: (error) => {
          this.savingObservation = false;

          if (error.status === 401) {
            this.logout();
            return;
          }

          if (error.status === 409) {
            this.observationError =
              'La observación no puede modificarse en el estado actual de la evaluación.';
          } else if (error.status === 422) {
            this.observationError =
              'Verifica el contenido de la observación médica.';
          } else {
            this.observationError =
              'No se pudo guardar la observación médica.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  calculateAge(birthDate: string): number {
    const [year, month, day] = birthDate
      .slice(0, 10)
      .split('-')
      .map(Number);

    const today = new Date();
    let age = today.getFullYear() - year;

    if (
      today.getMonth() + 1 < month ||
      (
        today.getMonth() + 1 === month &&
        today.getDate() < day
      )
    ) {
      age--;
    }

    return age;
  }

  goToPatient(): void {
    if (!this.evaluation) {
      return;
    }

    this.router.navigate([
      '/patients',
      this.evaluation.id_paciente
    ]);
  }

  ngOnDestroy(): void {
    if (this.retinographyUrl) {
      URL.revokeObjectURL(this.retinographyUrl);
    }
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }
}
