import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  Me, Theme, FicheCours, IllustrationDisponible, SiteExterne,
  QuestionAdmin, QuizSession, QuizSessionDetail, DemarrerQuizResponse, RepondreQuizResponse,
} from './models';

interface EnvWindow {
  __env?: { apiUrl?: string };
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  get base(): string {
    return (window as unknown as EnvWindow).__env?.apiUrl
      ?? 'http://localhost:8096';
  }

  getMe(): Observable<Me> {
    return this.http.get<Me>(`${this.base}/api/me/`);
  }

  // ── Thèmes ─────────────────────────────────────────────────────────────
  getThemes(): Observable<Theme[]> {
    return this.http.get<Theme[]>(`${this.base}/api/themes/`);
  }
  createTheme(data: Partial<Theme>): Observable<Theme> {
    return this.http.post<Theme>(`${this.base}/api/themes/`, data);
  }
  updateTheme(id: number, data: Partial<Theme>): Observable<Theme> {
    return this.http.patch<Theme>(`${this.base}/api/themes/${id}/`, data);
  }
  deleteTheme(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/api/themes/${id}/`);
  }

  // ── Fiches de cours ────────────────────────────────────────────────────
  getFiches(themeId?: number): Observable<FicheCours[]> {
    const url = themeId ? `${this.base}/api/fiches/?theme=${themeId}` : `${this.base}/api/fiches/`;
    return this.http.get<FicheCours[]>(url);
  }
  getFiche(id: number): Observable<FicheCours> {
    return this.http.get<FicheCours>(`${this.base}/api/fiches/${id}/`);
  }
  createFiche(data: FormData): Observable<FicheCours> {
    return this.http.post<FicheCours>(`${this.base}/api/fiches/`, data);
  }
  updateFiche(id: number, data: FormData): Observable<FicheCours> {
    return this.http.patch<FicheCours>(`${this.base}/api/fiches/${id}/`, data);
  }
  deleteFiche(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/api/fiches/${id}/`);
  }
  ficheIllustrationUrl(id: number): string {
    return `${this.base}/api/fiches/${id}/illustration/`;
  }

  getIllustrationsDisponibles(): Observable<IllustrationDisponible[]> {
    return this.http.get<IllustrationDisponible[]>(`${this.base}/api/illustrations-disponibles/`);
  }

  // ── Sites externes ─────────────────────────────────────────────────────
  getSitesExternes(): Observable<SiteExterne[]> {
    return this.http.get<SiteExterne[]>(`${this.base}/api/sites-externes/`);
  }
  createSiteExterne(data: Partial<SiteExterne>): Observable<SiteExterne> {
    return this.http.post<SiteExterne>(`${this.base}/api/sites-externes/`, data);
  }
  updateSiteExterne(id: number, data: Partial<SiteExterne>): Observable<SiteExterne> {
    return this.http.patch<SiteExterne>(`${this.base}/api/sites-externes/${id}/`, data);
  }
  deleteSiteExterne(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/api/sites-externes/${id}/`);
  }

  // ── Banque de questions (admin) ────────────────────────────────────────
  getQuestions(params: { theme?: number; statut?: string } = {}): Observable<QuestionAdmin[]> {
    const qs = new URLSearchParams();
    if (params.theme) qs.set('theme', String(params.theme));
    if (params.statut) qs.set('statut', params.statut);
    const suffix = qs.toString() ? `?${qs.toString()}` : '';
    return this.http.get<QuestionAdmin[]>(`${this.base}/api/questions/${suffix}`);
  }
  getQuestion(id: number): Observable<QuestionAdmin> {
    return this.http.get<QuestionAdmin>(`${this.base}/api/questions/${id}/`);
  }
  createQuestion(data: unknown): Observable<QuestionAdmin> {
    return this.http.post<QuestionAdmin>(`${this.base}/api/questions/`, data);
  }
  updateQuestion(id: number, data: unknown): Observable<QuestionAdmin> {
    return this.http.patch<QuestionAdmin>(`${this.base}/api/questions/${id}/`, data);
  }
  deleteQuestion(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/api/questions/${id}/`);
  }
  validerQuestion(id: number): Observable<QuestionAdmin> {
    return this.http.post<QuestionAdmin>(`${this.base}/api/questions/${id}/valider/`, {});
  }
  rejeterQuestion(id: number): Observable<QuestionAdmin> {
    return this.http.post<QuestionAdmin>(`${this.base}/api/questions/${id}/rejeter/`, {});
  }
  questionIllustrationUrl(id: number): string {
    return `${this.base}/api/questions/${id}/illustration/`;
  }

  // ── Moteur de quiz ─────────────────────────────────────────────────────
  demarrerQuiz(themes: number[], difficulte: string, nombreQuestions: number): Observable<DemarrerQuizResponse> {
    return this.http.post<DemarrerQuizResponse>(`${this.base}/api/quiz/demarrer/`, {
      themes, difficulte, nombre_questions: nombreQuestions,
    });
  }
  repondreQuiz(sessionId: number, questionId: number, reponsesChoisies: number[], tempsMs: number): Observable<RepondreQuizResponse> {
    return this.http.post<RepondreQuizResponse>(`${this.base}/api/quiz/${sessionId}/repondre/`, {
      question: questionId, reponses_choisies: reponsesChoisies, temps_ms: tempsMs,
    });
  }
  terminerQuiz(sessionId: number): Observable<QuizSession> {
    return this.http.post<QuizSession>(`${this.base}/api/quiz/${sessionId}/terminer/`, {});
  }
  getHistorique(): Observable<QuizSession[]> {
    return this.http.get<QuizSession[]>(`${this.base}/api/quiz/historique/`);
  }
  getSessionDetail(sessionId: number): Observable<QuizSessionDetail> {
    return this.http.get<QuizSessionDetail>(`${this.base}/api/quiz/${sessionId}/`);
  }
}
