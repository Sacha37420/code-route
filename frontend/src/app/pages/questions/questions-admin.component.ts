import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { ProtectedImageComponent } from '../../core/protected-image.component';
import {
  Difficulte, IllustrationDisponible, QuestionAdmin, ReponseAdmin, StatutQuestion, Theme, TypeQuestion,
} from '../../core/models';

interface FormulaireQuestion {
  id?: number;
  theme: number | null;
  enonce: string;
  type: TypeQuestion;
  difficulte: Difficulte;
  explication_generale: string;
  illustration_credit: string;
  illustration_path: string;
  reponses: ReponseAdmin[];
}

function formulaireVide(): FormulaireQuestion {
  return {
    theme: null, enonce: '', type: 'qcm_unique', difficulte: 'facile',
    explication_generale: '', illustration_credit: '', illustration_path: '',
    reponses: [
      { texte: '', correcte: true, explication: '' },
      { texte: '', correcte: false, explication: '' },
    ],
  };
}

@Component({
  selector: 'app-questions-admin',
  standalone: true,
  imports: [FormsModule, ProtectedImageComponent],
  templateUrl: './questions-admin.component.html',
  styleUrl: './questions-admin.component.scss',
})
export class QuestionsAdminComponent implements OnInit {
  private api = inject(ApiService);

  themes = signal<Theme[]>([]);
  questions = signal<QuestionAdmin[]>([]);
  loading = signal(true);

  filtreTheme = '';
  filtreStatut = '';

  editing = signal(false);
  form: FormulaireQuestion = formulaireVide();
  fichierChoisi: File | null = null;
  banque = signal<IllustrationDisponible[]>([]);
  showBanque = signal(false);

  ngOnInit(): void {
    this.api.getThemes().subscribe(themes => this.themes.set(themes));
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.getQuestions({
      theme: this.filtreTheme ? Number(this.filtreTheme) : undefined,
      statut: this.filtreStatut || undefined,
    }).subscribe(questions => {
      this.questions.set(questions);
      this.loading.set(false);
    });
  }

  illustrationUrl(id: number): string {
    return this.api.questionIllustrationUrl(id);
  }

  startCreate(): void {
    this.form = formulaireVide();
    this.fichierChoisi = null;
    this.editing.set(true);
  }

  startEdit(q: QuestionAdmin): void {
    this.form = {
      id: q.id, theme: q.theme, enonce: q.enonce, type: q.type, difficulte: q.difficulte,
      explication_generale: q.explication_generale, illustration_credit: q.illustration_credit,
      illustration_path: q.illustration_path,
      reponses: q.reponses.map(r => ({ ...r })),
    };
    this.fichierChoisi = null;
    this.editing.set(true);
  }

  cancelEdit(): void {
    this.editing.set(false);
    this.showBanque.set(false);
  }

  onTypeChange(): void {
    if (this.form.type === 'vrai_faux') {
      this.form.reponses = [
        { texte: 'Vrai', correcte: true, explication: '' },
        { texte: 'Faux', correcte: false, explication: '' },
      ];
    }
  }

  ajouterReponse(): void {
    this.form.reponses.push({ texte: '', correcte: false, explication: '' });
  }

  supprimerReponse(index: number): void {
    if (this.form.reponses.length <= 2) return;
    this.form.reponses.splice(index, 1);
  }

  choisirCorrecteUnique(index: number): void {
    this.form.reponses.forEach((r, i) => { r.correcte = i === index; });
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
    this.form.illustration_path = item.relative_path;
    this.form.illustration_credit = item.credit;
    this.showBanque.set(false);
  }

  submit(): void {
    if (!this.form.theme || !this.form.enonce.trim()) return;
    if (!this.form.reponses.some(r => r.correcte)) {
      alert('Au moins une réponse doit être marquée correcte.');
      return;
    }

    // Envoi JSON (pas FormData) : QuestionAdminSerializer a un champ imbriqué
    // `reponses` (liste d'objets) — le parseur multipart de DRF ne sait pas
    // reconstruire une liste imbriquée à partir d'un champ FormData, seul le
    // JSONParser le fait correctement. Le fichier, lui, part dans une requête
    // multipart séparée juste après (uniquement s'il a changé).
    const payload = {
      theme: this.form.theme,
      enonce: this.form.enonce,
      type: this.form.type,
      difficulte: this.form.difficulte,
      explication_generale: this.form.explication_generale,
      illustration_credit: this.form.illustration_credit,
      illustration_path: this.form.illustration_path,
      statut: 'validee',
      reponses: this.form.reponses,
    };

    const obs = this.form.id
      ? this.api.updateQuestion(this.form.id, payload)
      : this.api.createQuestion(payload);

    obs.subscribe(saved => {
      if (this.fichierChoisi) {
        const fd = new FormData();
        fd.set('illustration_file', this.fichierChoisi);
        this.api.updateQuestion(saved.id, fd).subscribe(() => {
          this.cancelEdit();
          this.load();
        });
      } else {
        this.cancelEdit();
        this.load();
      }
    });
  }

  valider(q: QuestionAdmin): void {
    this.api.validerQuestion(q.id).subscribe(() => this.load());
  }

  rejeter(q: QuestionAdmin): void {
    this.api.rejeterQuestion(q.id).subscribe(() => this.load());
  }

  supprimer(q: QuestionAdmin): void {
    if (!confirm('Supprimer cette question ?')) return;
    this.api.deleteQuestion(q.id).subscribe(() => this.load());
  }

  statutLabel(s: StatutQuestion): string {
    return { validee: 'Validée', proposee: 'Proposée (IA)', rejetee: 'Rejetée' }[s];
  }
}
