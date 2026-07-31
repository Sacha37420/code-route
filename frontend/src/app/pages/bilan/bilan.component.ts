import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';
import { AnalyseIA, Theme } from '../../core/models';

@Component({
  selector: 'app-bilan',
  standalone: true,
  imports: [DatePipe, RouterLink],
  templateUrl: './bilan.component.html',
  styleUrl: './bilan.component.scss',
})
export class BilanComponent implements OnInit {
  private api = inject(ApiService);

  analyse = signal<AnalyseIA | undefined>(undefined);
  themes = signal<Theme[]>([]);
  loading = signal(true);
  aucunHistorique = signal(false);

  ngOnInit(): void {
    this.api.getThemes().subscribe(themes => this.themes.set(themes));
    this.api.getMonBilan().subscribe({
      next: (analyse) => {
        this.analyse.set(analyse);
        this.loading.set(false);
      },
      error: (err) => {
        if (err.status === 404) this.aucunHistorique.set(true);
        this.loading.set(false);
      },
    });
  }

  themesEntries(): [string, { total: number; correctes: number; taux_reussite: number }][] {
    const stats = this.analyse()?.contenu.stats_par_theme ?? {};
    return Object.entries(stats).sort((a, b) => a[1].taux_reussite - b[1].taux_reussite);
  }

  themeIdParNom(nom: string): number | undefined {
    return this.themes().find(t => t.nom === nom)?.id;
  }

  prioriteClass(p: string): string {
    return `priorite-${p}`;
  }
}
