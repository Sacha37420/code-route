"""Outillage commun : vrais jetons RS256 signés par une clé locale, simulacres
de tout ce qui sort du conteneur.

Seul le TÉLÉCHARGEMENT du JWKS de Keycloak est remplacé. Tout le reste de
`KeycloakJWTAuthentication` (signature, expiration, azp, groupes, email)
s'exécute réellement — c'est le Verrou 2 de CLAUDE.md.
"""
import time
from unittest import mock

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.authentication import KeycloakJWTAuthentication
from api.models import ConfigurationMistral, FicheCours, Question, Reponse, SiteExterne, Theme

CLIENT_ID = 'code-route'
GROUPES = 'developers,famille'
ADMIN = 'admin@ssolab.local'
CLE_MISTRAL = 'mistral-SECRET-0123456789abcdef'

CLE_RSA = rsa.generate_private_key(public_exponent=65537, key_size=2048)
AUTRE_CLE_RSA = rsa.generate_private_key(public_exponent=65537, key_size=2048)


class JwksLocal:
    class _Cle:
        key = CLE_RSA.public_key()

    def get_signing_key_from_jwt(self, token):
        return self._Cle()


_ABSENT = object()


def jeton(uid='alice', groups=('famille',), azp=CLIENT_ID, email=_ABSENT, duree=300, cle=CLE_RSA):
    claims = {'preferred_username': uid, 'azp': azp, 'exp': int(time.time()) + duree}
    if groups is not None:
        claims['groups'] = list(groups)
    if email is _ABSENT:
        email = f'{uid}@ssolab.local'
    if email is not None:
        claims['email'] = email
    return jwt.encode(claims, cle, algorithm='RS256')


def client(uid='alice', **kw):
    """Client portant un vrai jeton : passe par la classe d'authentification réelle."""
    c = APIClient()
    c.jeton = jeton(uid, **kw)
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {c.jeton}')
    return c


@override_settings(
    KEYCLOAK_CLIENT_ID=CLIENT_ID,
    KEYCLOAK_REQUIRED_GROUPS=GROUPES,
    ADMIN_EMAILS={ADMIN},
    STORAGE_INTERNAL_URL='http://storage.test',
    STORAGE_NAMESPACE='code-route',
)
class CasRoute(TestCase):
    """Base : JWKS local, banque vidée de ses données d'amorçage, aucun réseau."""

    @classmethod
    def setUpTestData(cls):
        # Les migrations amorcent thèmes, fiches, questions et sites : on part de zéro.
        Question.objects.all().delete()
        FicheCours.objects.all().delete()
        SiteExterne.objects.all().delete()
        Theme.objects.all().delete()

    def _patch(self, *a, **kw):
        p = mock.patch(*a, **kw)
        m = p.start()
        self.addCleanup(p.stop)
        return m

    def setUp(self):
        super().setUp()
        p = mock.patch.object(KeycloakJWTAuthentication, '_get_jwks_client',
                              classmethod(lambda cls: JwksLocal()))
        p.start()
        self.addCleanup(p.stop)

        # Celery : l'envoi au courtier (Redis) est remplacé ; les tâches sont
        # testées en appel direct.
        self.tache_analyse = self._patch('api.views.analyser_resultats')
        self.tache_generation = self._patch('api.views.generer_questions')
        # storage : tout appel HTTP non prévu par un test est une erreur.
        hors_reseau = AssertionError('appel HTTP vers storage non simulé')
        self.http_post = self._patch('api.storage_client.requests.post', side_effect=hors_reseau)
        self.http_get = self._patch('api.storage_client.requests.get', side_effect=hors_reseau)
        self.http_delete = self._patch('api.storage_client.requests.delete', side_effect=hors_reseau)
        # Mistral : le SDK est remplacé, l'attente entre deux tentatives aussi.
        self.Mistral = mock.Mock(name='Mistral')
        self.mistral = self.Mistral.return_value
        self._patch('api.mistral_client._mistral_class', return_value=self.Mistral)
        self.sommeil = self._patch('api.mistral_client.time.sleep')

        self.admin = client('admin')
        self.alice = client('alice')
        self.bob = client('bob')

    # ── Mistral ──────────────────────────────────────────────────────────────
    def activer_mistral(self, cle=CLE_MISTRAL, modele='mistral-test'):
        cfg = ConfigurationMistral.get()
        cfg.actif, cfg.api_key, cfg.modele = True, cle, modele
        cfg.save()
        return cfg

    def mistral_repond(self, contenu):
        self.mistral.chat.complete.side_effect = None
        self.mistral.chat.complete.return_value = mock.Mock(
            choices=[mock.Mock(message=mock.Mock(content=contenu))])


def creer_theme(nom='Signalisation', ordre=0):
    return Theme.objects.create(nom=nom, ordre=ordre)


def creer_question(theme, enonce='Que signifie ce panneau ?', bonnes=('Stop',), fausses=('Cédez', 'Rien'),
                   **champs):
    """Question validée par défaut ; renvoie (question, ids des bonnes, ids des fausses)."""
    champs.setdefault('type', 'qcm_unique' if len(bonnes) == 1 else 'qcm_multiple')
    champs.setdefault('difficulte', 'facile')
    q = Question.objects.create(theme=theme, enonce=enonce, **champs)
    ok = [Reponse.objects.create(question=q, texte=t, correcte=True).id for t in bonnes]
    ko = [Reponse.objects.create(question=q, texte=t, correcte=False, explication=f'piège : {t}').id
          for t in fausses]
    return q, ok, ko
