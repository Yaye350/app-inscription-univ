import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `<div class="shell">
    <header class="topbar"><a class="brand" routerLink="/">Campus · Inscriptions</a>
      @if (auth.user(); as user) {
        <nav><a routerLink="/profil" routerLinkActive="active">Mon profil</a>
          @if(user.role==='etudiant'){<a routerLink="/etudiant" routerLinkActive="active">Espace étudiant</a>}
          @if(user.role==='agent'){<a routerLink="/agent" routerLinkActive="active">Espace agent</a>}
          @if(user.role==='admin'){<a routerLink="/admin" routerLinkActive="active">Administration</a>}
          <span>{{user.prenom}} {{user.nom}}</span><button (click)="logout()">Déconnexion</button></nav>
      } @else { <nav><a routerLink="/login">Connexion</a><a routerLink="/inscription">Inscription</a></nav> }
    </header><main><router-outlet /></main>
  </div>`,
})
export class AppComponent {
  auth = inject(AuthService); private router = inject(Router);
  logout(): void { this.auth.logout(); void this.router.navigateByUrl('/login'); }
}
