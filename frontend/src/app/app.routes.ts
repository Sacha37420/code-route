import { Routes } from '@angular/router';
import { HomeComponent }        from './pages/home/home.component';
import { ProfileComponent }     from './pages/profile/profile.component';
import { ThemeListComponent }   from './pages/themes/theme-list.component';
import { ThemeDetailComponent } from './pages/themes/theme-detail.component';
import { FicheDetailComponent } from './pages/fiches/fiche-detail.component';
import { RessourcesComponent }  from './pages/ressources/ressources.component';

export const routes: Routes = [
  { path: '',            component: HomeComponent },
  { path: 'themes',      component: ThemeListComponent },
  { path: 'themes/:id',  component: ThemeDetailComponent },
  { path: 'fiches/:id',  component: FicheDetailComponent },
  { path: 'ressources',  component: RessourcesComponent },
  { path: 'profile',     component: ProfileComponent },
  { path: '**',          redirectTo: '' },
];
