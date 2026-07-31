import { Component, ElementRef, OnInit, ViewChild, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { marked } from 'marked';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ApiService } from '../../core/api.service';
import { AssistantMessage, Theme } from '../../core/models';

@Component({
  selector: 'app-assistant-fiches',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './assistant-fiches.component.html',
  styleUrl: './assistant-fiches.component.scss',
})
export class AssistantFichesComponent implements OnInit {
  private api = inject(ApiService);
  private sanitizer = inject(DomSanitizer);

  themes = signal<Theme[]>([]);
  themeId: number | null = null;
  deepsearch = false;

  messages = signal<AssistantMessage[]>([]);
  saisie = '';
  envoiEnCours = signal(false);
  erreur = signal('');
  applicationEnCours = signal(false);

  private conversationId?: string;

  @ViewChild('zoneMessages') private zoneMessages?: ElementRef<HTMLDivElement>;

  ngOnInit(): void {
    this.api.getThemes().subscribe(themes => {
      this.themes.set(themes);
      if (themes.length > 0) this.themeId = themes[0].id;
    });
  }

  get conversationDemarree(): boolean {
    return this.messages().length > 0;
  }

  rendreMarkdown(texte: string): SafeHtml {
    // Le bloc ```json de la proposition est retiré de l'affichage : il est
    // montré séparément dans la carte de proposition (voir template).
    const sansJson = texte.replace(/```json[\s\S]*?```/, '').trim();
    const html = marked.parse(sansJson || texte, { async: false }) as string;
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }

  envoyer(): void {
    const message = this.saisie.trim();
    if (!message || this.envoiEnCours()) return;
    if (!this.conversationId && !this.themeId) return;

    this.messages.update(m => [...m, { role: 'admin', texte: message }]);
    this.saisie = '';
    this.envoiEnCours.set(true);
    this.erreur.set('');
    this.scrollVersBas();

    const payload: { theme_id?: number; message: string; conversation_id?: string; deepsearch?: boolean } = {
      message,
    };
    if (this.conversationId) {
      payload.conversation_id = this.conversationId;
    } else {
      payload.theme_id = this.themeId!;
      payload.deepsearch = this.deepsearch;
    }

    this.api.envoyerMessageAssistantFiches(payload).subscribe({
      next: (res) => {
        this.conversationId = res.conversation_id;
        this.messages.update(m => [...m, {
          role: 'assistant',
          texte: res.reponse_texte,
          citations: res.citations,
          proposition: res.proposition,
        }]);
        this.envoiEnCours.set(false);
        this.scrollVersBas();
      },
      error: (err) => {
        this.envoiEnCours.set(false);
        this.erreur.set(err.error?.detail ?? "L'assistant n'a pas pu répondre.");
      },
    });
  }

  nouvelleConversation(): void {
    this.conversationId = undefined;
    this.messages.set([]);
    this.erreur.set('');
  }

  private scrollVersBas(): void {
    setTimeout(() => {
      const el = this.zoneMessages?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    });
  }

  appliquer(msg: AssistantMessage): void {
    const p = msg.proposition;
    if (!p || this.applicationEnCours()) return;
    this.applicationEnCours.set(true);

    if (p.action === 'modifier' && p.fiche_id) {
      const fd = new FormData();
      fd.set('titre', p.titre);
      fd.set('contenu', p.contenu);
      if (p.illustration_credit) fd.set('illustration_credit', p.illustration_credit);
      this.api.updateFiche(p.fiche_id, fd).subscribe({
        next: () => this.marquerAppliquee(msg),
        error: () => this.applicationEnCours.set(false),
      });
    } else {
      // Création : l'ordre est calculé côté serveur ? Non — on ajoute à la fin
      // de la liste existante du thème.
      this.api.getFiches(this.themeId!).subscribe(fiches => {
        const fd = new FormData();
        fd.set('theme', String(this.themeId));
        fd.set('titre', p.titre);
        fd.set('contenu', p.contenu);
        fd.set('ordre', String(fiches.length));
        if (p.illustration_credit) fd.set('illustration_credit', p.illustration_credit);
        this.api.createFiche(fd).subscribe({
          next: () => this.marquerAppliquee(msg),
          error: () => this.applicationEnCours.set(false),
        });
      });
    }
  }

  private marquerAppliquee(msg: AssistantMessage): void {
    msg.propositionAppliquee = true;
    this.applicationEnCours.set(false);
  }
}
