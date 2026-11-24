import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs';
import { User } from './models';

export const API_URL = 'http://localhost:8000';

interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  user = signal<User | null>(this.read());

  get token(): string | null {
    return localStorage.getItem('token');
  }

  login(email: string, password: string) {
    return this.http.post<LoginResponse>(`${API_URL}/auth/login`, { email, password }).pipe(
      tap((response) => this.setSession(response.access_token, response.user)),
    );
  }

  register(payload: { email: string; password: string; nom: string; prenom: string }) {
    return this.http.post<User>(`${API_URL}/auth/register`, payload);
  }

  setSession(token: string, user: User): void {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    this.user.set(user);
  }

  updateStoredUser(user: User): void {
    localStorage.setItem('user', JSON.stringify(user));
    this.user.set(user);
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    this.user.set(null);
  }

  private read(): User | null {
    const raw = localStorage.getItem('user');
    if (!raw) {
      return null;
    }
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }
}
