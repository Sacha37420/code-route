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

// ── Banque de questions / quiz ─────────────────────────────────────────────

export type TypeQuestion = 'qcm_unique' | 'qcm_multiple' | 'vrai_faux';
export type Difficulte = 'facile' | 'moyen' | 'difficile';
export type OrigineQuestion = 'humaine' | 'ia';
export type StatutQuestion = 'validee' | 'proposee' | 'rejetee';

export interface ReponseAdmin {
  id?: number;
  texte: string;
  correcte: boolean;
  explication: string;
}

export interface QuestionAdmin {
  id: number;
  theme: number;
  theme_nom: string;
  enonce: string;
  type: TypeQuestion;
  difficulte: Difficulte;
  illustration_path: string;
  illustration_credit: string;
  explication_generale: string;
  origine: OrigineQuestion;
  statut: StatutQuestion;
  generation: number | null;
  cree_le: string;
  reponses: ReponseAdmin[];
}

export interface ReponseQuiz {
  id: number;
  texte: string;
}

export interface QuestionQuiz {
  id: number;
  theme: number;
  theme_nom: string;
  enonce: string;
  type: TypeQuestion;
  difficulte: Difficulte;
  illustration_path: string;
  illustration_credit: string;
  reponses: ReponseQuiz[];
}

export interface QuestionReview {
  id: number;
  theme: number;
  theme_nom: string;
  enonce: string;
  type: TypeQuestion;
  difficulte: Difficulte;
  illustration_path: string;
  illustration_credit: string;
  explication_generale: string;
  reponses: ReponseAdmin[];
}

export interface QuizSession {
  id: number;
  date_debut: string;
  date_fin: string | null;
  themes_filtres: string;
  difficulte_filtree: string;
  nombre_questions: number;
  score: number | null;
}

export interface QuizReponseDetail {
  id: number;
  question: QuestionReview;
  reponses_choisies: number[];
  correcte: boolean;
  temps_ms: number | null;
}

export interface QuizSessionDetail extends QuizSession {
  reponses_donnees: QuizReponseDetail[];
}

export interface DemarrerQuizResponse {
  session: QuizSession;
  questions: QuestionQuiz[];
}

export interface RepondreQuizResponse {
  correcte: boolean;
  question: QuestionReview;
}

// ── Mistral (Lot 3) ─────────────────────────────────────────────────────────

export interface ConfigurationMistral {
  actif: boolean;
  has_key: boolean;
  modele: string;
  updated_at: string;
}

export interface PointFaible {
  theme: string;
  taux_reussite: number;
  explication: string;
}

export interface ConseilRevision {
  theme: string;
  priorite: 'haute' | 'moyenne' | 'basse';
  conseil: string;
}

export interface DiagnosticIA {
  points_forts: string[];
  points_faibles: PointFaible[];
  plan_revision: ConseilRevision[];
  fiches_a_relire: string[];
  resume: string;
}

export interface StatsTheme {
  total: number;
  correctes: number;
  taux_reussite: number;
}

export interface AnalyseIA {
  id: number;
  date: string;
  contenu: {
    stats_par_theme: Record<string, StatsTheme>;
    diagnostic?: DiagnosticIA;
  };
  resume_texte: string;
}

// ── Génération IA de questions (Lot 4) ──────────────────────────────────────

export type StatutGeneration = 'en_cours' | 'terminee' | 'erreur';

export interface GenerationIA {
  id: number;
  theme: number;
  theme_nom: string;
  difficulte: Difficulte;
  date: string;
  modele: string;
  nombre_demande: number;
  nombre_genere: number;
  statut: StatutGeneration;
  erreur_message: string;
}

export interface GenerationIADetail extends GenerationIA {
  questions: QuestionAdmin[];
}
