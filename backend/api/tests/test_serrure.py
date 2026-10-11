"""Verrou 2 — la serrure de l'API, avec de vrais jetons signés localement."""
import time

import jwt
from django.test import override_settings
from django.urls import get_resolver
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient

from .outils import ADMIN, AUTRE_CLE_RSA, CasRoute, client, jeton

ROUTE = '/api/themes/'


class SerrureTests(CasRoute):

    def test_sans_jeton_refuse(self):
        self.assertIn(APIClient().get(ROUTE).status_code, (401, 403))

    def test_en_tete_qui_n_est_pas_un_bearer_refuse(self):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f'Basic {jeton()}')
        self.assertIn(c.get(ROUTE).status_code, (401, 403))

    def test_membre_d_un_des_groupes_accepte(self):
        for groups in (['famille'], ['developers'], ['amis-inconnus', 'developers']):
            with self.subTest(groups=groups):
                self.assertEqual(client('alice', groups=groups).get(ROUTE).status_code, 200)

    def test_jeton_d_un_autre_client_refuse(self):
        # admin-cli : client public du realm, password grant ouvert à tout compte.
        for azp in ('admin-cli', 'storage', 'lab-admin', '', None):
            with self.subTest(azp=azp):
                r = client('alice', azp=azp).get(ROUTE)
                self.assertEqual(r.status_code, 403)
                self.assertIn('autre client', r.json()['detail'])

    def test_hors_groupe_refuse(self):
        for groups in ([], None, ['amis'], ['famill'], ['famille-bis']):
            with self.subTest(groups=groups):
                r = client('lea', groups=groups).get(ROUTE)
                self.assertEqual(r.status_code, 403)
                self.assertIn('groupe', r.json()['detail'])

    def test_etre_administrateur_de_l_app_ne_dispense_pas_du_groupe(self):
        # ADMIN_EMAILS décide de l'administration, jamais de l'entrée.
        r = client('admin', groups=[], email=ADMIN).get(ROUTE)
        self.assertEqual(r.status_code, 403)
        r = client('admin', azp='admin-cli', email=ADMIN).get('/api/configuration-mistral/')
        self.assertEqual(r.status_code, 403)

    def test_jeton_expire_refuse(self):
        r = client('alice', duree=-60).get(ROUTE)
        self.assertEqual(r.status_code, 403)
        self.assertIn('Token invalide', r.json()['detail'])

    def test_jeton_signe_par_une_autre_cle_refuse(self):
        r = client('alice', cle=AUTRE_CLE_RSA).get(ROUTE)
        self.assertEqual(r.status_code, 403)
        self.assertIn('Token invalide', r.json()['detail'])

    def test_jeton_non_signe_ou_hs256_refuse(self):
        claims = {'preferred_username': 'admin', 'email': ADMIN, 'azp': 'code-route',
                  'groups': ['famille'], 'exp': int(time.time()) + 300}
        sans_signature = jwt.encode(claims, None, algorithm='none')
        hs256 = jwt.encode(claims, 'secret-partage-devine' * 3, algorithm='HS256')
        for nom, tok in (('none', sans_signature), ('hs256', hs256), ('charabia', 'pas.un.jeton')):
            with self.subTest(nom):
                c = APIClient()
                c.credentials(HTTP_AUTHORIZATION=f'Bearer {tok}')
                self.assertEqual(c.get(ROUTE).status_code, 403)

    def test_charge_utile_modifiee_apres_signature_refusee(self):
        # Jeton d'un usager dont on réécrit la charge utile (email d'admin) en gardant la signature.
        usager = jeton('alice')
        admin = jeton('admin')
        entete, _, signature = usager.split('.')
        forge = '.'.join([entete, admin.split('.')[1], signature])
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {forge}')
        self.assertEqual(c.get('/api/me/').status_code, 403)

    def test_jeton_sans_email_refuse(self):
        r = client('alice', email=None).get(ROUTE)
        self.assertEqual(r.status_code, 403)
        self.assertIn('email', r.json()['detail'])

    @override_settings(KEYCLOAK_REQUIRED_GROUPS=' developers , admins ')
    def test_liste_de_groupes_avec_espaces(self):
        self.assertEqual(client('a', groups=['admins']).get(ROUTE).status_code, 200)
        self.assertEqual(client('a', groups=['famille']).get(ROUTE).status_code, 403)


class InventaireTests(CasRoute):
    """Rien n'est ouvert sans jeton — vérifié sur les URL réelles."""

    def _vues(self, resolver=None):
        for p in (resolver or get_resolver()).url_patterns:
            if hasattr(p, 'url_patterns'):
                yield from self._vues(p)
            elif getattr(p.callback, 'cls', None) is not None:
                yield p.callback.cls

    def test_aucune_vue_n_echappe_au_jeton(self):
        vues = set(self._vues())
        self.assertGreater(len(vues), 15)
        ouvertes = {v.__name__ for v in vues
                    if AllowAny in v.permission_classes or not v.authentication_classes}
        self.assertEqual(ouvertes, set())

    def test_toute_route_refuse_un_anonyme_et_un_jeton_etranger(self):
        routes = [
            '/api/', '/api/me/', '/api/illustrations-disponibles/',
            '/api/themes/', '/api/themes/1/', '/api/fiches/', '/api/fiches/1/', '/api/fiches/1/illustration/',
            '/api/sites-externes/', '/api/sites-externes/1/',
            '/api/questions/', '/api/questions/1/', '/api/questions/1/illustration/',
            '/api/questions/1/valider/', '/api/questions/1/rejeter/',
            '/api/quiz/demarrer/', '/api/quiz/historique/', '/api/quiz/1/', '/api/quiz/1/repondre/',
            '/api/quiz/1/terminer/', '/api/configuration-mistral/', '/api/mon-bilan/',
            '/api/generation-ia/', '/api/generation-ia/lancer/', '/api/generation-ia/1/statut/',
            '/api/assistant-fiches/message/',
        ]
        anonyme, etranger = APIClient(), client('admin', azp='admin-cli')
        for route in routes:
            for methode in ('get', 'post', 'put', 'patch', 'delete'):
                with self.subTest(route=route, methode=methode):
                    self.assertIn(getattr(anonyme, methode)(route, {}, format='json').status_code, (401, 403))
                    self.assertEqual(getattr(etranger, methode)(route, {}, format='json').status_code, 403)
        self.tache_generation.delay.assert_not_called()
        # Garde-fou : une route ajoutée dans api/urls.py doit passer par cette liste.
        from api import urls
        self.assertEqual(len(urls.urlpatterns), 14)
        self.assertEqual(len(urls.router.registry), 4)

    def test_documentation_d_api_absente_hors_debug(self):
        for route in ('/api/schema/', '/api/docs/', '/'):
            self.assertEqual(self.admin.get(route).status_code, 404, route)
