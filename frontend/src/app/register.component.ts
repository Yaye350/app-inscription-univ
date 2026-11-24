import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from './auth.service';
import { errorMessage } from './models';

@Component({selector:'app-register', imports:[ReactiveFormsModule,RouterLink], template:`
<section class="auth-layout panel"><h1>Inscription étudiant</h1><p class="muted">Créez votre compte pour constituer un dossier.</p>
@if(error()){<div class="alert">{{error()}}</div>}
<form class="grid" [formGroup]="form" (ngSubmit)="submit()">
<label><span class="req">Prénom</span><input formControlName="prenom"></label><label><span class="req">Nom</span><input formControlName="nom"></label>
<label><span class="req">Email</span><input type="email" formControlName="email"></label><label><span class="req">Mot de passe (8 caractères minimum)</span><input type="password" formControlName="password"></label>
<button type="submit" [disabled]="loading() || form.invalid">Créer le compte</button></form>
<p>Déjà inscrit ? <a routerLink="/login">Se connecter</a></p></section>`})
export class RegisterComponent {
  private auth=inject(AuthService);private router=inject(Router);private fb=inject(FormBuilder);
  form=this.fb.group({prenom:['',[Validators.required,Validators.maxLength(100)]],nom:['',[Validators.required,Validators.maxLength(100)]],email:['',[Validators.required,Validators.email]],password:['',[Validators.required,Validators.minLength(8),Validators.maxLength(128)]]});
  loading=signal(false);error=signal('');
  submit():void{if(this.form.invalid)return;this.loading.set(true);this.error.set('');const v=this.form.getRawValue();
    this.auth.register({prenom:v.prenom!,nom:v.nom!,email:v.email!,password:v.password!}).subscribe({next:()=>this.auth.login(v.email!,v.password!).subscribe({next:()=>void this.router.navigateByUrl('/'),error:e=>{this.loading.set(false);this.error.set(errorMessage(e));}}),error:e=>{this.loading.set(false);this.error.set(errorMessage(e));}});
  }
}
