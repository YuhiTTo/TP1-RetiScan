import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-url';


export interface Establishment {
  id_establecimiento: number;
  codigo_institucional: string;
  nombre: string;
  ruc: string | null;
  direccion: string;
  distrito: string;
  telefono: string;
  estado: boolean;
  fecha_registro: string;
}

export interface CreateInstitutionalAccountRequest {
  establecimiento: {
    nombre: string;
    ruc: string | null;
    direccion: string;
    distrito: string;
    telefono: string;
    estado: boolean;
  };

  cuenta: {
    correo_electronico: string;
    password: string;
    nombre_mostrado: string | null;
  };
}

export interface CreateInstitutionalAccountResponse {
  id_establecimiento: number;
  codigo_institucional: string;
  nombre_establecimiento: string;

  id_cuenta: number;
  correo_electronico: string;
  tipo_cuenta: string;
}

export interface EstablishmentDetail {
  id_establecimiento: number;
  codigo_institucional: string;
  nombre: string;
  ruc: string | null;
  direccion: string;
  distrito: string;
  telefono: string;
  estado: boolean;
  fecha_registro: string;
  correo_electronico: string;
}

export interface UpdateEstablishmentRequest {
  nombre: string;
  ruc: string | null;
  direccion: string;
  distrito: string;
  telefono: string;
  estado: boolean;
  correo_electronico: string;
  nueva_password: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class AdminEstablishmentService {

  private readonly apiUrl = `${API_BASE_URL}/admin/establishments`;


  constructor(
    private http: HttpClient
  ) {
  }


  getEstablishments(): Observable<Establishment[]> {

    return this.http.get<Establishment[]>(
      this.apiUrl
    );
  }

  getEstablishmentDetail(
    idEstablishment: number
  ): Observable<EstablishmentDetail> {

    return this.http.get<EstablishmentDetail>(
      `${this.apiUrl}/${idEstablishment}`
    );
  }

  createEstablishment(
    data: CreateInstitutionalAccountRequest
  ): Observable<CreateInstitutionalAccountResponse> {
    return this.http.post<CreateInstitutionalAccountResponse>(
      `${API_BASE_URL}/institutional-accounts`,
      data
    );
  }

  updateEstablishment(
    idEstablishment: number,
    data: UpdateEstablishmentRequest
  ): Observable<Establishment> {

    return this.http.patch<Establishment>(
      `${this.apiUrl}/${idEstablishment}`,
      data
    );
  }
}
