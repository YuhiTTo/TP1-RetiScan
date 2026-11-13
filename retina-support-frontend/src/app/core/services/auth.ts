import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';


export interface LoginRequest {
  email: string;
  password: string;
}


export interface LoginResponse {
  access_token: string;
  token_type: string;
  account_type: string;
  establishment_id: number | null;
  display_name: string;
}


@Injectable({
  providedIn: 'root'
})
export class AuthService {

  private readonly apiUrl =
    'http://127.0.0.1:8000/api/v1/auth';

  constructor(
    private http: HttpClient
  ) {
  }

  login(
    credentials: LoginRequest
  ): Observable<LoginResponse> {

    return this.http.post<LoginResponse>(
      `${this.apiUrl}/login`,
      credentials
    );
  }
}