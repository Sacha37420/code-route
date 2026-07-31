export interface Me {
  email: string;
  username: string;
  groups: string[];
  is_admin: boolean;
}

export interface Theme {
  id: number;
  nom: string;
  description: string;
  ordre: number;
}

export interface FicheCours {
  id: number;
  theme: number;
  theme_nom: string;
  titre: string;
  contenu: string;
  ordre: number;
  illustration_path: string;
  illustration_credit: string;
}

export interface IllustrationDisponible {
  relative_path: string;
  nom: string;
  credit: string;
}

export type StatutSiteExterne = 'gratuit' | 'freemium' | 'payant';

export interface SiteExterne {
  id: number;
  nom: string;
  url: string;
  statut: StatutSiteExterne;
  offre_resume: string;
  date_verification: string | null;
  ordre: number;
}
