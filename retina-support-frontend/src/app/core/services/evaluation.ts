import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-url';


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

  retinopatia_diabetica: EvaluationHistoryModelResult | null;
  glaucoma: EvaluationHistoryModelResult | null;
}

export interface EvaluationHistoryModelResult {
  resultado: string;
  confianza: number;
}

export interface EvaluationSummary {
  id_evaluacion: number;
  id_paciente: number;

  nombres_paciente: string;
  apellidos_paciente: string;

  fecha_evaluacion: string;
  ojo_evaluado: string;

  medico_responsable: string;
  estado: string;
}

export interface EvaluationDetail {
  id_evaluacion: number;
  fecha_evaluacion: string;
  ojo_evaluado: string;
  estado: string;
  observacion_medica: string | null;

  id_paciente: number;
  numero_documento: string;
  nombres_paciente: string;
  apellidos_paciente: string;
  fecha_nacimiento: string;
  sexo: string;

  id_medico: number;
  medico_responsable: string;
}

export interface MedicalObservationResponse {
  id_evaluacion: number;
  observacion_medica: string;
  estado: string;
}

export interface EvaluationFinalizeResponse {
  id_evaluacion: number;
  estado: string;
  observacion_medica: string | null;
  fecha_finalizacion: string;
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
  prioridad_sugerida?: string | null;
}


export interface StoredModelResult {
  estado: string;
  resultado: string;
  confianza: number;
  requiere_revision: boolean | null;
}


export interface RetinographyResume {
  id_retinografia: number;
  id_evaluacion: number;
  nombre_archivo: string;
  formato: string;
  tamano_bytes: number;
  estado_validacion: string;
  calidad_imagen: string | null;
  estado: string;
}

export interface StoredRetinography {
  id_retinografia: number;
  nombre_archivo: string;
  formato: string;
  ancho_px: number;
  alto_px: number;
}

export interface AIEvaluationResultsResponse {
  id_evaluacion: number;
  id_analisis: number;
  estado: string;
  retinografia: StoredRetinography;
  retinopatia_diabetica: StoredModelResult;
  glaucoma: StoredModelResult;
  requiere_revision: boolean | null;
  prioridad_sugerida: string | null;
  resumen: string | null;
  aviso_soporte_clinico: string;
}

@Injectable({
  providedIn: 'root'
})
export class EvaluationService {

  private readonly apiUrl = `${API_BASE_URL}/patients`;

  private readonly evaluationsApiUrl = `${API_BASE_URL}/evaluations`;

  private analysisResult: AIAnalysisResponse | null = null;

  constructor(
    private http: HttpClient
  ) {
  }

  getEstablishmentEvaluations(): Observable<EvaluationSummary[]> {
    return this.http.get<EvaluationSummary[]>(
      this.evaluationsApiUrl
    );
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

  updateEvaluation(
    evaluationId: number,
    data: {
      fecha_evaluacion: string;
      ojo_evaluado: string;
      medico_responsable: string;
    }
  ): Observable<{ id_evaluacion: number }> {
    return this.http.patch<{ id_evaluacion: number }>(
      `${this.evaluationsApiUrl}/${evaluationId}`,
      data
    );
  }

  getEvaluationDetail(
    evaluationId: number
  ): Observable<EvaluationDetail> {

    return this.http.get<EvaluationDetail>(
      `${this.evaluationsApiUrl}/${evaluationId}`
    );
  }

  updateMedicalObservation(
    evaluationId: number,
    observation: string
  ): Observable<MedicalObservationResponse> {

    return this.http.patch<MedicalObservationResponse>(
      `${this.evaluationsApiUrl}/${evaluationId}/medical-observation`,
      { observacion_medica: observation }
    );
  }

  finalizeEvaluation(
    evaluationId: number,
    observation: string | null
  ): Observable<EvaluationFinalizeResponse> {

    return this.http.post<EvaluationFinalizeResponse>(
      `${this.evaluationsApiUrl}/${evaluationId}/finalize`,
      { observacion_medica: observation }
    );
  }

  uploadRetinography(
    evaluationId: number,
    file: File
  ): Observable<unknown> {

    const formData = new FormData();

    formData.append('file', file);

    return this.http.put<unknown>(
      `${this.evaluationsApiUrl}/${evaluationId}/retinography`,
      formData
    );
  }

  getRetinographyResume(
    evaluationId: number
  ): Observable<RetinographyResume> {
    return this.http.get<RetinographyResume>(
      `${this.evaluationsApiUrl}/${evaluationId}/retinography`
    );
  }

  getRetinographyImage(evaluationId: number): Observable<Blob> {
    return this.http.get(
      `${this.evaluationsApiUrl}/${evaluationId}/retinography/image`,
      {
        responseType: 'blob'
      }
    );
  }

  getStoredEvaluationResults(
    evaluationId: number
  ): Observable<AIEvaluationResultsResponse> {

    return this.http.get<AIEvaluationResultsResponse>(
      `${this.evaluationsApiUrl}/${evaluationId}/results`
    );
  }

  analyzeEvaluation(
    evaluationId: number
  ): Observable<AIAnalysisResponse> {

    return this.http.post<AIAnalysisResponse>(
      `${this.evaluationsApiUrl}/${evaluationId}/analysis`,
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