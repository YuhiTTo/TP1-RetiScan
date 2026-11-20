import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
  Patient,
  PatientService
} from '../../../core/services/patient';


@Component({
  selector: 'app-patient-list',
  imports: [
    CommonModule,
    FormsModule
  ],
  templateUrl: './patient-list.html',
  styleUrl: './patient-list.css'
})
export class PatientList implements OnInit {

  searchTerm = '';

  patients: Patient[] = [];

  readonly pageSize = 8;
  currentPage = 1;

  get totalPages(): number {
    return Math.max(1, Math.ceil(this.patients.length / this.pageSize));
  }

  get paginatedPatients(): Patient[] {
    const start = (this.currentPage - 1) * this.pageSize;
    return this.patients.slice(start, start + this.pageSize);
  }

  get pageNumbers(): number[] {
    const first = Math.max(
      1,
      Math.min(this.currentPage - 2, this.totalPages - 4)
    );

    const last = Math.min(this.totalPages, first + 4);

    return Array.from(
      { length: last - first + 1 },
      (_, index) => first + index
    );
  }

  get shownStart(): number {
    return this.patients.length === 0
      ? 0
      : (this.currentPage - 1) * this.pageSize + 1;
  }

  get shownEnd(): number {
    return Math.min(
      this.currentPage * this.pageSize,
      this.patients.length
    );
  }

  changePage(page: number): void {
    if (
      !Number.isInteger(page) ||
      page < 1 ||
      page > this.totalPages
    ) {
      return;
    }

    this.currentPage = page;
    this.cdr.markForCheck();
  }


  loading = false;

  errorMessage = '';

  displayName =
    localStorage.getItem('display_name') ?? 'Establecimiento';

  constructor(
    private router: Router,
    private patientService: PatientService,
    private cdr: ChangeDetectorRef
  ) {
  }


  ngOnInit(): void {
    this.loadPatients();
  }


  loadPatients(): void {

    this.currentPage = 1;
    this.loading = true;
    this.errorMessage = '';

    this.patientService
      .getPatients(this.searchTerm)
      .subscribe({

        next: (response) => {

          console.log('Pacientes recibidos:', response);

          this.patients = response;
          this.loading = false;

          this.cdr.markForCheck();
        },

        error: (error) => {

          console.error('Error al cargar pacientes:', error);

          this.loading = false;

          if (error.status === 401) {
            this.logout();
          } else {
            this.errorMessage =
              'No se pudieron cargar los pacientes.';

            this.cdr.markForCheck();
          }
        }
      });
  }

  goToHome(): void {
    this.router.navigate(['/home']);
  }

  goToEvaluations(): void {
    this.router.navigate(['/evaluations']);
  }

  registerPatient(): void {
    this.router.navigate(['/patients/new']);
  }

  searchPatients(): void {
    this.loadPatients();
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

  viewPatient(patientId: number): void {
    this.router.navigate(['/patients', patientId]);
  }

  logout(): void {

    localStorage.removeItem('access_token');
    localStorage.removeItem('account_type');
    localStorage.removeItem('establishment_id');
    localStorage.removeItem('display_name');

    this.router.navigate(['/login']);
  }
}