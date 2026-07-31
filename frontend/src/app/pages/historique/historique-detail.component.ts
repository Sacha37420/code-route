import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { ProtectedImageComponent } from '../../core/protected-image.component';
import { QuizSessionDetail } from '../../core/models';

@Component({
  selector: 'app-historique-detail',
  standalone: true,
  imports: [RouterLink, DatePipe, ProtectedImageComponent],
  templateUrl: './historique-detail.component.html',
  styleUrl: './historique-detail.component.scss',
})
export class HistoriqueDetailComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  session = signal<QuizSessionDetail | undefined>(undefined);
  loading = signal(true);

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getSessionDetail(id).subscribe(session => {
      this.session.set(session);
      this.loading.set(false);
    });
  }

  illustrationUrl(questionId: number): string {
    return this.api.questionIllustrationUrl(questionId);
  }
}
