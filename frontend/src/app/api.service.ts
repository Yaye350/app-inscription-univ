import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { API_URL } from './auth.service';
import { Campagne, Dossier, Formation, Piece, Stats, User } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  me() {
    return this.http.get<User>(`${API_URL}/me`);
  }

  updateMe(body: Partial<User>) {
    return this.http.put<User>(`${API_URL}/me`, body);
  }

  campagnes() {
    return this.http.get<Campagne[]>(`${API_URL}/campagnes`);
  }

  saveCampagne(body: Omit<Campagne, 'id' | 'ouverte'>, id?: number) {
    if (id) {
      return this.http.put<Campagne>(`${API_URL}/campagnes/${id}`, body);
    }
    return this.http.post<Campagne>(`${API_URL}/campagnes`, body);
  }

  deleteCampagne(id: number) {
    return this.http.delete(`${API_URL}/campagnes/${id}`);
  }

  formations() {
    return this.http.get<Formation[]>(`${API_URL}/formations`);
  }

  saveFormation(body: Omit<Formation, 'id'>, id?: number) {
    if (id) {
      return this.http.put<Formation>(`${API_URL}/formations/${id}`, body);
    }
    return this.http.post<Formation>(`${API_URL}/formations`, body);
  }

  deleteFormation(id: number) {
    return this.http.delete(`${API_URL}/formations/${id}`);
  }

  users() {
    return this.http.get<User[]>(`${API_URL}/users`);
  }

  updateRole(id: number, role: string) {
    return this.http.patch<User>(`${API_URL}/users/${id}/role`, { role });
  }

  dossiers(filters: Record<string, string> = {}) {
    return this.http.get<Dossier[]>(`${API_URL}/dossiers`, { params: this.params(filters) });
  }

  dossier(id: number) {
    return this.http.get<Dossier>(`${API_URL}/dossiers/${id}`);
  }

  createDossier(body: { campagne_id: number; formation_id: number; commentaire?: string }) {
    return this.http.post<Dossier>(`${API_URL}/dossiers`, body);
  }

  updateDossier(id: number, body: { formation_id?: number; commentaire?: string }) {
    return this.http.put<Dossier>(`${API_URL}/dossiers/${id}`, body);
  }

  uploadPiece(id: number, typePiece: string, file: File) {
    const data = new FormData();
    data.append('type_piece', typePiece);
    data.append('fichier', file);
    return this.http.post<Piece>(`${API_URL}/dossiers/${id}/pieces`, data);
  }

  deletePiece(dossierId: number, pieceId: number) {
    return this.http.delete(`${API_URL}/dossiers/${dossierId}/pieces/${pieceId}`);
  }

  downloadPiece(dossierId: number, pieceId: number) {
    return this.http.get(`${API_URL}/dossiers/${dossierId}/pieces/${pieceId}`, { responseType: 'blob' });
  }

  submit(id: number) {
    return this.http.post<Dossier>(`${API_URL}/dossiers/${id}/soumettre`, {});
  }

  complement(id: number, motif: string) {
    return this.http.post<Dossier>(`${API_URL}/dossiers/${id}/complement`, { motif });
  }

  accept(id: number, motif: string) {
    return this.http.post<Dossier>(`${API_URL}/dossiers/${id}/accepter`, { motif });
  }

  reject(id: number, motif: string) {
    return this.http.post<Dossier>(`${API_URL}/dossiers/${id}/rejeter`, { motif });
  }

  stats() {
    return this.http.get<Stats>(`${API_URL}/rapports/statistiques`);
  }

  exportCsv(filters: Record<string, string>) {
    return this.http.get(`${API_URL}/rapports/dossiers.csv`, {
      params: this.params(filters),
      responseType: 'blob',
    });
  }

  private params(filters: Record<string, string>): HttpParams {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value) {
        params = params.set(key, value);
      }
    }
    return params;
  }
}
