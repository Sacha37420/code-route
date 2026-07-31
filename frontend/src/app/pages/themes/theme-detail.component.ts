import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { Theme, FicheCours } from '../../core/models';

@Component({
  selector: 'app-theme-detail',
  standalone: true,
  imports: [RouterLink, FormsModule],
  templateUrl: './theme-detail.component.html',
  styleUrl: './theme-detail.component.scss',
})
export class ThemeDetailComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);

  themeId = 0;
  theme = signal<Theme | undefined>(undefined);
  fiches = signal<FicheCours[]>([]);
  loading = signal(true);
  isAdmin = signal(false);
  creating = signal(false);
  nouveauTitre = '';

  ngOnInit(): void {
    this.themeId = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getMe().subscribe(me => this.isAdmin.set(me.is_admin));
    this.api.getThemes().subscribe(themes => {
      this.theme.set(themes.find(t => t.id === this.themeId));
    });
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.getFiches(this.themeId).subscribe(fiches => {
      this.fiches.set(fiches);
      this.loading.set(false);
    });
  }

  startCreate(): void { this.creating.set(true); }
  cancelCreate(): void { this.creating.set(false); this.nouveauTitre = ''; }

  submitCreate(): void {
    if (!this.nouveauTitre.trim()) return;
    const fd = new FormData();
    fd.set('theme', String(this.themeId));
    fd.set('titre', this.nouveauTitre.trim());
    fd.set('contenu', '');
    fd.set('ordre', String(this.fiches().length));
    this.api.createFiche(fd).subscribe(() => {
      this.cancelCreate();
      this.load();
    });
  }

  supprimer(fiche: FicheCours): void {
    if (!confirm(`Supprimer la fiche « ${fiche.titre} » ?`)) return;
    this.api.deleteFiche(fiche.id).subscribe(() => this.load());
  }
}
