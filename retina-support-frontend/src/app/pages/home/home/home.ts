import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import {
  DashboardService,
  DashboardSummary
} from '../../../core/services/dashboard';


@Component({
  selector: 'app-home',
  imports: [CommonModule],
  templateUrl: './home.html',
  styleUrl: './home.css'
})
export class Home implements OnInit {

  displayName =
    localStorage.getItem('display_name') ?? 'Establecimiento';

  // Datos del Dashboard
  dashboard: DashboardSummary | null = null;

  // Estados de carga
  dashboardLoading = true;
  dashboardError = false;

  constructor(
    private router: Router,
    private dashboardService: DashboardService,
    private cdr: ChangeDetectorRef
  ) { }

  ngOnInit(): void {
    console.log('[Dashboard] ngOnInit ejecutado');
    this.loadDashboard();
  }

  // Obtener estadísticas del backend
  loadDashboard(): void {

    this.dashboardLoading = true;
    this.dashboardError = false;


    this.dashboardService.getSummary().subscribe({

      next: (response) => {

        console.log('[Dashboard] Respuesta recibida:', response);

        this.dashboard = response;
        this.dashboardLoading = false;
        this.dashboardError = false;

        // Notificar a Angular que debe actualizar la vista
        this.cdr.markForCheck();

        console.log('[Dashboard] Vista actualizada');
      },

      error: (error) => {

        console.error('[Dashboard] Error:', error);

        this.dashboardError = true;
        this.dashboardLoading = false;

        // Actualizar la vista también cuando ocurre un error
        this.cdr.markForCheck();
      }

    });
  }

  // Navegación
  goToHome(): void {
    this.router.navigate(['/home']);
  }

  goToPatients(): void {
    this.router.navigate(['/patients']);
  }

  registerPatient(): void {
    this.router.navigate(['/patients/new']);
  }

  searchPatient(): void {
    this.router.navigate(['/patients']);
  }

  viewHistory(): void {
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