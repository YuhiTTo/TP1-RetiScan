import { ChangeDetectorRef, Component, OnInit } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

import { Patient, PatientService } from '../../../core/services/patient';
import { Evaluation, EvaluationService } from '../../../core/services/evaluation';

@Component({
  selector: 'app-patient-detail',
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './patient-detail.html',
  styleUrl: './patient-detail.css'
})
export class PatientDetail implements OnInit {

  patient: Patient | null = null;

  activeTab = 'information';

  evaluations: Evaluation[] = [];

  evaluationsLoading = false;

  evaluationsError = '';

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

    this.activeTab = tab;

    if (
      tab === 'evaluations' &&
      this.evaluations.length === 0
    ) {
      this.loadEvaluations();
    }
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

          this.evaluations = response;
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

  logout(): void {

    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }
}
