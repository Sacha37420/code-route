import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { QuizSession } from '../../core/models';

@Component({
  selector: 'app-historique-list',
  standalone: true,
  imports: [RouterLink, DatePipe],
  templateUrl: './historique-list.component.html',
  styleUrl: './historique-list.component.scss',
})
export class HistoriqueListComponent implements OnInit {
  private api = inject(ApiService);

  sessions = signal<QuizSession[]>([]);
  loading = signal(true);

  ngOnInit(): void {
    this.api.getHistorique().subscribe(sessions => {
      this.sessions.set(sessions);
      this.loading.set(false);
    });
  }

  pourcentage(session: QuizSession): number {
    if (session.score === null || session.nombre_questions === 0) return 0;
    return Math.round((100 * session.score) / session.nombre_questions);
  }
}
