import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { ProtectedImageComponent } from '../../core/protected-image.component';
import { QuestionQuiz, QuestionReview, QuizSession } from '../../core/models';

type Phase = 'chargement' | 'repondre' | 'correction' | 'termine' | 'erreur';

@Component({
  selector: 'app-quiz-session',
  standalone: true,
  imports: [RouterLink, ProtectedImageComponent],
  templateUrl: './quiz-session.component.html',
  styleUrl: './quiz-session.component.scss',
})
export class QuizSessionComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  sessionId = 0;
  questions: QuestionQuiz[] = [];
  index = signal(0);
  phase = signal<Phase>('chargement');
  erreur = signal('');
  /** Échec de l'envoi d'une réponse — affiché sous le bouton « Valider ». */
  erreurEnvoi = signal('');
  /** Une réponse est en cours d'envoi : empêche un second envoi (double clic). */
  envoi = signal(false);

  selection = new Set<number>();
  derniereCorrection = signal<{ correcte: boolean; question: QuestionReview } | null>(null);
  sessionFinale = signal<QuizSession | null>(null);

  private questionAfficheeDepuis = Date.now();

  get question(): QuestionQuiz | undefined {
    return this.questions[this.index()];
  }

  get estDerniere(): boolean {
    return this.index() >= this.questions.length - 1;
  }

  ngOnInit(): void {
    this.sessionId = Number(this.route.snapshot.paramMap.get('id'));
    const raw = sessionStorage.getItem(`quiz-questions-${this.sessionId}`);
    if (!raw) {
      this.phase.set('erreur');
      this.erreur.set("Session introuvable (page rechargée trop tard, ou lien direct sans démarrage). Redémarrez un quiz.");
      return;
    }
    this.questions = JSON.parse(raw);
    // Page rechargée en cours de quiz : on reprend là où la session en est,
    // pas à la question 1 (une question ne reçoit qu'une réponse — 409 sinon).
    this.reprendre(true);
  }

  /** Place le quiz sur la première question sans réponse, d'après l'état de la
   *  session côté serveur. Toutes répondues : écran de fin, comme le parcours
   *  normal. `initial` : à l'ouverture, un échec de lecture retombe sur la
   *  question 1 (comportement d'origine) plutôt que de bloquer le quiz. */
  private reprendre(initial = false): void {
    this.api.getSessionDetail(this.sessionId).subscribe({
      next: detail => {
        if (detail.date_fin !== null) {
          sessionStorage.removeItem(`quiz-questions-${this.sessionId}`);
          this.sessionFinale.set(detail);
          this.phase.set('termine');
          return;
        }
        // Même règle que le backend (`deja_repondue`) : une réponse enregistrée
        // porte un choix ou un temps.
        const repondues = new Set<number>(
          detail.reponses_donnees
            .filter(r => r.reponses_choisies.length > 0 || r.temps_ms !== null)
            .map(r => r.question.id),
        );
        const prochaine = this.questions.findIndex(q => !repondues.has(q.id));
        if (prochaine === -1) {
          this.terminer();
          return;
        }
        this.afficherQuestion(prochaine);
      },
      error: () => {
        if (initial) {
          this.afficherQuestion(0);
        } else {
          this.erreurEnvoi.set("Impossible de relire l'état du quiz. Rechargez la page.");
        }
      },
    });
  }

  private afficherQuestion(index: number): void {
    this.index.set(index);
    this.selection.clear();
    this.derniereCorrection.set(null);
    this.erreurEnvoi.set('');
    this.phase.set('repondre');
    this.questionAfficheeDepuis = Date.now();
  }

  isSelected(reponseId: number): boolean {
    return this.selection.has(reponseId);
  }

  choisirUnique(reponseId: number): void {
    this.selection.clear();
    this.selection.add(reponseId);
  }

  toggleMultiple(reponseId: number): void {
    if (this.selection.has(reponseId)) this.selection.delete(reponseId);
    else this.selection.add(reponseId);
  }

  valider(): void {
    if (!this.question || this.selection.size === 0 || this.envoi()) return;
    const tempsMs = Date.now() - this.questionAfficheeDepuis;
    this.envoi.set(true);
    this.erreurEnvoi.set('');
    this.api.repondreQuiz(this.sessionId, this.question.id, Array.from(this.selection), tempsMs)
      .subscribe({
        next: res => {
          this.envoi.set(false);
          this.derniereCorrection.set(res);
          this.phase.set('correction');
        },
        error: (err: HttpErrorResponse) => {
          this.envoi.set(false);
          if (err.status === 409) {
            // Question déjà répondue dans cette session (autre onglet, page
            // rechargée) : la première réponse compte, on passe à la suite.
            this.reprendre();
            return;
          }
          const detail: unknown = err.error?.detail;
          this.erreurEnvoi.set(
            typeof detail === 'string' && detail
              ? detail
              : "La réponse n'a pas pu être enregistrée. Vérifiez la connexion et réessayez.",
          );
        },
      });
  }

  suivant(): void {
    if (this.estDerniere) {
      this.terminer();
      return;
    }
    this.afficherQuestion(this.index() + 1);
  }

  private terminer(): void {
    this.api.terminerQuiz(this.sessionId).subscribe(session => {
      sessionStorage.removeItem(`quiz-questions-${this.sessionId}`);
      this.sessionFinale.set(session);
      this.phase.set('termine');
    });
  }

  voirCorrection(): void {
    this.router.navigate(['/historique', this.sessionId]);
  }

  illustrationUrl(): string {
    return this.api.questionIllustrationUrl(this.question!.id);
  }
}
