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