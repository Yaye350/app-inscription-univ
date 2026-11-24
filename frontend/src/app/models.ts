export interface User {
  id: number;
  email: string;
  role: 'etudiant' | 'agent' | 'admin';
  nom: string;
  prenom: string;
  date_naissance: string | null;
  telephone: string | null;
  adresse: string | null;
  cin: string | null;
}

export interface Campagne {
  id: number;
  nom: string;
  annee: string;
  date_ouverture: string;
  date_cloture: string;
  ouverte: boolean;
}

export interface Formation {
  id: number;
  code: string;
  nom: string;
  niveau: string;
  description: string | null;
}

export interface Piece {
  id: number;
  type_piece: string;
  nom_fichier: string;
  uploaded_at: string | null;
}

export interface HistoriqueItem {
  id: number;
  ancien_statut: string | null;
  nouveau_statut: string;
  motif: string | null;
  created_at: string | null;
  acteur: { id: number; nom: string; prenom: string; role: string } | null;
}

export interface Dossier {
  id: number;
  statut: string;
  commentaire: string | null;
  correction_motif: string | null;
  decision_motif: string | null;
  submitted_at: string | null;
  decided_at: string | null;
  created_at: string | null;
  campagne: Campagne;
  formation: Formation | null;
  etudiant: {
    id: number;
    nom: string;
    prenom: string;
    email: string;
    cin?: string | null;
    telephone?: string | null;
    adresse?: string | null;
    date_naissance?: string | null;
  };
  pieces: Piece[];
  historique?: HistoriqueItem[];
}

export interface Stats {
  total: number;
  par_statut: Record<string, number>;
  par_formation: { formation: string; total: number }[];
}

export const STATUT_LABELS: Record<string, string> = {
  brouillon: 'Brouillon',
  en_attente: 'En attente de vérification',
  a_completer: 'À compléter',
  accepte: 'Accepté',
  rejete: 'Rejeté',
};

export function statutLabel(statut: string): string {
  return STATUT_LABELS[statut] ?? statut;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return '—';
  }
  return new Date(value).toLocaleString('fr-FR');
}

export function errorMessage(err: unknown): string {
  const detail = (err as { error?: { detail?: unknown } }).error?.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  return 'Une erreur est survenue. Vérifiez les champs obligatoires.';
}
