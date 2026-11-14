import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


export interface Evaluation {
  id_evaluacion: number;
  id_paciente: number;
  id_medico: number;
  id_establecimiento: number;

  fecha_evaluacion: string;
  ojo_evaluado: string;

  observacion_medica: string | null;
  prioridad_sugerida: string | null;

  estado: string;

  fecha_creacion: string;
  fecha_finalizacion: string | null;
  medico_responsable: string;
}

export interface EvaluationDetail {
  id_evaluacion: number;
  fecha_evaluacion: string;
  ojo_evaluado: string;
  estado: string;

  id_paciente: number;
  numero_documento: string;
  nombres_paciente: string;
  apellidos_paciente: string;
  fecha_nacimiento: string;
  sexo: string;

  id_medico: number;
  medico_responsable: string;
}

export interface AIModelResult {
  estado: string;
  resultado: string | null;
  confianza: number | null;
  tiempo_inferencia_ms?: number | null;
  requiere_revision: boolean;
  detalle_error: string | null;
}

export interface AIAnalysisResponse {
  id_analisis: number;
  id_evaluacion: number;
  estado: string;
  retinopatia_diabetica: AIModelResult;
  glaucoma: AIModelResult;
  requiere_revision: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class EvaluationService {

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/v1/patients';

  private analysisResult: AIAnalysisResponse | null = null;

  constructor(
    private http: HttpClient
  ) {
  }


  getPatientEvaluations(
    patientId: number
  ): Observable<Evaluation[]> {

    return this.http.get<Evaluation[]>(
      `${this.apiUrl}/${patientId}/evaluations`
    );
  }

  createEvaluation(
    patientId: number,
    data: {
      fecha_evaluacion: string;
      ojo_evaluado: string;
      medico_responsable: string;
    }
  ): Observable<Evaluation> {

    return this.http.post<Evaluation>(
      `${this.apiUrl}/${patientId}/evaluations`,
      data
    );
  }

  getEvaluationDetail(
    evaluationId: number
  ): Observable<EvaluationDetail> {

    return this.http.get<EvaluationDetail>(
      `http://127.0.0.1:8000/api/v1/evaluations/${evaluationId}`
    );
  }

  uploadRetinography(
    evaluationId: number,
    file: File
  ): Observable<unknown> {

    const formData = new FormData();

    formData.append('file', file);

    return this.http.put<unknown>(
      `http://127.0.0.1:8000/api/v1/evaluations/${evaluationId}/retinography`,
      formData
    );
  }

  getRetinographyImage(evaluationId: number): Observable<Blob> {
    return this.http.get(
      `http://127.0.0.1:8000/api/v1/evaluations/${evaluationId}/retinography/image`,
      {
        responseType: 'blob'
      }
    );
  }

  analyzeEvaluation(
    evaluationId: number
  ): Observable<AIAnalysisResponse> {

    return this.http.post<AIAnalysisResponse>(
      `http://127.0.0.1:8000/api/v1/evaluations/${evaluationId}/analysis`,
      {}
    );
  }

  saveAnalysisResult(result: AIAnalysisResponse): void {
    this.analysisResult = result;
  }

  getAnalysisResult(evaluationId: number): AIAnalysisResponse | null {
    if (this.analysisResult?.id_evaluacion === evaluationId) {
      return this.analysisResult;
    }

    return null;
  }
}