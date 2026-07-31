import { Component, inject, OnInit, signal } from '@angular/core';
import { ApiService } from '../../core/api.service';
import { KeycloakService } from '../../core/keycloak.service';
import { Me } from '../../core/models';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.scss',
})
export class ProfileComponent implements OnInit {
  private api = inject(ApiService);
  private kc = inject(KeycloakService);

  me      = signal<Me | null>(null);
  loading = signal(true);
  error   = signal<string | null>(null);
  tokenCopie = signal(false);

  ngOnInit(): void {
    this.api.getMe().subscribe({
      next: (data) => {
        this.me.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(`Impossible de charger le profil (${err.status ?? 'réseau'})`);
      },
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
