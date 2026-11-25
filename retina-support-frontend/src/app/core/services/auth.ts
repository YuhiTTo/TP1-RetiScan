import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { API_BASE_URL } from './api-url';


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

  private readonly apiUrl = `${API_BASE_URL}/auth`;

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