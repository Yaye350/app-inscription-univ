import { Component, inject, OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';
import { errorMessage } from './models';

@Component({
  selector: 'app-profil',
  imports: [FormsModule],
  template: `
    <section class="panel">
      <h1>Informations personnelles</h1>
      <p class="muted">Les champs marqués sont nécessaires avant la soumission d'un dossier.</p>
      @if (message()) { <div class="alert ok">{{ message() }}</div> }
      @if (error()) { <div class="alert">{{ error() }}</div> }
      <form class="grid two" (ngSubmit)="save()">
        <label><span class="req">Prénom</span><input name="prenom" required [(ngModel)]="prenom"></label>
        <label><span class="req">Nom</span><input name="nom" required [(ngModel)]="nom"></label>
        <label><span class="req">Date de naissance</span><input type="date" name="date" required [(ngModel)]="dateNaissance"></label>
        <label><span class="req">CIN</span><input name="cin" required [(ngModel)]="cin"></label>
        <label>Téléphone<input name="telephone" [(ngModel)]="telephone"></label>
        <label>Adresse<textarea name="adresse" [(ngModel)]="adresse"></textarea></label>
        <div class="actions"><button type="submit">Enregistrer</button></div>
      </form>
    </section>
  `,
})
export class ProfilComponent implements OnInit {
  private api = inject(ApiService);
  private auth = inject(AuthService);
  prenom = '';
  nom = '';
  dateNaissance = '';
  cin = '';
  telephone = '';
  adresse = '';
  message = signal('');
  error = signal('');

  ngOnInit(): void {
    this.api.me().subscribe((user) => {
      this.auth.updateStoredUser(user);
      this.prenom = user.prenom;
      this.nom = user.nom;
      this.dateNaissance = user.date_naissance ?? '';
      this.cin = user.cin ?? '';
      this.telephone = user.telephone ?? '';
      this.adresse = user.adresse ?? '';
    });
  }

  save(): void {
    this.message.set('');
    this.error.set('');
    this.api.updateMe({
      prenom: this.prenom,
      nom: this.nom,
      date_naissance: this.dateNaissance || null,
      cin: this.cin,
      telephone: this.telephone,
      adresse: this.adresse,
    }).subscribe({
      next: (user) => {
        this.auth.updateStoredUser(user);
        this.message.set('Profil enregistré.');
      },
      error: (err) => this.error.set(errorMessage(err)),
    });
  }
}
