import { Component, ElementRef, HostListener, OnInit, computed, inject, signal, ViewChild } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { KeycloakService } from './core/keycloak.service';
import { ThemeService } from './core/theme.service';
import { ApiService } from './core/api.service';

interface NavItem {
  label: string;
  abbr: string;
  path: string;
  exact?: boolean;
}

const MOBILE_CLOSE_ANIM_MS = 220;

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, NgTemplateOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class AppComponent implements OnInit {
  protected kc = inject(KeycloakService);
  protected theme = inject(ThemeService);
  private api = inject(ApiService);

  collapsed = signal(false);
  mobileOpen = signal(false);
  mobileClosing = signal(false);
  isAdmin = signal(false);

  protected noop = (): void => {};
  protected closeMobileFn = (): void => this.closeMobile();

  private readonly baseNavItems: NavItem[] = [
    { path: '/',           label: 'Accueil',           abbr: 'Ac', exact: true },
    { path: '/themes',     label: 'Fiches de révision', abbr: 'Fi' },
    { path: '/quiz',       label: 'Quiz',              abbr: 'Qz' },
    { path: '/historique', label: 'Mon historique',    abbr: 'Hi' },
    { path: '/bilan',      label: 'Mon bilan',         abbr: 'Bi' },
    { path: '/ressources', label: 'Autres ressources', abbr: 'Re' },
    { path: '/profile',    label: 'Profil',            abbr: 'Pr' },
  ];

  private readonly adminNavItems: NavItem[] = [
    { path: '/questions',      label: 'Banque de questions', abbr: 'Qu' },
    { path: '/generation-ia',  label: 'Génération IA',       abbr: 'Ge' },
    { path: '/parametrage',    label: 'Paramétrage',         abbr: 'Pa' },
  ];

  navItems = computed<NavItem[]>(() => this.isAdmin()
    ? [...this.baseNavItems, ...this.adminNavItems]
    : this.baseNavItems);

  @ViewChild('closeBtn') private closeBtnRef?: ElementRef<HTMLButtonElement>;
  @ViewChild('burgerBtn') private burgerBtnRef?: ElementRef<HTMLButtonElement>;

  ngOnInit(): void {
    this.api.getMe().subscribe(me => this.isAdmin.set(me.is_admin));
  }

  toggleCollapsed(): void {
    this.collapsed.update(v => !v);
  }

  openMobile(): void {
    this.mobileOpen.set(true);
    this.mobileClosing.set(false);
    document.body.style.overflow = 'hidden';
    setTimeout(() => this.closeBtnRef?.nativeElement.focus());
  }

  closeMobile(): void {
    if (!this.mobileOpen() || this.mobileClosing()) return;
    this.mobileClosing.set(true);
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setTimeout(() => {
      this.mobileOpen.set(false);
      this.mobileClosing.set(false);
      document.body.style.overflow = '';
      this.burgerBtnRef?.nativeElement.focus();
    }, reduced ? 0 : MOBILE_CLOSE_ANIM_MS);
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.mobileOpen()) this.closeMobile();
  }

  get username(): string {
    return this.kc.username || this.kc.email;
  }

  logout(): void {
    this.kc.logout();
  }
}

// Export pour Angular standalone
export { AppComponent as App };
