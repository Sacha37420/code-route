import { Component, DestroyRef, Input, OnChanges, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

/**
 * <img> classique impossible : l'illustration est servie derrière l'auth JWT
 * (jamais d'accès anonyme, cf. CLAUDE.md « Verrou 2 ») — un <img src> brut
 * n'attache pas l'en-tête Authorization. On télécharge donc le blob via
 * HttpClient (intercepté par auth.interceptor) puis on l'affiche via une URL
 * objet locale.
 */
@Component({
  selector: 'app-protected-image',
  standalone: true,
  template: `@if (safeUrl) {<img [src]="safeUrl" [alt]="alt" />}`,
})
export class ProtectedImageComponent implements OnChanges {
  @Input({ required: true }) url!: string;
  @Input() alt = '';

  private http = inject(HttpClient);
  private sanitizer = inject(DomSanitizer);
  private destroyRef = inject(DestroyRef);
  private objectUrl?: string;

  safeUrl?: SafeUrl;

  ngOnChanges(): void {
    this.revoke();
    if (!this.url) return;
    const sub = this.http.get(this.url, { responseType: 'blob' }).subscribe(blob => {
      this.objectUrl = URL.createObjectURL(blob);
      this.safeUrl = this.sanitizer.bypassSecurityTrustUrl(this.objectUrl);
    });
    this.destroyRef.onDestroy(() => {
      sub.unsubscribe();
      this.revoke();
    });
  }

  private revoke(): void {
    if (this.objectUrl) {
      URL.revokeObjectURL(this.objectUrl);
      this.objectUrl = undefined;
    }
  }
}
