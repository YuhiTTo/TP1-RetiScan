import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-url';


export interface PatientReport {
  id_evaluacion: number;
  fecha_evaluacion: string;
  ojo_evaluado: string;
  tiene_reporte: boolean;
  fecha_generacion: string | null;
}


export interface ReportListItem {
  id_evaluacion: number;
  id_paciente: number;

  nombres_paciente: string;
  apellidos_paciente: string;

  fecha_evaluacion: string;
  ojo_evaluado: string;

  medico_responsable: string;

  tiene_reporte: boolean;
  id_reporte: number | null;
  fecha_generacion: string | null;
}


export interface ReportGenerationResponse {
  id_reporte: number;
  id_evaluacion: number;
  fecha_generacion: string;
  mensaje: string;
}


@Injectable({
  providedIn: 'root'
})
export class ReportService {

  private readonly apiUrl = API_BASE_URL;

  constructor(
    private http: HttpClient
  ) {
  }


  getPatientReports(
    patientId: number
  ): Observable<PatientReport[]> {

    return this.http.get<PatientReport[]>(
      `${this.apiUrl}/patients/${patientId}/reports`
    );
  }


  getEstablishmentReports(): Observable<ReportListItem[]> {

    return this.http.get<ReportListItem[]>(
      `${this.apiUrl}/reports/`
    );
  }


  generateReport(
    evaluationId: number
  ): Observable<ReportGenerationResponse> {

    return this.http.post<ReportGenerationResponse>(
      `${this.apiUrl}/evaluations/${evaluationId}/report`,
      {}
    );
  }


  viewReport(
    evaluationId: number
  ): Observable<Blob> {

    return this.http.get(
      `${this.apiUrl}/evaluations/${evaluationId}/report`,
      {
        responseType: 'blob'
      }
    );
  }


  downloadReport(
    evaluationId: number
  ): Observable<Blob> {

    return this.http.get(
      `${this.apiUrl}/evaluations/${evaluationId}/report/download`,
      {
        responseType: 'blob'
      }
    );
  }
}
