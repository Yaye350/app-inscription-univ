import { Component, inject, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './auth.service';

@Component({
  selector: 'app-home',
  template: `<p class="muted">Ouverture de votre espace…</p>`,
})
export class HomeComponent implements OnInit {
  private auth = inject(AuthService);
  private router = inject(Router);

  ngOnInit(): void {
    const role = this.auth.user()?.role;
    if (role === 'admin') {
      void this.router.navigateByUrl('/admin');
    } else if (role === 'agent') {
      void this.router.navigateByUrl('/agent');
    } else {
      void this.router.navigateByUrl('/etudiant');
    }
  }
}
