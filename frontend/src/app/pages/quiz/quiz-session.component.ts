import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { ProtectedImageComponent } from '../../core/protected-image.component';
import { QuestionQuiz, QuestionReview, QuizSession } from '../../core/models';

type Phase = 'repondre' | 'correction' | 'termine' | 'erreur';

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
  phase = signal<Phase>('repondre');
  erreur = signal('');

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
    if (!this.question || this.selection.size === 0) return;
    const tempsMs = Date.now() - this.questionAfficheeDepuis;
    this.api.repondreQuiz(this.sessionId, this.question.id, Array.from(this.selection), tempsMs)
      .subscribe(res => {
        this.derniereCorrection.set(res);
        this.phase.set('correction');
      });
  }

  suivant(): void {
    if (this.estDerniere) {
      this.terminer();
      return;
    }
    this.index.update(i => i + 1);
    this.selection.clear();
    this.derniereCorrection.set(null);
    this.phase.set('repondre');
    this.questionAfficheeDepuis = Date.now();
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
