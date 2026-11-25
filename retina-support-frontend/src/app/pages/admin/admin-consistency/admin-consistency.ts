import { ChangeDetectorRef, Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  Router,
  RouterLink,
  RouterLinkActive
} from '@angular/router';

import {
  AdminConsistencyItem,
  AdminConsistencyService,
  ConsistencyStatus
} from '../../../core/services/admin-consistency';



@Component({
  selector: 'app-admin-consistency',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './admin-consistency.html',
  styleUrls: [
    '../admin-dashboard/admin-dashboard.css',
    './admin-consistency.css'
  ]
})
export class AdminConsistency implements OnInit {

  readonly displayName =
    sessionStorage.getItem('display_name') ?? 'Administrador';

  records: AdminConsistencyItem[] = [];

  selectedRecord: AdminConsistencyItem | null = null;

  reviewedRecords: number | null = null;
  incidentRecords: number | null = null;

  loading = true;
  summaryLoading = true;

  errorMessage = '';
  summaryError = '';

  page = 1;
  readonly pageSize = 8;
  total = 0;
  totalPages = 0;

  private requestId = 0;


  getStatusLabel(status: ConsistencyStatus): string {
    switch (status) {
      case 'CONSISTENTE':
        return 'Consistente';
      case 'EN_PROCESO':
        return 'En proceso';
      case 'REQUIERE_ATENCION':
        return 'Requiere atención';
    }
  }

  getStatusClass(status: ConsistencyStatus): string {
    switch (status) {
      case 'CONSISTENTE':
        return 'consistent';
      case 'EN_PROCESO':
        return 'in-progress';
      case 'REQUIERE_ATENCION':
        return 'needs-attention';
    }
  }

  constructor(
    private service: AdminConsistencyService,
    private cdr: ChangeDetectorRef,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadSummary();
    this.loadRecords();
  }

  loadSummary(): void {
    this.summaryLoading = true;
    this.summaryError = '';

    this.service.summary().subscribe({
      next: result => {
        this.reviewedRecords = result.registros_revisados;
        this.incidentRecords = result.con_incidencias;

        this.summaryLoading = false;
        this.cdr.markForCheck();
      },
      error: error => {
        if (error.status === 401 || error.status === 403) {
          this.logout();
          return;
        }

        this.reviewedRecords = null;
        this.incidentRecords = null;

        this.summaryLoading = false;
        this.summaryError =
          'No se pudieron cargar los indicadores.';

        this.cdr.markForCheck();
      }
    });
  }

  loadRecords(): void {
    const currentRequest = ++this.requestId;

    this.loading = true;
    this.errorMessage = '';

    this.service.list({
      page: this.page,
      page_size: this.pageSize
    }).subscribe({
      next: response => {
        if (currentRequest !== this.requestId) {
          return;
        }

        this.records = response.items;
        this.total = response.total;
        this.page = response.page;
        this.totalPages = response.total_pages;

        this.loading = false;
        this.cdr.markForCheck();
      },
      error: error => {
        if (currentRequest !== this.requestId) {
          return;
        }

        if (error.status === 401 || error.status === 403) {
          this.logout();
          return;
        }

        this.records = [];
        this.total = 0;
        this.totalPages = 0;
        this.loading = false;

        this.errorMessage =
          'No se pudieron cargar los resultados de verificación.';

        this.cdr.markForCheck();
      }
    });
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
    this.loadRecords();
  }

  get firstShown(): number {
    return this.total === 0
      ? 0
      : (this.page - 1) * this.pageSize + 1;
  }

  get lastShown(): number {
    return Math.min(
      this.page * this.pageSize,
      this.total
    );
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


  showIssues(
    record: AdminConsistencyItem,
    dialog: HTMLDialogElement
  ): void {
    if (record.incidencias.length === 0) {
      return;
    }

    this.selectedRecord = record;
    this.cdr.markForCheck();
    dialog.showModal();
  }

  closeIssues(dialog: HTMLDialogElement): void {
    dialog.close();
  }

  onIssuesDialogClosed(): void {
    this.selectedRecord = null;
    this.cdr.markForCheck();
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
