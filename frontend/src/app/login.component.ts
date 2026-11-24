import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from './auth.service';
import { errorMessage } from './models';

@Component({selector:'app-login', imports:[ReactiveFormsModule,RouterLink], template:`
<section class="auth-layout panel"><h1>Connexion</h1><p class="muted">Espace des inscriptions universitaires.</p>
@if(error()){<div class="alert">{{error()}}</div>}
<form class="grid" [formGroup]="form" (ngSubmit)="submit()">
<label><span class="req">Email</span><input type="email" formControlName="email"></label>
<label><span class="req">Mot de passe</span><input type="password" formControlName="password"></label>
<button type="submit" [disabled]="loading() || form.invalid">Se connecter</button></form>
<p>Pas encore de compte ? <a routerLink="/inscription">Créer un compte étudiant</a></p>
<div class="demo"><strong>Comptes de démonstration</strong><p>Admin : admin&#64;univ.edu / Admin123!</p><p>Agent : agent&#64;univ.edu / Agent123!</p></div></section>`})
export class LoginComponent {
  private auth=inject(AuthService); private router=inject(Router); private fb=inject(FormBuilder);
  form=this.fb.group({email:['',[Validators.required,Validators.email]],password:['',Validators.required]});
  loading=signal(false); error=signal('');
  submit():void { if(this.form.invalid)return; this.loading.set(true);this.error.set('');const {email,password}=this.form.getRawValue();
    this.auth.login(email!,password!).subscribe({next:()=>{this.loading.set(false);void this.router.navigateByUrl('/');},error:e=>{this.loading.set(false);this.error.set(errorMessage(e));}});
  }
}
