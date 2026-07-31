import { Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import { ApiService } from '../../core/api.service';
import { ProtectedImageComponent } from '../../core/protected-image.component';
import { FicheCours, IllustrationDisponible } from '../../core/models';

@Component({
  selector: 'app-fiche-detail',
  standalone: true,
  imports: [RouterLink, FormsModule, ProtectedImageComponent],
  templateUrl: './fiche-detail.component.html',
  styleUrl: './fiche-detail.component.scss',
})
export class FicheDetailComponent implements OnInit {
  private api = inject(ApiService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private sanitizer = inject(DomSanitizer);

  fiche = signal<FicheCours | undefined>(undefined);
  contenuHtml = signal<SafeHtml>('');
  loading = signal(true);
  isAdmin = signal(false);
  editing = signal(false);
  banque = signal<IllustrationDisponible[]>([]);
  showBanque = signal(false);

  // Champs d'édition
  editTitre = '';
  editContenu = '';
  editOrdre = 0;
  editCredit = '';
  fichierChoisi: File | null = null;

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getMe().subscribe(me => this.isAdmin.set(me.is_admin));
    this.api.getFiche(id).subscribe(fiche => {
      this.fiche.set(fiche);
      this.renderMarkdown(fiche.contenu);
      this.editTitre = fiche.titre;
      this.editContenu = fiche.contenu;
      this.editOrdre = fiche.ordre;
      this.editCredit = fiche.illustration_credit;
      this.loading.set(false);
    });
  }

  private renderMarkdown(md: string): void {
    const html = marked.parse(md || '', { async: false }) as string;
    this.contenuHtml.set(this.sanitizer.bypassSecurityTrustHtml(html));
  }

  illustrationUrl(): string {
    return this.api.ficheIllustrationUrl(this.fiche()!.id);
  }

  startEdit(): void {
    this.editing.set(true);
  }

  cancelEdit(): void {
    this.editing.set(false);
    this.fichierChoisi = null;
    this.showBanque.set(false);
  }

  onFichierChange(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.fichierChoisi = input.files?.[0] ?? null;
  }

  toggleBanque(): void {
    this.showBanque.update(v => !v);
    if (this.showBanque() && this.banque().length === 0) {
      this.api.getIllustrationsDisponibles().subscribe(items => this.banque.set(items));
    }
  }

  choisirDansBanque(item: IllustrationDisponible): void {
    const fiche = this.fiche()!;
    const fd = new FormData();
    fd.set('theme', String(fiche.theme));
    fd.set('titre', this.editTitre);
    fd.set('contenu', this.editContenu);
    fd.set('ordre', String(this.editOrdre));
    fd.set('illustration_path', item.relative_path);
    fd.set('illustration_credit', item.credit);
    this.api.updateFiche(fiche.id, fd).subscribe(updated => {
      this.fiche.set(updated);
      this.editCredit = updated.illustration_credit;
      this.showBanque.set(false);
    });
  }

  submitEdit(): void {
    const fiche = this.fiche()!;
    const fd = new FormData();
    fd.set('theme', String(fiche.theme));
    fd.set('titre', this.editTitre);
    fd.set('contenu', this.editContenu);
    fd.set('ordre', String(this.editOrdre));
    fd.set('illustration_credit', this.editCredit);
    if (this.fichierChoisi) fd.set('illustration_file', this.fichierChoisi);
    this.api.updateFiche(fiche.id, fd).subscribe(updated => {
      this.fiche.set(updated);
      this.renderMarkdown(updated.contenu);
      this.cancelEdit();
    });
  }

  supprimer(): void {
    const fiche = this.fiche()!;
    if (!confirm(`Supprimer la fiche « ${fiche.titre} » ?`)) return;
    this.api.deleteFiche(fiche.id).subscribe(() => this.router.navigate(['/themes', fiche.theme]));
  }
}
