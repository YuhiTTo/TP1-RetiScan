import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-url';


export interface Patient {
  id_paciente: number;
  id_establecimiento: number;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  fecha_nacimiento: string;
  sexo: string;
  telefono: string | null;
  correo: string | null;
  direccion: string | null;
  estado: boolean;
  fecha_registro: string;
  ultima_evaluacion: string | null;
}


@Injectable({
  providedIn: 'root'
})
export class PatientService {

  private readonly apiUrl = `${API_BASE_URL}/patients`;

  constructor(
    private http: HttpClient
  ) {
  }

  createPatient(
    data: {
      numero_documento: string;
      nombres: string;
      apellidos: string;
      fecha_nacimiento: string;
      sexo: string;
      telefono: string | null;
      correo: string | null;
      direccion: string | null;
    }
  ): Observable<Patient> {

    return this.http.post<Patient>(
      this.apiUrl,
      data
    );
  }

  getPatients(
    search: string = ''
  ): Observable<Patient[]> {

    let params = new HttpParams();

    if (search.trim()) {
      params = params.set(
        'search',
        search.trim()
      );
    }

    return this.http.get<Patient[]>(
      this.apiUrl,
      { params }
    );
  }

  getPatientById(
    patientId: number
  ): Observable<Patient> {
    return this.http.get<Patient>(
      `${this.apiUrl}/${patientId}`
    );
  }

  updatePatient(
    patientId: number,
    data: Partial<Patient>
  ): Observable<Patient> {

    return this.http.patch<Patient>(
      `${this.apiUrl}/${patientId}`,
      data
    );
  }
}