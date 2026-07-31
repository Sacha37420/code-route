import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { Theme } from '../../core/models';

@Component({
  selector: 'app-quiz-demarrer',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './quiz-demarrer.component.html',
  styleUrl: './quiz-demarrer.component.scss',
})
export class QuizDemarrerComponent implements OnInit {
  private api = inject(ApiService);
  private router = inject(Router);

  themes = signal<Theme[]>([]);
  themesChoisis = new Set<number>();
  difficulte = '';
  nombreQuestions = 10;
  demarrage = signal(false);
  erreur = signal('');

  ngOnInit(): void {
    this.api.getThemes().subscribe(themes => this.themes.set(themes));
  }

  toggleTheme(id: number): void {
    if (this.themesChoisis.has(id)) this.themesChoisis.delete(id);
    else this.themesChoisis.add(id);
  }

  demarrer(): void {
    this.demarrage.set(true);
    this.erreur.set('');
    this.api.demarrerQuiz(
      Array.from(this.themesChoisis), this.difficulte, this.nombreQuestions,
    ).subscribe({
      next: (res) => {
        // sessionStorage plutôt que le seul router state : survit à un F5 sur
        // la page de quiz (le router state est perdu au rechargement).
        sessionStorage.setItem(`quiz-questions-${res.session.id}`, JSON.stringify(res.questions));
        this.router.navigate(['/quiz', res.session.id]);
      },
      error: (err) => {
        this.demarrage.set(false);
        this.erreur.set(err.error?.detail ?? "Impossible de démarrer le quiz.");
      },
    });
  }
}
