import { ChangeDetectorRef, Component, OnInit, OnDestroy } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import { Patient, PatientService } from '../../../core/services/patient';
import { Evaluation, EvaluationService } from '../../../core/services/evaluation';
import { PatientReport, ReportService } from '../../../core/services/report';

@Component({
  selector: 'app-patient-detail',
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './patient-detail.html',
  styleUrl: './patient-detail.css'
})
export class PatientDetail implements OnInit, OnDestroy {

  patient: Patient | null = null;

  activeTab = 'information';

  evaluations: Evaluation[] = [];

  evaluationsLoading = false;

  evaluationsError = '';

  continuingEvaluationId: number | null = null;

  patientReports: PatientReport[] = [];

  readonly reportPageSize = 7;
  readonly evaluationPageSize = 7;
  evaluationPage = 1;
  reportPage = 1;

  private getVisiblePages(
    currentPage: number,
    totalPages: number
  ): number[] {
    const first = Math.max(
      1,
      Math.min(currentPage - 2, totalPages - 4)
    );

    const last = Math.min(totalPages, first + 4);

    return Array.from(
      { length: last - first + 1 },
      (_, index) => first + index
    );
  }

  get totalEvaluationPages(): number {
    return Math.max(
      1,
      Math.ceil(this.evaluations.length / this.evaluationPageSize)
    );
  }

  get paginatedEvaluations(): Evaluation[] {
    const start = (this.evaluationPage - 1) * this.evaluationPageSize;
    return this.evaluations.slice(start, start + this.evaluationPageSize);
  }

  get evaluationPageNumbers(): number[] {
    return this.getVisiblePages(
      this.evaluationPage,
      this.totalEvaluationPages
    );
  }

  get evaluationShownStart(): number {
    return this.evaluations.length === 0
      ? 0
      : (this.evaluationPage - 1) * this.evaluationPageSize + 1;
  }

  get evaluationShownEnd(): number {
    return Math.min(
      this.evaluationPage * this.evaluationPageSize,
      this.evaluations.length
    );
  }

  changeEvaluationPage(page: number): void {
    if (
      !Number.isInteger(page) ||
      page < 1 ||
      page > this.totalEvaluationPages
    ) {
      return;
    }

    this.evaluationPage = page;
    this.cdr.markForCheck();
  }

  get totalReportPages(): number {
    return Math.max(
      1,
      Math.ceil(this.patientReports.length / this.reportPageSize)
    );
  }

  get paginatedReports(): PatientReport[] {
    const start = (this.reportPage - 1) * this.reportPageSize;
    return this.patientReports.slice(start, start + this.reportPageSize);
  }

  get reportPageNumbers(): number[] {
    return this.getVisiblePages(
      this.reportPage,
      this.totalReportPages
    );
  }

  get reportShownStart(): number {
    return this.patientReports.length === 0
      ? 0
      : (this.reportPage - 1) * this.reportPageSize + 1;
  }

  get reportShownEnd(): number {
    return Math.min(
      this.reportPage * this.reportPageSize,
      this.patientReports.length
    );
  }

  changeReportPage(page: number): void {
    if (
      !Number.isInteger(page) ||
      page < 1 ||
      page > this.totalReportPages
    ) {
      return;
    }

    this.reportPage = page;
    this.cdr.markForCheck();
  }


  reportsLoading = false;
  reportsError = '';
  reportGeneratingId: number | null = null;
  reportActionMessage = '';

  reportPreviewOpen = false;
  reportPreviewUrl: SafeResourceUrl | null = null;

  reportViewingId: number | null = null;
  reportDownloadingId: number | null = null;

  private reportObjectUrl: string | null = null;


  loading = true;

  errorMessage = '';

  showEditModal = false;

  editData = {
    nombres: '',
    apellidos: '',
    numero_documento: '',
    fecha_nacimiento: '',
    sexo: '',
    telefono: '',
    correo: '',
    direccion: ''
  };

  updating = false;
  updateError = '';

