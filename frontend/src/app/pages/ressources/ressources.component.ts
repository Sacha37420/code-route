import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { SiteExterne, StatutSiteExterne } from '../../core/models';

@Component({
  selector: 'app-ressources',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './ressources.component.html',
  styleUrl: './ressources.component.scss',
})
export class RessourcesComponent implements OnInit {
  private api = inject(ApiService);

  sites = signal<SiteExterne[]>([]);
  loading = signal(true);
  isAdmin = signal(false);
  creating = signal(false);

  nouveau: Partial<SiteExterne> = { statut: 'gratuit' };

  readonly statutLabels: Record<StatutSiteExterne, string> = {
    gratuit: 'Gratuit',
    freemium: 'Freemium',
    payant: 'Payant',
  };

  ngOnInit(): void {
    this.load();
    this.api.getMe().subscribe(me => this.isAdmin.set(me.is_admin));
  }

  load(): void {
    this.loading.set(true);
    this.api.getSitesExternes().subscribe(sites => {
      this.sites.set(sites);
      this.loading.set(false);
    });
  }

  startCreate(): void { this.creating.set(true); }
  cancelCreate(): void { this.creating.set(false); this.nouveau = { statut: 'gratuit' }; }

  submitCreate(): void {
    if (!this.nouveau.nom?.trim() || !this.nouveau.url?.trim()) return;
    this.api.createSiteExterne({
      ...this.nouveau,
      ordre: this.sites().length,
      date_verification: new Date().toISOString().slice(0, 10),
    }).subscribe(() => {
      this.cancelCreate();
      this.load();
    });
  }

  supprimer(site: SiteExterne): void {
    if (!confirm(`Supprimer « ${site.nom} » ?`)) return;
    this.api.deleteSiteExterne(site.id).subscribe(() => this.load());
  }
}
