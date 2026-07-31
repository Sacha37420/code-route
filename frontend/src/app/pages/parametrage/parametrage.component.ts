import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { KeycloakService } from '../../core/keycloak.service';
import { ConfigurationMistral } from '../../core/models';

@Component({
  selector: 'app-parametrage',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './parametrage.component.html',
  styleUrl: './parametrage.component.scss',
})
export class ParametrageComponent implements OnInit {
  private api = inject(ApiService);
  private kc = inject(KeycloakService);

  config = signal<ConfigurationMistral | undefined>(undefined);
  loading = signal(true);
  enregistre = signal(false);
  tokenCopie = signal(false);

  actif = false;
  modele = 'mistral-large-latest';
  nouvelleCle = '';

  ngOnInit(): void {
    this.api.getConfigurationMistral().subscribe(c => {
      this.config.set(c);
      this.actif = c.actif;
      this.modele = c.modele;
      this.loading.set(false);
    });
  }

  enregistrer(): void {
    const payload: { actif: boolean; modele: string; api_key?: string } = {
      actif: this.actif, modele: this.modele,
    };
    // Champ write-only : on n'envoie api_key que si l'admin en a saisi une
    // nouvelle, sinon la clé déjà enregistrée n'est jamais touchée (cf. serializer).
    if (this.nouvelleCle.trim()) payload.api_key = this.nouvelleCle.trim();

    this.api.updateConfigurationMistral(payload).subscribe(c => {
      this.config.set(c);
      this.nouvelleCle = '';
      this.enregistre.set(true);
      setTimeout(() => this.enregistre.set(false), 2000);
    });
  }

  copierToken(): void {
    const token = this.kc.getToken();
    if (!token) return;
    navigator.clipboard.writeText(token).then(() => {
      this.tokenCopie.set(true);
      setTimeout(() => this.tokenCopie.set(false), 2000);
    });
  }
}
