import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AdminHomeEstablishmentActivity {
  id_establecimiento: number;
  establecimiento: string;
  evaluaciones_ultimos_7_dias: number;
  ultima_evaluacion: string | null;
}

export interface AdminHomeSummary {
  total_establecimientos: number;
  establecimientos_con_actividad_reciente: number;
  actividad_establecimientos: AdminHomeEstablishmentActivity[];
}

@Injectable({
  providedIn: 'root'
})
export class AdminHomeService {

  private readonly url =
    'http://127.0.0.1:8000/api/v1/admin/home/summary';

  constructor(private http: HttpClient) {}

  summary(): Observable<AdminHomeSummary> {
    return this.http.get<AdminHomeSummary>(this.url);
  }
}
