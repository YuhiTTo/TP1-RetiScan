import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AdminEvaluation {
  id_evaluacion: number;
  id_establecimiento: number;
  establecimiento: string;
  fecha_evaluacion: string;
  ojo_evaluado: string;
  estado: string;
}

export interface AdminEvaluationsPage {
  items: AdminEvaluation[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminEvaluationsSummary {
  total_evaluaciones: number;
  evaluaciones_pendientes: number;
  evaluaciones_finalizadas: number;
  establecimientos_con_evaluaciones: number;
}

export interface AdminEvaluationsFilters {
  page: number;
  page_size: number;
  evaluation_id?: number;
  establishment_id?: number;
  estado?: 'PENDIENTE' | 'FINALIZADA';
}

@Injectable({
  providedIn: 'root'
})
export class AdminEvaluationsService {

  private readonly url =
    'http://127.0.0.1:8000/api/v1/admin/evaluations';

  constructor(private http: HttpClient) {}

  list(
    filters: AdminEvaluationsFilters
  ): Observable<AdminEvaluationsPage> {

    let params = new HttpParams()
      .set('page', filters.page)
      .set('page_size', filters.page_size);

    if (filters.evaluation_id !== undefined) {
      params = params.set(
        'evaluation_id', filters.evaluation_id
      );
    }

    if (filters.establishment_id !== undefined) {
      params = params.set(
        'establishment_id', filters.establishment_id
      );
    }

    if (filters.estado !== undefined) {
      params = params.set('estado', filters.estado);
    }

    return this.http.get<AdminEvaluationsPage>(
      this.url, { params }
    );
  }

  summary(): Observable<AdminEvaluationsSummary> {
    return this.http.get<AdminEvaluationsSummary>(
      `${this.url}/summary`
    );
  }
}