  displayName =
    localStorage.getItem('display_name') ?? 'Establecimiento';

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private patientService: PatientService,
    private evaluationService: EvaluationService,
    private reportService: ReportService,
    private sanitizer: DomSanitizer,
    private cdr: ChangeDetectorRef
  ) {
  }


  ngOnInit(): void {

    const patientId =
      Number(
        this.route.snapshot.paramMap.get('id')
      );

    if (!patientId) {
      this.errorMessage =
        'Identificador de paciente no válido.';

      this.loading = false;
      return;
    }

    this.loadPatient(patientId);
  }


  loadPatient(
    patientId: number
  ): void {

    this.loading = true;
    this.errorMessage = '';

    this.patientService
      .getPatientById(patientId)
      .subscribe({

        next: (response) => {

          this.patient = response;
          this.loading = false;

          if (history.state?.patientTab === 'evaluations') {
            this.selectTab('evaluations');
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

  calculateAge(birthDate: string): number {

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

  openEditModal(): void {

    if (!this.patient) {
      return;
    }

    this.editData = {
      nombres: this.patient.nombres,
      apellidos: this.patient.apellidos,
      numero_documento: this.patient.numero_documento,
      fecha_nacimiento: this.patient.fecha_nacimiento,
      sexo: this.patient.sexo,
      telefono: this.patient.telefono ?? '',
      correo: this.patient.correo ?? '',
      direccion: this.patient.direccion ?? ''
    };

    this.updateError = '';
    this.showEditModal = true;
  }

  closeEditModal(): void {
    this.showEditModal = false;
    this.updateError = '';
  }

  updatePatient(): void {

    if (!this.patient) {
      return;
    }

    this.updating = true;
    this.updateError = '';

    const data = {
      nombres: this.editData.nombres.trim(),
      apellidos: this.editData.apellidos.trim(),
      numero_documento:
        this.editData.numero_documento.trim(),
      fecha_nacimiento:
        this.editData.fecha_nacimiento,
      sexo: this.editData.sexo,
      telefono:
        this.editData.telefono.trim() || null,
      correo:
        this.editData.correo.trim() || null,
      direccion:
        this.editData.direccion.trim() || null
    };

    this.patientService
      .updatePatient(
        this.patient.id_paciente,
        data
      )
      .subscribe({

        next: (response) => {

          this.patient = response;

          this.updating = false;
          this.showEditModal = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.updating = false;

          if (error.status === 401) {

            this.logout();

          } else if (error.status === 409) {

            this.updateError =
              'Ya existe otro paciente con ese DNI.';

          } else if (error.status === 422) {

            this.updateError =
              'Verifica los datos ingresados.';

          } else if (error.status === 404) {

            this.updateError =
              'El paciente no fue encontrado.';

          } else {

            this.updateError =
              'No se pudieron actualizar los datos.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  selectTab(tab: string): void {

    if (
      tab === 'evaluations' &&
      this.activeTab !== 'evaluations'
    ) {
      this.evaluationPage = 1;
    }

    if (tab === 'reports' && this.activeTab !== 'reports') {
      this.reportPage = 1;
    }

    this.activeTab = tab;

    if (tab === 'reports') {
      this.loadReports();
    }


    if (
      tab === 'evaluations' &&
      this.evaluations.length === 0
    ) {
      this.loadEvaluations();
    }
  }



  loadReports(): void {

    if (!this.patient) {
      return;
    }

    this.reportsLoading = true;
    this.reportsError = '';

    this.reportService
      .getPatientReports(this.patient.id_paciente)
      .subscribe({

        next: (response) => {
          this.patientReports = [...response].sort(
            (a, b) => b.id_evaluacion - a.id_evaluacion
          );
          this.reportPage = Math.min(
            this.reportPage,
            this.totalReportPages
          );
          this.reportsLoading = false;
          this.cdr.markForCheck();
        },

        error: (error) => {
          this.reportsLoading = false;

          if (error.status === 401) {
            this.logout();
          } else {
            this.reportsError =
              'No se pudieron cargar los reportes del paciente.';
          }

          this.cdr.markForCheck();
        }
      });
  }


  generateReport(evaluationId: number): void {

    if (this.reportGeneratingId !== null) {
      return;
    }

    const report = this.patientReports.find(
      item => item.id_evaluacion === evaluationId
    );

    if (!report || report.tiene_reporte) {
      return;
    }

    this.reportGeneratingId = evaluationId;
    this.reportsError = '';
    this.reportActionMessage = '';

    this.reportService
      .generateReport(evaluationId)
      .subscribe({

        next: () => {
          this.reportGeneratingId = null;

          this.reportActionMessage =
            'Reporte PDF generado correctamente.';

          this.loadReports();
          this.cdr.markForCheck();
        },

        error: (error) => {
          this.reportGeneratingId = null;

          if (error.status === 401) {
            this.logout();

          } else if (error.status === 409) {
            this.reportsError =
              'El reporte ya existe o la evaluación ' +
              'todavía no está lista para generarlo.';

          } else if (error.status === 503) {
            this.reportsError =
              'No se pudo confirmar la generación. ' +
              'Consulta nuevamente el listado antes de reintentar.';

          } else {
            this.reportsError =
              'No se pudo generar el reporte PDF.';
          }

          this.cdr.markForCheck();
        }
      });
  }



  viewReport(evaluationId: number): void {

    if (this.reportViewingId !== null) {
      return;
    }

    this.reportViewingId = evaluationId;
    this.reportsError = '';

    this.reportService.viewReport(evaluationId).subscribe({

      next: (blob) => {
        this.reportViewingId = null;

        if (!blob.size) {
          this.reportsError = 'El archivo PDF está vacío.';
          this.cdr.markForCheck();
          return;
        }

        this.closeReportPreview();

        const pdfBlob = new Blob(
          [blob],
          { type: 'application/pdf' }
        );

        this.reportObjectUrl = URL.createObjectURL(pdfBlob);

        this.reportPreviewUrl =
          this.sanitizer.bypassSecurityTrustResourceUrl(
            this.reportObjectUrl + '#toolbar=0&navpanes=0'
          );

        this.reportPreviewOpen = true;
        this.cdr.markForCheck();
      },

      error: (error) => {
        this.reportViewingId = null;

        if (error.status === 401) {
          this.logout();
        } else {
          this.reportsError =
            'No se pudo visualizar el reporte PDF.';
        }

        this.cdr.markForCheck();
      }
    });
  }


  downloadReport(evaluationId: number): void {

    if (this.reportDownloadingId !== null) {
      return;
    }

    this.reportDownloadingId = evaluationId;
    this.reportsError = '';

    this.reportService.downloadReport(evaluationId).subscribe({

      next: (blob) => {
        this.reportDownloadingId = null;

        if (!blob.size) {
          this.reportsError = 'El archivo PDF está vacío.';
          this.cdr.markForCheck();
          return;
        }

        const url = URL.createObjectURL(
          new Blob([blob], { type: 'application/pdf' })
        );

        const link = document.createElement('a');
        link.href = url;
        link.download = `RetiScan_reporte_${evaluationId}.pdf`;

        document.body.appendChild(link);
        link.click();
        link.remove();

        setTimeout(() => {
          URL.revokeObjectURL(url);
        }, 60000);

        this.cdr.markForCheck();
      },

      error: (error) => {
        this.reportDownloadingId = null;

        if (error.status === 401) {
          this.logout();
        } else {
          this.reportsError =
            'No se pudo descargar el reporte PDF.';
        }

        this.cdr.markForCheck();
      }
    });
  }


  closeReportPreview(): void {

    this.reportPreviewOpen = false;
    this.reportPreviewUrl = null;

    if (this.reportObjectUrl !== null) {
      URL.revokeObjectURL(this.reportObjectUrl);
      this.reportObjectUrl = null;
    }
  }


  ngOnDestroy(): void {
    this.closeReportPreview();
  }


  loadEvaluations(): void {

    if (!this.patient) {
      return;
    }

    this.evaluationsLoading = true;
    this.evaluationsError = '';

    this.evaluationService
      .getPatientEvaluations(
        this.patient.id_paciente
      )
      .subscribe({

        next: (response) => {

          this.evaluations = [...response].sort((a, b) => {
            const dateA = Date.parse(a.fecha_creacion) || 0;
            const dateB = Date.parse(b.fecha_creacion) || 0;

            return (
              dateB - dateA ||
              b.id_evaluacion - a.id_evaluacion
            );
          });
          this.evaluationPage = Math.min(
            this.evaluationPage,
            this.totalEvaluationPages
          );
          this.evaluationsLoading = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          this.evaluationsLoading = false;

          if (error.status === 401) {

            this.logout();

          } else {

            this.evaluationsError =
              'No se pudieron cargar las evaluaciones.';
          }

          this.cdr.markForCheck();
        }
      });
  }

  getEvaluationResultState(
    evaluation: Evaluation
  ): 'pending' | 'incomplete' | 'clear' | 'high' | 'medium' | 'neutral' {

    const rd = evaluation.retinopatia_diabetica;
    const glaucoma = evaluation.glaucoma;

    if (!rd && !glaucoma) {
      return 'pending';
    }

    if (!rd || !glaucoma) {
      return 'incomplete';
    }

    const prioridad =
      (evaluation.prioridad_sugerida ?? '').trim().toUpperCase();

    const sinIndicios =
      rd.resultado.trim() === 'Sin indicios de Retinopatía Diabética' &&
      glaucoma.resultado.trim() === 'Bajo riesgo de Glaucoma';

    if (
      sinIndicios &&
      (prioridad === '' || prioridad === 'BAJA')
    ) {
      return 'clear';
    }

    if (prioridad === 'ALTA') {
      return 'high';
    }

    if (prioridad === 'MEDIA') {
      return 'medium';
    }

    return 'neutral';
  }

  formatHistoryConfidence(
    confianza: number | null | undefined
  ): string {

    if (confianza == null || !Number.isFinite(confianza)) {
      return 'No disponible';
    }

    return `${(confianza * 100).toFixed(2)} %`;
  }


  viewEvaluation(evaluationId: number): void {
    this.router.navigate([
      '/evaluations',
      evaluationId,
      'detail'
    ]);
  }

  continueEvaluation(evaluation: Evaluation): void {

    if (
      evaluation.estado !== 'PENDIENTE' ||
      this.continuingEvaluationId !== null
    ) {
      return;
    }

    this.continuingEvaluationId = evaluation.id_evaluacion;
    this.evaluationsError = '';

    this.evaluationService
      .getStoredEvaluationResults(evaluation.id_evaluacion)
      .subscribe({

        next: () => {
          this.continuingEvaluationId = null;

          // Ya existen resultados IA completos.
          // Corresponde revisar y finalizar.
          this.router.navigate([
            '/evaluations',
            evaluation.id_evaluacion,
            'results'
          ]);
        },

        error: (error) => {
          this.continuingEvaluationId = null;

          if (error.status === 401) {
            this.logout();
            return;
          }

          if (error.status === 409) {

            // No existen resultados completos.
            // Se retomara la etapa de retinografia.
            this.router.navigate([
              '/evaluations',
              evaluation.id_evaluacion,
              'retinography'
            ]);

            return;
          }

          if (error.status === 404) {
            this.evaluationsError =
              'La evaluación no fue encontrada.';
          } else {
            this.evaluationsError =
              'No se pudo comprobar el estado de la evaluación. Inténtalo nuevamente.';
          }

          this.cdr.markForCheck();
        }
      });
  }


  newEvaluation(): void {

    if (!this.patient) {
      return;
    }

    this.router.navigate([
      '/patients',
      this.patient.id_paciente,
      'evaluations',
      'new'
    ]);
  }

  goBack(): void {
    this.router.navigate(['/patients']);
  }

  goHome(): void {
    this.router.navigate(['/home']);
  }

  goToEvaluations(): void {
    this.router.navigate(['/evaluations']);
  }

  goToReports(): void {
    this.router.navigate(['/reports']);
  }

  logout(): void {

    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }
}
