import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ApiService } from './api.service';
import { AuthService } from './auth.service';
import { Campagne, Dossier, Formation, Stats, User, errorMessage, formatDate, statutLabel } from './models';

@Component({
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="panel">
      <h1>{{ title }}</h1><p class="muted">{{ subtitle }}</p>
      @if (error()) { <div class="alert">{{ error() }}</div> }
      @if (notice()) { <div class="alert ok">{{ notice() }}</div> }
    </section>

    @if (role === 'etudiant') {
      <section class="panel">
        <h2>Mon profil</h2>
        <form class="grid two" [formGroup]="profile" (ngSubmit)="saveProfile()">
          <label><span class="req">Nom</span><input formControlName="nom"></label>
          <label><span class="req">Prénom</span><input formControlName="prenom"></label>
          <label>CIN<input formControlName="cin"></label><label>Téléphone<input formControlName="telephone"></label>
          <label>Date de naissance<input type="date" formControlName="date_naissance"></label>
          <label>Adresse<input formControlName="adresse"></label>
          <button [disabled]="profile.invalid">Enregistrer mon profil</button>
        </form>
      </section>
      <section class="panel">
        <h2>Créer un dossier</h2>
        <form class="grid two" [formGroup]="newDossier" (ngSubmit)="createDossier()">
          <label class="req">Campagne<select formControlName="campagne_id"><option value="">Choisir une campagne ouverte</option>@for (c of campagnes; track c.id) { @if (c.ouverte) { <option [value]="c.id">{{ c.nom }}</option> } }</select></label>
          <label class="req">Formation<select formControlName="formation_id"><option value="">Choisir une formation</option>@for (f of formations; track f.id) { <option [value]="f.id">{{ f.nom }}</option> }</select></label>
          <label>Commentaire<textarea formControlName="commentaire"></textarea></label><button [disabled]="newDossier.invalid">Créer le brouillon</button>
        </form>
      </section>
      @for (d of dossiers; track d.id) {
        <section class="panel">
          <div class="row"><h2>Dossier #{{ d.id }} · {{ d.formation?.nom }}</h2><span class="badge" [class]="'badge '+d.statut">{{ label(d.statut) }}</span></div>
          <p>{{ d.campagne.nom }}</p>
          @if (d.correction_motif) { <div class="alert info">Complément demandé : {{ d.correction_motif }}</div> }
          @if (editable(d)) {
            <form class="grid two" [formGroup]="editForm(d.id)" (ngSubmit)="saveDossier(d)">
              <label class="req">Formation<select formControlName="formation_id">@for (f of formations; track f.id) { <option [value]="f.id">{{ f.nom }}</option> }</select></label>
              <label>Commentaire<textarea formControlName="commentaire"></textarea></label>
              <button [disabled]="editForm(d.id).invalid">Enregistrer les modifications</button>
            </form>
            <div class="grid two upload-row">
              @for (kind of pieceKinds; track kind) { <label>{{ kind }}<input type="file" accept=".pdf,.jpg,.jpeg,.png" (change)="upload(d.id, kind, $event)"></label> }
            </div>
            <div class="actions">@if (d.pieces.length) { <button (click)="submit(d)">Soumettre le dossier</button> }</div>
          }
          @if (d.pieces.length) { <p class="muted">Pièces : @for (p of d.pieces; track p.id) { <button class="link-button" (click)="download(d.id,p.id,p.nom_fichier)">{{ p.type_piece }} · {{ p.nom_fichier }}</button> }</p> }
          @if (d.historique?.length) { <h3>Historique</h3><ul class="timeline">@for (h of d.historique; track h.id) { <li><strong>{{ label(h.nouveau_statut) }}</strong> · {{ fmt(h.created_at) }} @if (h.motif) { — {{ h.motif }} }</li> }</ul> }
          @if (d.decision_motif) { <p>Motif de décision : {{ d.decision_motif }}</p> }
        </section>
      } @empty { <section class="panel muted">Aucun dossier pour le moment.</section> }
    }

    @if (role === 'agent') {
      <section class="panel"><h2>File de traitement</h2>
        <form class="filters" [formGroup]="filters" (ngSubmit)="loadDossiers()">
          <label>Statut<select formControlName="statut"><option value="">Tous</option><option value="en_attente">En attente</option><option value="a_completer">À compléter</option><option value="accepte">Accepté</option><option value="rejete">Rejeté</option></select></label>
          <label>Recherche<input formControlName="q" placeholder="Nom, prénom ou email"></label><button>Filtrer</button>
        </form>
      </section>
      @for (d of dossiers; track d.id) { <section class="panel"><div class="row"><h2>#{{d.id}} · {{d.etudiant.prenom}} {{d.etudiant.nom}}</h2><span class="badge" [class]="'badge '+d.statut">{{label(d.statut)}}</span></div>
        <p>{{d.etudiant.email}} · {{d.formation?.nom}} · CIN {{d.etudiant.cin || 'non renseignée'}}</p>
        <p>Pièces : @for (p of d.pieces; track p.id) { <button class="link-button" (click)="download(d.id,p.id,p.nom_fichier)">{{p.type_piece}} · {{p.nom_fichier}}</button> }</p>
        @if (d.statut === 'en_attente') { <form class="actions" [formGroup]="motifForm(d.id)">
          <input formControlName="motif" placeholder="Motif obligatoire pour la décision">
          <button class="warn" [disabled]="motifForm(d.id).invalid" (click)="complement(d)">Demander un complément</button>
          <button class="ok" (click)="accept(d)">Accepter</button>
          <button class="danger" [disabled]="motifForm(d.id).invalid" (click)="reject(d)">Rejeter</button>
        </form> }
        @if (d.historique?.length) { <details><summary>Historique du dossier</summary><ul class="timeline">@for(h of d.historique;track h.id){<li>{{label(h.nouveau_statut)}} · {{fmt(h.created_at)}} · {{h.motif}}</li>}</ul></details> }
      </section> } @empty { <section class="panel muted">Aucun dossier ne correspond aux filtres.</section> }
    }

    @if (role === 'admin') {
      @if (stats) { <section class="panel"><h2>Statistiques</h2><div class="cards"><div class="stat"><strong>{{stats.total}}</strong>Total dossiers</div>@for (entry of statEntries(); track entry[0]) { <div class="stat"><strong>{{entry[1]}}</strong>{{label(entry[0])}}</div> }</div><h3>Par formation</h3><p>@for (f of stats.par_formation; track f.formation) { <span class="badge">{{f.formation}} : {{f.total}}</span> }</p></section> }
      <section class="panel"><h2>Campagnes</h2><form class="grid two" [formGroup]="campaignForm" (ngSubmit)="saveCampaign()"><label class="req">Nom<input formControlName="nom"></label><label class="req">Année<input formControlName="annee"></label><label class="req">Ouverture<input type="date" formControlName="date_ouverture"></label><label class="req">Clôture<input type="date" formControlName="date_cloture"></label><button [disabled]="campaignForm.invalid">{{campaignEditingId ? 'Enregistrer la campagne' : 'Créer la campagne'}}</button>@if(campaignEditingId){<button type="button" class="secondary" (click)="cancelCampaignEdit()">Annuler</button>}</form>
        <table><thead><tr><th>Campagne</th><th>Période</th><th>État</th><th></th></tr></thead><tbody>@for(c of campagnes;track c.id){<tr><td>{{c.nom}}</td><td>{{c.date_ouverture}} – {{c.date_cloture}}</td><td>{{c.ouverte?'Ouverte':'Fermée'}}</td><td><button class="secondary" (click)="editCampaign(c)">Modifier</button> <button class="danger" (click)="deleteCampaign(c.id)">Supprimer</button></td></tr>}</tbody></table>
      </section>
      <section class="panel"><h2>Formations</h2><form class="grid two" [formGroup]="formationForm" (ngSubmit)="saveFormation()"><label class="req">Code<input formControlName="code"></label><label class="req">Nom<input formControlName="nom"></label><label class="req">Niveau<input formControlName="niveau"></label><label>Description<input formControlName="description"></label><button [disabled]="formationForm.invalid">{{formationEditingId ? 'Enregistrer la formation' : 'Créer la formation'}}</button>@if(formationEditingId){<button type="button" class="secondary" (click)="cancelFormationEdit()">Annuler</button>}</form><table><thead><tr><th>Code</th><th>Formation</th><th></th></tr></thead><tbody>@for(f of formations;track f.id){<tr><td>{{f.code}}</td><td>{{f.nom}} · {{f.niveau}}</td><td><button class="secondary" (click)="editFormation(f)">Modifier</button> <button class="danger" (click)="deleteFormation(f.id)">Supprimer</button></td></tr>}</tbody></table></section>
      <section class="panel"><h2>Utilisateurs et export</h2><button (click)="exportCsv()">Exporter les dossiers CSV</button><table><thead><tr><th>Utilisateur</th><th>Email</th><th>Rôle</th></tr></thead><tbody>@for(u of users;track u.id){<tr><td>{{u.prenom}} {{u.nom}}</td><td>{{u.email}}</td><td><select [value]="u.role" (change)="changeRole(u,$event)"><option value="etudiant">Étudiant</option><option value="agent">Agent</option><option value="admin">Admin</option></select></td></tr>}</tbody></table></section>
      <section class="panel"><h2>Recherche dossiers</h2><form class="filters" [formGroup]="filters" (ngSubmit)="loadDossiers()"><label>Statut<select formControlName="statut"><option value="">Tous</option><option value="brouillon">Brouillon</option><option value="en_attente">En attente</option><option value="a_completer">À compléter</option><option value="accepte">Accepté</option><option value="rejete">Rejeté</option></select></label><label>Recherche<input formControlName="q"></label><button>Rechercher</button></form><table><thead><tr><th>Étudiant</th><th>Formation</th><th>Campagne</th><th>Statut</th></tr></thead><tbody>@for(d of dossiers;track d.id){<tr><td>{{d.etudiant.prenom}} {{d.etudiant.nom}}<br>{{d.etudiant.email}}</td><td>{{d.formation?.nom}}</td><td>{{d.campagne.nom}}</td><td>{{label(d.statut)}}</td></tr>}</tbody></table></section>
    }
  `,
})
export class WorkspaceComponent implements OnInit {
  private api = inject(ApiService); private auth = inject(AuthService); private fb = inject(FormBuilder);
  role = this.auth.user()?.role ?? 'etudiant';
  title = this.role === 'etudiant' ? 'Mon espace étudiant' : this.role === 'agent' ? 'Espace agent' : 'Administration';
  subtitle = this.role === 'etudiant' ? 'Complétez votre profil et suivez vos inscriptions.' : this.role === 'agent' ? 'Examinez les dossiers et consignez chaque décision.' : 'Gérez les référentiels et suivez les inscriptions.';
  dossiers: Dossier[] = []; campagnes: Campagne[] = []; formations: Formation[] = []; users: User[] = []; stats: Stats | null = null;
  error = signal(''); notice = signal(''); motifs: Record<number, ReturnType<FormBuilder['group']>> = {}; editForms: Record<number, ReturnType<FormBuilder['group']>> = {};
  campaignEditingId: number | null = null; formationEditingId: number | null = null;
  pieceKinds = ['cin', 'bac', 'photo'];
  profile = this.fb.group({nom: [this.auth.user()?.nom ?? '', Validators.required], prenom: [this.auth.user()?.prenom ?? '', Validators.required], cin: [this.auth.user()?.cin ?? '', Validators.required], telephone: [this.auth.user()?.telephone ?? ''], adresse: [this.auth.user()?.adresse ?? ''], date_naissance: [this.auth.user()?.date_naissance ?? '', Validators.required]});
  newDossier = this.fb.group({campagne_id: ['', Validators.required], formation_id: ['', Validators.required], commentaire: ['']});
  filters = this.fb.group({statut: [''], q: ['']});
  campaignForm = this.fb.group({nom: ['', Validators.required], annee: ['', Validators.required], date_ouverture: ['', Validators.required], date_cloture: ['', Validators.required]});
  formationForm = this.fb.group({code: ['', Validators.required], nom: ['', Validators.required], niveau: ['', Validators.required], description: ['']});
  ngOnInit(): void { this.loadReference(); this.loadDossiers(); if (this.role === 'admin') { this.api.stats().subscribe(v => this.stats = v); this.api.users().subscribe(v => this.users = v); } }
  loadReference(): void { this.api.campagnes().subscribe(v => this.campagnes = v); this.api.formations().subscribe(v => this.formations = v); }
  loadDossiers(): void { const f = this.filters.getRawValue(); this.api.dossiers({statut: f.statut ?? '', q: f.q ?? ''}).subscribe({next: v => {this.dossiers = v; for (const d of v) { if (!this.motifs[d.id]) this.motifs[d.id] = this.fb.group({motif: ['', [Validators.required, Validators.maxLength(2000)]]}); if (!this.editForms[d.id]) this.editForms[d.id] = this.fb.group({formation_id: [String(d.formation?.id ?? ''), Validators.required], commentaire: [d.commentaire ?? '']}); this.api.dossier(d.id).subscribe({next: detail => {const index=this.dossiers.findIndex(item=>item.id===detail.id);if(index>=0)this.dossiers[index]=detail;},error:e=>this.fail(e)});}}, error: e => this.fail(e)}); }
  saveProfile(): void { if (this.profile.invalid) return; this.api.updateMe(this.profile.getRawValue() as Partial<User>).subscribe({next: u => {this.auth.updateStoredUser(u);this.ok('Profil enregistré.');},error:e=>this.fail(e)}); }
  createDossier(): void { if(this.newDossier.invalid)return; const v=this.newDossier.getRawValue(); this.api.createDossier({campagne_id:Number(v.campagne_id),formation_id:Number(v.formation_id),commentaire:v.commentaire||undefined}).subscribe({next:()=>{this.ok('Brouillon créé.');this.newDossier.reset();this.loadDossiers();},error:e=>this.fail(e)}); }
  editForm(id:number){return this.editForms[id];}
  saveDossier(d:Dossier):void{if(this.editForms[d.id].invalid)return;const v=this.editForms[d.id].getRawValue();this.api.updateDossier(d.id,{formation_id:Number(v.formation_id),commentaire:v.commentaire??''}).subscribe({next:()=>{this.ok('Dossier modifié.');this.loadDossiers();},error:e=>this.fail(e)});}
  editable(d:Dossier):boolean{return this.role==='etudiant'&&['brouillon','a_completer'].includes(d.statut);}
  upload(id:number,kind:string,event:Event):void{const file=(event.target as HTMLInputElement).files?.[0];if(!file)return;this.api.uploadPiece(id,kind,file).subscribe({next:()=>{this.ok(`Pièce ${kind} déposée.`);this.loadDossiers();},error:e=>this.fail(e)});}
  submit(d:Dossier):void{this.api.submit(d.id).subscribe({next:()=>{this.ok('Dossier soumis.');this.loadDossiers();},error:e=>this.fail(e)});}
  download(d:number,p:number,name:string):void{this.api.downloadPiece(d,p).subscribe({next:b=>{const url=URL.createObjectURL(b);const a=document.createElement('a');a.href=url;a.download=name;a.click();URL.revokeObjectURL(url);},error:e=>this.fail(e)});}
  complement(d:Dossier):void{const motif=this.motifs[d.id].value.motif;this.api.complement(d.id,motif).subscribe({next:()=>{this.ok('Complément demandé.');this.loadDossiers();},error:e=>this.fail(e)});}
  accept(d:Dossier):void{this.api.accept(d.id,this.motifs[d.id].value.motif).subscribe({next:()=>{this.ok('Dossier accepté.');this.loadDossiers();},error:e=>this.fail(e)});}
  reject(d:Dossier):void{this.api.reject(d.id,this.motifs[d.id].value.motif).subscribe({next:()=>{this.ok('Dossier rejeté.');this.loadDossiers();},error:e=>this.fail(e)});}
  saveCampaign():void{if(this.campaignForm.invalid)return;this.api.saveCampagne(this.campaignForm.getRawValue() as Omit<Campagne,'id'|'ouverte'>,this.campaignEditingId??undefined).subscribe({next:()=>{this.ok(this.campaignEditingId?'Campagne modifiée.':'Campagne créée.');this.campaignEditingId=null;this.campaignForm.reset();this.loadReference();},error:e=>this.fail(e)});}
  editCampaign(c:Campagne):void{this.campaignEditingId=c.id;this.campaignForm.patchValue({nom:c.nom,annee:c.annee,date_ouverture:c.date_ouverture,date_cloture:c.date_cloture});}
  cancelCampaignEdit():void{this.campaignEditingId=null;this.campaignForm.reset();}
  deleteCampaign(id:number):void{this.api.deleteCampagne(id).subscribe({next:()=>{this.ok('Campagne supprimée.');this.loadReference();},error:e=>this.fail(e)});}
  saveFormation():void{if(this.formationForm.invalid)return;this.api.saveFormation(this.formationForm.getRawValue() as Omit<Formation,'id'>,this.formationEditingId??undefined).subscribe({next:()=>{this.ok(this.formationEditingId?'Formation modifiée.':'Formation créée.');this.formationEditingId=null;this.formationForm.reset();this.loadReference();},error:e=>this.fail(e)});}
  editFormation(f:Formation):void{this.formationEditingId=f.id;this.formationForm.patchValue({code:f.code,nom:f.nom,niveau:f.niveau,description:f.description??''});}
  deleteFormation(id:number):void{this.api.deleteFormation(id).subscribe({next:()=>{this.ok('Formation supprimée.');this.loadReference();},error:e=>this.fail(e)});}
  cancelFormationEdit():void{this.formationEditingId=null;this.formationForm.reset();}
  changeRole(u:User,e:Event):void{const role=(e.target as HTMLSelectElement).value;this.api.updateRole(u.id,role).subscribe({next:updated=>{u.role=updated.role;this.ok('Rôle mis à jour.');},error:err=>this.fail(err)});}
  exportCsv():void{this.api.exportCsv({}).subscribe({next:b=>{const url=URL.createObjectURL(b);const a=document.createElement('a');a.href=url;a.download='dossiers.csv';a.click();URL.revokeObjectURL(url);},error:e=>this.fail(e)});}
  statEntries():[string,number][]{return Object.entries(this.stats?.par_statut??{});}
  motifForm(id:number){return this.motifs[id];}
  label=statutLabel; fmt=formatDate;
  private ok(value:string):void{this.error.set('');this.notice.set(value);}
  private fail(e:unknown):void{this.notice.set('');this.error.set(errorMessage(e));}
}
