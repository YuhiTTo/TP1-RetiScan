import {
  ChangeDetectorRef,
  Component,
  OnInit
} from '@angular/core';

import { CommonModule } from '@angular/common';

import {
  Router,
  RouterLink,
  RouterLinkActive
} from '@angular/router';

import {
  AdminHomeService,
  AdminHomeSummary
} from '../../../core/services/admin-home';

@Component({
  selector: 'app-admin-home',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive
  ],
  templateUrl: './admin-home.html',
  styleUrls: [
    '../admin-dashboard/admin-dashboard.css',
    './admin-home.css'
  ]
})
export class AdminHome implements OnInit {

  readonly displayName =
    sessionStorage.getItem('display_name') ?? 'Administrador';

  summary: AdminHomeSummary | null = null;

  loading = true;
  errorMessage = '';

  page = 1;
  readonly pageSize = 8;

  constructor(
    private service: AdminHomeService,
    private cdr: ChangeDetectorRef,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadSummary();
  }

  loadSummary(): void {
    this.loading = true;
    this.errorMessage = '';
    this.summary = null;

    this.service.summary().subscribe({
      next: (result: AdminHomeSummary) => {
        this.summary = result;
        this.page = 1;
        this.loading = false;
        this.cdr.markForCheck();
      },

      error: (error) => {
        if (error.status === 401 || error.status === 403) {
          this.logout();
          return;
        }

        this.loading = false;
        this.summary = null;
        this.errorMessage =
          'No se pudo cargar el resumen administrativo.';
        this.cdr.markForCheck();
      }
    });
  }

  get total(): number {
    return this.summary?.actividad_establecimientos.length ?? 0;
  }

  get totalPages(): number {
    return Math.ceil(this.total / this.pageSize);
  }

  get pagedActivity(): AdminHomeSummary['actividad_establecimientos'] {
    const start = (this.page - 1) * this.pageSize;

    return this.summary?.actividad_establecimientos.slice(
      start,
      start + this.pageSize
    ) ?? [];
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

  goToPage(next: number): void {
    if (
      this.loading ||
      next < 1 ||
      next > this.totalPages ||
      next === this.page
    ) {
      return;
    }

    this.page = next;
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
