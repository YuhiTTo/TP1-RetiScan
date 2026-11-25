import {
  ChangeDetectorRef,
  Component,
  OnInit
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
  Router,
  RouterLink,
  RouterLinkActive
} from '@angular/router';

import {
  AdminEvaluation,
  AdminEvaluationsPage,
  AdminEvaluationsSummary,
  AdminEvaluationsService
} from '../../../core/services/admin-evaluations';

import {
  AdminEstablishmentService,
  Establishment
} from '../../../core/services/admin-establishment';

@Component({
  selector: 'app-admin-evaluations',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    RouterLinkActive
  ],
  templateUrl: './admin-evaluations.html',
  styleUrls: [
    '../admin-dashboard/admin-dashboard.css',
    './admin-evaluations.css'
  ]
})
export class AdminEvaluations implements OnInit {

  displayName =
    sessionStorage.getItem('display_name') ?? 'Administrador';

  evaluations: AdminEvaluation[] = [];
  establishments: Establishment[] = [];
  summary: AdminEvaluationsSummary | null = null;

  loading = true;
  summaryLoading = true;
  errorMessage = '';
  summaryError = '';
  filterError = '';

  searchId = '';
  selectedEstablishment = '';
  selectedStatus = '';

  private appliedId: number | undefined;
  private appliedEstablishment: number | undefined;
  private appliedStatus:
    'PENDIENTE' | 'FINALIZADA' | undefined;

  page = 1;
  readonly pageSize = 8;
  total = 0;
  totalPages = 0;

  private requestId = 0;

  constructor(
    private service: AdminEvaluationsService,
    private establishmentService: AdminEstablishmentService,
    private cdr: ChangeDetectorRef,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadSummary();
    this.loadEstablishments();
    this.loadEvaluations();
  }

  loadSummary(): void {
    this.summaryLoading = true;
    this.summaryError = '';

    this.service.summary().subscribe({
      next: result => {
        this.summary = result;
        this.summaryLoading = false;
        this.cdr.markForCheck();
      },
      error: (error) => {
        if (error.status === 401 || error.status === 403) {
          this.logout();
          return;
        }

        this.summaryLoading = false;
        this.summaryError =
          'No se pudieron cargar los indicadores.';
        this.cdr.markForCheck();
      }
    });
  }

  loadEstablishments(): void {
    this.establishmentService.getEstablishments()
      .subscribe({
        next: result => {
          this.establishments = result;
          this.cdr.markForCheck();
        },
        error: (error) => {
          if (error.status === 401 || error.status === 403) {
            this.logout();
            return;
          }

          this.filterError =
            'No se pudo cargar la lista de establecimientos.';
          this.cdr.markForCheck();
        }
      });
  }

  loadEvaluations(): void {
    const currentRequest = ++this.requestId;

    this.loading = true;
    this.errorMessage = '';

    this.service.list({
      page: this.page,
      page_size: this.pageSize,
      evaluation_id: this.appliedId,
      establishment_id: this.appliedEstablishment,
      estado: this.appliedStatus
    }).subscribe({
      next: (response: AdminEvaluationsPage) => {
        if (currentRequest !== this.requestId) {
          return;
        }

        this.evaluations = response.items;
        this.total = response.total;
        this.totalPages = response.total_pages;
        this.page = response.page;
        this.loading = false;
        this.cdr.markForCheck();
      },
      error: (error) => {
        if (currentRequest !== this.requestId) {
          return;
        }

        if (error.status === 401 || error.status === 403) {
          this.logout();
          return;
        }

        this.evaluations = [];
        this.total = 0;
        this.totalPages = 0;
        this.loading = false;

        this.errorMessage =
          error.status === 403
            ? 'No tienes permisos de administrador.'
            : error.status === 401
              ? 'Tu sesión ha expirado. Inicia sesión nuevamente.'
              : 'No se pudieron cargar las evaluaciones.';

        this.cdr.markForCheck();
      }
    });
  }

  applyFilters(): void {
    this.filterError = '';

    const raw = this.searchId.trim();

    if (raw && !/^[1-9][0-9]*$/.test(raw)) {
      this.filterError =
        'Ingresa un ID de evaluación válido.';
      return;
    }

    if (
      raw && !Number.isSafeInteger(Number(raw))
    ) {
      this.filterError =
        'El ID de evaluación está fuera de rango.';
      return;
    }

    this.appliedId = raw ? Number(raw) : undefined;

    this.appliedEstablishment =
      this.selectedEstablishment
        ? Number(this.selectedEstablishment)
        : undefined;

    this.appliedStatus =
      this.selectedStatus === 'PENDIENTE' ||
        this.selectedStatus === 'FINALIZADA'
        ? this.selectedStatus
        : undefined;

    this.page = 1;
    this.loadEvaluations();
  }

  clearFilters(): void {
    this.searchId = '';
    this.selectedEstablishment = '';
    this.selectedStatus = '';

    this.appliedId = undefined;
    this.appliedEstablishment = undefined;
    this.appliedStatus = undefined;

    this.filterError = '';
    this.page = 1;
    this.loadEvaluations();
  }

  goToPage(next: number): void {
    if (
      next < 1 ||
      next > this.totalPages ||
      next === this.page
    ) {
      return;
    }

    this.page = next;
    this.loadEvaluations();
  }

  get firstShown(): number {
    return this.total === 0
      ? 0
      : (this.page - 1) * this.pageSize + 1;
  }

  get lastShown(): number {
    return Math.min(this.page * this.pageSize, this.total);
  }

  get visiblePages(): number[] {
    const count = Math.min(5, this.totalPages);

    const start = Math.min(
      Math.max(1, this.page - 2),
      Math.max(1, this.totalPages - 4)
    );

    return Array.from(
      { length: count },
      (_, index) => start + index
    );
  }

  logout(): void {
    for (const key of [
      'access_token',
      'account_type',
      'establishment_id',
      'display_name'
    ]) {
      sessionStorage.removeItem(key);
    }

    this.router.navigate(['/admin/login']);
  }
}
