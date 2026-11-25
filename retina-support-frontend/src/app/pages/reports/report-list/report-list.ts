
import {
    ChangeDetectorRef,
    Component,
    OnDestroy,
    OnInit
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import {
    DomSanitizer,
    SafeResourceUrl
} from '@angular/platform-browser';
import { Router } from '@angular/router';

import {
    ReportListItem,
    ReportService
} from '../../../core/services/report';


@Component({
    selector: 'app-report-list',
    imports: [
        CommonModule,
        FormsModule
    ],
    templateUrl: './report-list.html',
    styleUrl: './report-list.css'
})
export class ReportList implements OnInit, OnDestroy {

    reports: ReportListItem[] = [];

    searchTerm = '';

    statusFilter = 'TODOS';

    loading = false;

    errorMessage = '';

    reportActionMessage = '';

    displayName =
        sessionStorage.getItem('display_name') ?? 'Establecimiento';

    readonly pageSize = 8;

    currentPage = 1;

    reportGeneratingId: number | null = null;

    reportViewingId: number | null = null;

    reportDownloadingId: number | null = null;

    reportPreviewOpen = false;

    reportPreviewUrl: SafeResourceUrl | null = null;

    private reportObjectUrl: string | null = null;


    constructor(
        private router: Router,
        private reportService: ReportService,
        private sanitizer: DomSanitizer,
        private cdr: ChangeDetectorRef
    ) { }


    ngOnInit(): void {
        this.loadReports();
    }


    loadReports(): void {

        this.currentPage = 1;
        this.loading = true;
        this.errorMessage = '';

        this.reportService
            .getEstablishmentReports()
            .subscribe({

                next: (response) => {

                    this.reports = [...response];

                    this.loading = false;

                    this.cdr.markForCheck();
                },

                error: (error) => {

                    this.loading = false;

                    if (error.status === 401) {

                        this.logout();

                    } else {

                        this.errorMessage =
                            'No se pudieron cargar los reportes.';

                        this.cdr.markForCheck();
                    }
                }
            });
    }


    get filteredReports(): ReportListItem[] {

        const term = this.searchTerm.trim().toLowerCase();

        return this.reports.filter(report => {

            const fullName =
                `${report.nombres_paciente} ${report.apellidos_paciente}`;

            const matchesSearch = !term || [

                fullName,

                report.nombres_paciente,

                report.apellidos_paciente,

                report.ojo_evaluado,

                report.medico_responsable,

                String(report.id_evaluacion)

            ].some(value =>
                (value ?? '').toLowerCase().includes(term)
            );

            const matchesStatus =
                this.statusFilter === 'TODOS' ||
                (
                    this.statusFilter === 'DISPONIBLE' &&
                    report.tiene_reporte
                ) ||
                (
                    this.statusFilter === 'NO_GENERADO' &&
                    !report.tiene_reporte
                );

            return matchesSearch && matchesStatus;
        });
    }


    get totalPages(): number {

        return Math.max(
            1,
            Math.ceil(this.filteredReports.length / this.pageSize)
        );
    }


    get paginatedReports(): ReportListItem[] {

        const start = (this.currentPage - 1) * this.pageSize;

        return this.filteredReports.slice(
            start,
            start + this.pageSize
        );
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

        return this.filteredReports.length === 0
            ? 0
            : (this.currentPage - 1) * this.pageSize + 1;
    }


    get shownEnd(): number {

        return Math.min(
            this.currentPage * this.pageSize,
            this.filteredReports.length
        );
    }


    onFilterChange(): void {

        this.currentPage = 1;

        this.cdr.markForCheck();
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


    getReportStatusLabel(report: ReportListItem): string {

        return report.tiene_reporte
            ? 'Disponible'
            : 'No generado';
    }


    getReportStatusClass(report: ReportListItem): string {

        return report.tiene_reporte
            ? 'status-available'
            : 'status-not-generated';
    }


    generateReport(evaluationId: number): void {

        if (this.reportGeneratingId !== null) {
            return;
        }

        const report = this.reports.find(
            item => item.id_evaluacion === evaluationId
        );

        if (!report || report.tiene_reporte) {
            return;
        }

        this.reportGeneratingId = evaluationId;

        this.errorMessage = '';
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

                        this.errorMessage =
                            'El reporte ya existe o la evaluación ' +
                            'todavía no está lista para generarlo.';

                    } else if (error.status === 503) {

                        this.errorMessage =
                            'No se pudo confirmar la generación. ' +
                            'Consulta nuevamente el listado antes de reintentar.';

                    } else {

                        this.errorMessage =
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

        this.errorMessage = '';

        this.reportService
            .viewReport(evaluationId)
            .subscribe({

                next: (blob) => {

                    this.reportViewingId = null;

                    if (!blob.size) {

                        this.errorMessage =
                            'El archivo PDF está vacío.';

                        this.cdr.markForCheck();

                        return;
                    }

                    this.closeReportPreview();

                    const pdfBlob = new Blob(
                        [blob],
                        { type: 'application/pdf' }
                    );

                    this.reportObjectUrl =
                        URL.createObjectURL(pdfBlob);

                    this.reportPreviewUrl =
                        this.sanitizer.bypassSecurityTrustResourceUrl(
                            this.reportObjectUrl +
                            '#toolbar=0&navpanes=0'
                        );

                    this.reportPreviewOpen = true;

                    this.cdr.markForCheck();
                },

                error: (error) => {

                    this.reportViewingId = null;

                    if (error.status === 401) {

                        this.logout();

                    } else {

                        this.errorMessage =
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

        this.errorMessage = '';

        this.reportService
            .downloadReport(evaluationId)
            .subscribe({

                next: (blob) => {

                    this.reportDownloadingId = null;

                    if (!blob.size) {

                        this.errorMessage =
                            'El archivo PDF está vacío.';

                        this.cdr.markForCheck();

                        return;
                    }

                    const url = URL.createObjectURL(
                        new Blob(
                            [blob],
                            { type: 'application/pdf' }
                        )
                    );

                    const link = document.createElement('a');

                    link.href = url;

                    link.download =
                        `RetiScan_reporte_${evaluationId}.pdf`;

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

                        this.errorMessage =
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


    goToHome(): void {
        this.router.navigate(['/home']);
    }


    goToPatients(): void {
        this.router.navigate(['/patients']);
    }


    goToEvaluations(): void {
        this.router.navigate(['/evaluations']);
    }


    logout(): void {

        this.closeReportPreview();

        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('account_type');
        sessionStorage.removeItem('establishment_id');
        sessionStorage.removeItem('display_name');

        this.router.navigate(['/login']);
    }

}