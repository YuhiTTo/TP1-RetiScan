import { ChangeDetectorRef, Component, OnInit } from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import {
    EvaluationSummary,
    EvaluationService
} from '../../../core/services/evaluation';

@Component({
    selector: 'app-evaluation-list',
    imports: [
        CommonModule,
        FormsModule
    ],
    templateUrl: './evaluation-list.html',
    styleUrl: './evaluation-list.css'
})
export class EvaluationList implements OnInit {

    evaluations: EvaluationSummary[] = [];

    searchTerm = '';

    statusFilter = 'TODOS';

    loading = false;

    errorMessage = '';

    displayName =
        localStorage.getItem('display_name') ?? 'Establecimiento';

    readonly pageSize = 8;

    currentPage = 1;


    constructor(
        private router: Router,
        private evaluationService: EvaluationService,
        private cdr: ChangeDetectorRef
    ) { }


    ngOnInit(): void {
        this.loadEvaluations();
    }


    loadEvaluations(): void {

        this.currentPage = 1;
        this.loading = true;
        this.errorMessage = '';

        this.evaluationService
            .getEstablishmentEvaluations()
            .subscribe({

                next: (response) => {

                    console.log('Evaluaciones recibidas:', response);

                    this.evaluations = response;

                    this.loading = false;

                    this.cdr.markForCheck();
                },

                error: (error) => {

                    console.error('Error al cargar evaluaciones:', error);

                    this.loading = false;

                    if (error.status === 401) {
                        this.logout();
                    } else {
                        this.errorMessage =
                            'No se pudieron cargar las evaluaciones.';

                        this.cdr.markForCheck();
                    }
                }
            });
    }


    get filteredEvaluations(): EvaluationSummary[] {

        const term = this.searchTerm.trim().toLowerCase();

        return this.evaluations.filter(evaluation => {

            const matchesSearch = !term || [

                `${evaluation.nombres_paciente} ${evaluation.apellidos_paciente}`,

                evaluation.nombres_paciente,

                evaluation.apellidos_paciente,

                evaluation.ojo_evaluado,

                evaluation.medico_responsable,

                String(evaluation.id_evaluacion)

            ].some(value =>
                (value ?? '').toLowerCase().includes(term)
            );

            const matchesStatus =
                this.statusFilter === 'TODOS' ||
                evaluation.estado.toUpperCase() === this.statusFilter;

            return matchesSearch && matchesStatus;
        });
    }


    get totalPages(): number {
        return Math.max(
            1,
            Math.ceil(this.filteredEvaluations.length / this.pageSize)
        );
    }


    get paginatedEvaluations(): EvaluationSummary[] {

        const start = (this.currentPage - 1) * this.pageSize;

        return this.filteredEvaluations.slice(
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

        return this.filteredEvaluations.length === 0
            ? 0
            : (this.currentPage - 1) * this.pageSize + 1;
    }


    get shownEnd(): number {

        return Math.min(
            this.currentPage * this.pageSize,
            this.filteredEvaluations.length
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


    getStatusLabel(status: string): string {

        switch (status.toUpperCase()) {

            case 'FINALIZADA':
                return 'Finalizada';

            case 'PENDIENTE':
                return 'Pendiente';

            default:
                return status;
        }
    }


    getStatusClass(status: string): string {

        switch (status.toUpperCase()) {

            case 'FINALIZADA':
                return 'status-finalizada';

            case 'PENDIENTE':
                return 'status-pendiente';

            default:
                return 'status-other';
        }
    }


    viewEvaluation(evaluationId: number): void {

        this.router.navigate([
            '/evaluations',
            evaluationId,
            'detail'
        ]);
    }


    continueEvaluation(evaluationId: number): void {

        this.router.navigate([
            '/evaluations',
            evaluationId,
            'retinography'
        ]);
    }


    goToHome(): void {
        this.router.navigate(['/home']);
    }


    goToPatients(): void {
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