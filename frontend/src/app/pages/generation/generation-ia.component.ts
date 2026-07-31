import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { Difficulte, GenerationIA, GenerationIADetail, QuestionAdmin, Theme } from '../../core/models';

const POLL_INTERVAL_MS = 3000;

@Component({
  selector: 'app-generation-ia',
  standalone: true,
  imports: [FormsModule, DatePipe],
  templateUrl: './generation-ia.component.html',
  styleUrl: './generation-ia.component.scss',
})
export class GenerationIaComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);

  themes = signal<Theme[]>([]);
  generations = signal<GenerationIA[]>([]);
  loading = signal(true);
  lancement = signal(false);

  themeId: number | null = null;
  difficulte: Difficulte = 'facile';
  nombreDemande = 5;

  ouverte = signal<GenerationIADetail | undefined>(undefined);

  private pollHandle?: ReturnType<typeof setInterval>;

  ngOnInit(): void {
    this.api.getThemes().subscribe(themes => this.themes.set(themes));
    this.charger();
    this.pollHandle = setInterval(() => this.pollerEnCours(), POLL_INTERVAL_MS);
  }

  ngOnDestroy(): void {
    if (this.pollHandle) clearInterval(this.pollHandle);
  }

  charger(): void {
    this.loading.set(true);
    this.api.getGenerationsIA().subscribe(generations => {
      this.generations.set(generations);
      this.loading.set(false);
    });
  }

  private pollerEnCours(): void {
    const enCours = this.generations().filter(g => g.statut === 'en_cours');
    if (enCours.length === 0) return;
    this.charger();
    if (this.ouverte() && this.ouverte()!.statut === 'en_cours') {
      this.voir(this.ouverte()!.id);
    }
  }

  lancer(): void {
    if (!this.themeId) return;
    this.lancement.set(true);
    this.api.lancerGenerationIA(this.themeId, this.difficulte, this.nombreDemande).subscribe({
      next: () => {
        this.lancement.set(false);
        this.charger();
      },
      error: () => this.lancement.set(false),
    });
  }

  voir(id: number): void {
    this.api.getStatutGenerationIA(id).subscribe(detail => this.ouverte.set(detail));
  }

  fermer(): void {
    this.ouverte.set(undefined);
  }

  valider(q: QuestionAdmin): void {
    this.api.validerQuestion(q.id).subscribe(() => this.voir(this.ouverte()!.id));
  }

  rejeter(q: QuestionAdmin): void {
    this.api.rejeterQuestion(q.id).subscribe(() => this.voir(this.ouverte()!.id));
  }
}
