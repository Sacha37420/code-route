import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { Theme } from '../../core/models';

@Component({
  selector: 'app-theme-list',
  standalone: true,
  imports: [RouterLink, FormsModule],
  templateUrl: './theme-list.component.html',
  styleUrl: './theme-list.component.scss',
})
export class ThemeListComponent implements OnInit {
  private api = inject(ApiService);

  themes = signal<Theme[]>([]);
  loading = signal(true);
  isAdmin = signal(false);
  creating = signal(false);
  nouveauNom = '';
  nouvelleDescription = '';

  ngOnInit(): void {
    this.load();
    this.api.getMe().subscribe(me => this.isAdmin.set(me.is_admin));
  }

  load(): void {
    this.loading.set(true);
    this.api.getThemes().subscribe(themes => {
      this.themes.set(themes);
      this.loading.set(false);
    });
  }

  startCreate(): void {
    this.creating.set(true);
  }

  cancelCreate(): void {
    this.creating.set(false);
    this.nouveauNom = '';
    this.nouvelleDescription = '';
  }

  submitCreate(): void {
    if (!this.nouveauNom.trim()) return;
    this.api.createTheme({
      nom: this.nouveauNom.trim(),
      description: this.nouvelleDescription.trim(),
      ordre: this.themes().length,
    }).subscribe(() => {
      this.cancelCreate();
      this.load();
    });
  }

  supprimer(theme: Theme): void {
    if (!confirm(`Supprimer le thème « ${theme.nom} » et toutes ses fiches ?`)) return;
    this.api.deleteTheme(theme.id).subscribe(() => this.load());
  }
}
