import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


export interface PatientReport {
  id_evaluacion: number;
  fecha_evaluacion: string;
  ojo_evaluado: string;
  tiene_reporte: boolean;
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

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/v1';

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
