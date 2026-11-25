import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-url';


export type ConsistencyStatus =
  | 'CONSISTENTE'
  | 'EN_PROCESO'
  | 'REQUIERE_ATENCION';

export type ConsistencyCode =
  | 'CONS-01'
  | 'CONS-02'
  | 'CONS-03'
  | 'CONS-04'
  | 'CONS-05';

export interface AdminConsistencyIssue {
  codigo: ConsistencyCode;
  descripcion: string;
}

export interface AdminConsistencyItem {
  id_evaluacion: number;
  id_establecimiento: number;
  establecimiento: string;
  consistencia: ConsistencyStatus;
  incidencias: AdminConsistencyIssue[];
}

export interface AdminConsistencyPage {
  items: AdminConsistencyItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminConsistencySummary {
  registros_revisados: number;
  con_incidencias: number;
}

export interface AdminConsistencyFilters {
  page: number;
  page_size: number;
}

@Injectable({
  providedIn: 'root'
})
export class AdminConsistencyService {

  private readonly url = `${API_BASE_URL}/admin/consistency`;

  constructor(private http: HttpClient) { }

  list(
    filters: AdminConsistencyFilters
  ): Observable<AdminConsistencyPage> {

    const params = new HttpParams()
      .set('page', filters.page)
      .set('page_size', filters.page_size);

    return this.http.get<AdminConsistencyPage>(
      this.url,
      { params }
    );
  }

  summary(): Observable<AdminConsistencySummary> {
    return this.http.get<AdminConsistencySummary>(
      `${this.url}/summary`
    );
  }
}
