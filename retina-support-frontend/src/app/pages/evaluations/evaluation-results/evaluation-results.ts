import { ChangeDetectorRef, Component, OnInit, OnDestroy } from '@angular/core';

import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import { AIEvaluationResultsResponse, AIAnalysisResponse, EvaluationDetail, EvaluationService } from '../../../core/services/evaluation';

@Component({
  selector: 'app-evaluation-results',
  imports: [CommonModule],
  templateUrl: './evaluation-results.html',
  styleUrl: './evaluation-results.css'
})
export class EvaluationResults implements OnInit, OnDestroy {

  evaluationId = 0;

  analysis: AIAnalysisResponse | AIEvaluationResultsResponse | null = null;
  loadingResults = false;
  prioritySuggested: string | null = null;
  evaluation: EvaluationDetail | null = null;
  retinographyUrl: string | null = null;
  loadingRetinography = false;
  retinographyError = '';

  loadingEvaluation = false;
  errorMessage = '';

  displayName =
    localStorage.getItem('display_name') ?? 'Establecimiento';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private evaluationService: EvaluationService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {

    this.evaluationId = Number(
      this.route.snapshot.paramMap.get('evaluationId')
    );

    if (
      !Number.isInteger(this.evaluationId) ||
      this.evaluationId <= 0
    ) {
      this.errorMessage =
        'Identificador de evaluación no válido.';
      return;
    }

    this.analysis = this.evaluationService
      .getAnalysisResult(this.evaluationId);

    this.prioritySuggested =
      this.analysis?.prioridad_sugerida ?? null;

    this.loadStoredResults();
    this.loadEvaluation();
    this.loadRetinographyImage();
  }

  loadStoredResults(): void {

    this.loadingResults = true;

    this.evaluationService
      .getStoredEvaluationResults(this.evaluationId)
      .subscribe({

        next: (results) => {
          this.analysis = results;
          this.prioritySuggested = results.prioridad_sugerida;
          this.errorMessage = '';
          this.loadingResults = false;
          this.cdr.markForCheck();
        },

        error: (error) => {
          this.loadingResults = false;

          if (error.status === 401) {
            this.router.navigate(['/login']);
            return;
          }

          if (error.status === 409 && this.analysis) {
            this.cdr.markForCheck();
            return;
          }

          this.analysis = null;
          this.prioritySuggested = null;

          if (error.status === 409) {
            this.errorMessage =
              'Los resultados todavía no están disponibles.';
          } else if (error.status === 404) {
            this.errorMessage =
              'La evaluación retiniana no fue encontrada.';
          } else {
            this.errorMessage =
              'No se pudieron recuperar los resultados.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  loadEvaluation(): void {

    this.loadingEvaluation = true;

    this.evaluationService
      .getEvaluationDetail(this.evaluationId)
      .subscribe({

        next: (response) => {

          this.evaluation = response;
          this.loadingEvaluation = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.loadingEvaluation = false;

          if (error.status === 401) {
            this.router.navigate(['/login']);
            return;
          }

          if (!this.errorMessage) {
            this.errorMessage =
              'No se pudo obtener la información de la evaluación.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  goBack(): void {

    this.router.navigate([
      '/evaluations',
      this.evaluationId,
      'retinography'
    ]);
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

        error: () => {

          this.loadingRetinography = false;

          this.retinographyError =
            'No se pudo cargar la retinografía evaluada.';

          this.cdr.markForCheck();
        }

      });
  }

  ngOnDestroy(): void {

    if (this.retinographyUrl) {
      URL.revokeObjectURL(this.retinographyUrl);
    }

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

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }

}
