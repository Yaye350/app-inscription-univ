import { Routes } from '@angular/router';
import { authGuard, roleGuard } from './auth.guard';
import { LoginComponent } from './login.component';
import { RegisterComponent } from './register.component';
import { HomeComponent } from './home.component';
import { ProfilComponent } from './profil.component';
import { WorkspaceComponent } from './workspace.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'inscription', component: RegisterComponent },
  { path: 'profil', component: ProfilComponent, canActivate: [authGuard] },
  { path: 'etudiant', component: WorkspaceComponent, canActivate: [authGuard, roleGuard], data: { roles: ['etudiant'] } },
  { path: 'agent', component: WorkspaceComponent, canActivate: [authGuard, roleGuard], data: { roles: ['agent'] } },
  { path: 'admin', component: WorkspaceComponent, canActivate: [authGuard, roleGuard], data: { roles: ['admin'] } },
  { path: '', component: HomeComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: '' },
];
