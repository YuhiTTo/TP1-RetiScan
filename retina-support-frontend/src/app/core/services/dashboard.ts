import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


export interface DashboardRecentEvaluation {
    id_evaluacion: number;
    nombres_paciente: string;
    apellidos_paciente: string;
    fecha_evaluacion: string;
    ojo_evaluado: string;
    estado: string;
}


export interface DashboardSummary {
    total_pacientes: number;
    evaluaciones_realizadas: number;
    evaluaciones_pendientes: number;
    reportes_generados: number;
    evaluaciones_recientes: DashboardRecentEvaluation[];
}


@Injectable({
    providedIn: 'root'
})
export class DashboardService {

    private readonly apiUrl =
        'http://127.0.0.1:8000/api/v1/dashboard/summary';

    constructor(
        private http: HttpClient
    ) { }

    getSummary(): Observable<DashboardSummary> {

        return this.http.get<DashboardSummary>(
            this.apiUrl
        );

    }
}