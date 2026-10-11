"""Qui lit, modifie, lance quoi : administrateurs (ADMIN_EMAILS) et usagers,
propriété des sessions de quiz, corrections et clé Mistral jamais exposées."""
import unittest
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.db import connection
from django.test import override_settings

from api.models import (
    AnalyseIA, ConfigurationMistral, FicheCours, GenerationIA, Question, QuizSession, SiteExterne, Theme,
)
from .outils import ADMIN, CLE_MISTRAL, CasRoute, client, creer_question, creer_theme


class AdminOuUsagerTests(CasRoute):

    def setUp(self):
        super().setUp()
        self.theme = creer_theme()
        self.fiche = FicheCours.objects.create(theme=self.theme, titre='Les panneaux', contenu='# Stop')
        self.site = SiteExterne.objects.create(nom='Site', url='https://exemple.test/', statut='gratuit')
        self.question, self.ok, self.ko = creer_question(self.theme, statut='proposee')
        self.generation = GenerationIA.objects.create(theme=self.theme, difficulte='facile', nombre_demande=2)

    def test_identite(self):
        self.assertEqual(self.alice.get('/api/me/').json(), {
            'email': 'alice@ssolab.local', 'username': 'alice', 'groups': ['famille'], 'is_admin': False})
        self.assertTrue(self.admin.get('/api/me/').json()['is_admin'])
        # La comparaison d'adresse ignore la casse.
        self.assertTrue(client('x', email='Admin@SSOLAB.local').get('/api/me/').json()['is_admin'])
        self.assertEqual(client('x', email='Admin@SSOLAB.local').get('/api/questions/').status_code, 200)

    def test_usager_lit_le_contenu_pedagogique_sans_pouvoir_l_ecrire(self):
        for base, pk, corps in (
            ('/api/themes/', self.theme.id, {'nom': 'Pirate'}),
            ('/api/fiches/', self.fiche.id, {'theme': self.theme.id, 'titre': 'Pirate', 'contenu': 'x'}),
            ('/api/sites-externes/', self.site.id, {'nom': 'Pirate', 'url': 'https://p.test/', 'statut': 'payant'}),
        ):
            with self.subTest(base):
                self.assertEqual(self.alice.get(base).status_code, 200)
                self.assertEqual(self.alice.get(f'{base}{pk}/').status_code, 200)
                self.assertEqual(self.alice.post(base, corps, format='json').status_code, 403)
                self.assertEqual(self.alice.put(f'{base}{pk}/', corps, format='json').status_code, 403)
                self.assertEqual(self.alice.patch(f'{base}{pk}/', corps, format='json').status_code, 403)
                self.assertEqual(self.alice.delete(f'{base}{pk}/').status_code, 403)
        self.assertEqual((Theme.objects.get().nom, FicheCours.objects.get().titre, SiteExterne.objects.get().nom),
                         ('Signalisation', 'Les panneaux', 'Site'))

    def test_administrateur_ecrit_le_contenu_pedagogique(self):
        r = self.admin.post('/api/themes/', {'nom': 'Priorités', 'ordre': 2}, format='json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.admin.patch(f'/api/fiches/{self.fiche.id}/', {'titre': 'Corrigée'},
                                          format='json').status_code, 200)
        self.assertEqual(self.admin.delete(f'/api/sites-externes/{self.site.id}/').status_code, 204)

    def test_la_banque_de_questions_est_fermee_aux_usagers(self):
        """Un usager ne parcourt jamais la banque avec les bonnes réponses visibles."""
        pk = self.question.id
        essais = [('get', '/api/questions/', None), ('get', f'/api/questions/{pk}/', None),
                  ('post', '/api/questions/', {'enonce': 'x'}), ('patch', f'/api/questions/{pk}/', {'statut': 'validee'}),
                  ('delete', f'/api/questions/{pk}/', None), ('post', f'/api/questions/{pk}/valider/', {}),
                  ('post', f'/api/questions/{pk}/rejeter/', {})]
        for methode, route, corps in essais:
            with self.subTest(route=route, methode=methode):
                r = getattr(self.alice, methode)(route, corps, format='json')
                self.assertEqual(r.status_code, 403)
                self.assertNotIn(b'correcte', r.content)
        self.assertEqual(Question.objects.get().statut, 'proposee')
        self.assertEqual(self.admin.get(f'/api/questions/{pk}/').status_code, 200)

    def test_pages_d_administration_fermees_aux_usagers(self):
        essais = [
            ('get', '/api/configuration-mistral/', None),
            ('patch', '/api/configuration-mistral/', {'actif': True, 'api_key': 'cle-pirate'}),
            ('get', '/api/generation-ia/', None),
            ('post', '/api/generation-ia/lancer/', {'theme_id': self.theme.id, 'difficulte': 'facile'}),
            ('get', f'/api/generation-ia/{self.generation.id}/statut/', None),
            ('post', '/api/assistant-fiches/message/', {'message': 'bonjour', 'theme_id': self.theme.id}),
            ('get', '/api/illustrations-disponibles/', None),
        ]
        for methode, route, corps in essais:
            with self.subTest(route=route):
                self.assertEqual(getattr(self.alice, methode)(route, corps, format='json').status_code, 403)
        # Aucun effet : pas de tâche, pas d'appel à l'IA ni à storage, clé inchangée.
        self.tache_generation.delay.assert_not_called()
        self.Mistral.assert_not_called()
        self.http_get.assert_not_called()
        self.assertEqual(GenerationIA.objects.count(), 1)
        cfg = ConfigurationMistral.get()
        self.assertEqual((cfg.actif, cfg.api_key), (False, ''))

    @override_settings(ADMIN_EMAILS=set())
    def test_sans_liste_d_administrateurs_personne_n_administre(self):
        for c in (self.admin, self.alice):
            self.assertEqual(c.get('/api/questions/').status_code, 403)
            self.assertEqual(c.post('/api/themes/', {'nom': 'x'}, format='json').status_code, 403)
            self.assertFalse(c.get('/api/me/').json()['is_admin'])
        self.assertEqual(self.alice.get('/api/themes/').status_code, 200)


class SessionsDeQuizTests(CasRoute):
    """Une session de quiz, son historique et son bilan n'appartiennent qu'à leur auteur."""

    def setUp(self):
        super().setUp()
        self.theme = creer_theme()
        self.q1, self.ok1, self.ko1 = creer_question(self.theme, 'Q1')
        self.q2, self.ok2, self.ko2 = creer_question(self.theme, 'Q2')
        r = self.alice.post('/api/quiz/demarrer/', {'nombre_questions': 2}, format='json')
        self.assertEqual(r.status_code, 201)
        self.demarrage = r.json()
        self.sid = self.demarrage['session']['id']

    def test_le_quiz_ne_livre_pas_les_corrections(self):
        for q in self.demarrage['questions']:
            self.assertEqual(set(q), {'id', 'theme', 'theme_nom', 'enonce', 'type', 'difficulte',
                                      'illustration_path', 'illustration_credit', 'reponses'})
            for rep in q['reponses']:
                self.assertEqual(set(rep), {'id', 'texte'})

    def test_un_autre_ne_touche_pas_a_la_session(self):
        for methode, route, corps in (
            ('get', f'/api/quiz/{self.sid}/', None),
            ('post', f'/api/quiz/{self.sid}/repondre/', {'question': self.q1.id, 'reponses_choisies': self.ok1}),
            ('post', f'/api/quiz/{self.sid}/terminer/', {}),
        ):
            with self.subTest(route):
                r = getattr(self.bob, methode)(route, corps, format='json')
                self.assertEqual(r.status_code, 403)
                self.assertNotIn(b'correcte', r.content)
        s = QuizSession.objects.get()
        self.assertEqual((s.date_fin, s.score), (None, None))
        self.assertFalse(s.reponses_donnees.filter(correcte=True).exists())
        self.tache_analyse.delay.assert_not_called()

    def test_l_administrateur_n_a_pas_acces_aux_sessions_des_autres(self):
        self.assertEqual(self.admin.get(f'/api/quiz/{self.sid}/').status_code, 403)
        self.assertEqual(self.admin.get('/api/quiz/historique/').json(), [])

    def test_historique_et_proprietaire_tires_du_jeton(self):
        self.bob.post('/api/quiz/demarrer/', {'utilisateur_email': 'alice@ssolab.local'}, format='json')
        self.assertEqual([s['id'] for s in self.alice.get('/api/quiz/historique/').json()], [self.sid])
        self.assertEqual(len(self.bob.get('/api/quiz/historique/').json()), 1)
        self.assertEqual(QuizSession.objects.filter(utilisateur_email='bob@ssolab.local').count(), 1)
        # Même personne, casse différente dans le jeton : c'est toujours sa session.
        self.assertEqual(client('alice', email='Alice@SSOLAB.local').get(f'/api/quiz/{self.sid}/').status_code, 200)

    def test_bilan_personnel(self):
        self.assertEqual(self.alice.get('/api/mon-bilan/').status_code, 404)
        AnalyseIA.objects.create(utilisateur_email='alice@ssolab.local', contenu={'n': 1}, resume_texte='ancien')
        AnalyseIA.objects.create(utilisateur_email='alice@ssolab.local', contenu={'n': 2}, resume_texte='récent')
        self.assertEqual(self.alice.get('/api/mon-bilan/').json()['resume_texte'], 'récent')
        self.assertEqual(self.bob.get('/api/mon-bilan/').status_code, 404)
        self.assertEqual(self.admin.get('/api/mon-bilan/').status_code, 404)

    def test_session_inconnue(self):
        self.assertEqual(self.alice.get('/api/quiz/999999/').status_code, 404)

    # DÉFAUT DE PRODUCTION (contrat I4, non corrigé) : `GET /api/quiz/<id>/` sert
    # QuizSessionDetailSerializer (donc QuestionReviewSerializer, avec `correcte` et
    # les explications) même tant que la session est ouverte. Un usager démarre un
    # quiz, lit ici toutes les bonnes réponses, puis répond : la règle « ne jamais
    # exposer la bonne réponse avant correction » (ReponseQuizSerializer) est
    # contournée. À retirer quand la vue ne détaille que les questions répondues
    # ou les sessions terminées.
    @unittest.expectedFailure
    def test_le_detail_d_une_session_ouverte_ne_livre_pas_les_bonnes_reponses(self):
        r = self.alice.get(f'/api/quiz/{self.sid}/')
        self.assertEqual(r.status_code, 200)
        for ligne in r.json()['reponses_donnees']:
            for rep in ligne['question']['reponses']:
                self.assertNotIn('correcte', rep)

    # DÉFAUT DE PRODUCTION (contrat I4, non corrigé) : l'image d'une question n'est
    # servie que par `/api/questions/<id>/illustration/`, action de QuestionViewSet
    # (IsAdmin). Or c'est cette URL que le frontend appelle pendant un quiz et dans
    # l'historique (`ApiService.questionIllustrationUrl`) : un usager non admin
    # reçoit 403 et ne voit jamais l'illustration d'une question qu'on lui pose.
    @unittest.expectedFailure
    def test_un_usager_voit_l_illustration_d_une_question_de_son_quiz(self):
        Question.objects.filter(pk=self.q1.id).update(illustration_path='questions/abc-panneau.png')
        self.http_get.side_effect = None
        self.http_get.return_value = mock.Mock(status_code=200, iter_content=lambda chunk_size: [b'PNG'])
        r = self.alice.get(f'/api/questions/{self.q1.id}/illustration/')
        self.assertEqual(r.status_code, 200)


class CleMistralTests(CasRoute):
    """La clé Mistral du lab : écrite par un administrateur, jamais relue."""

    URL = '/api/configuration-mistral/'

    def test_la_cle_n_est_jamais_rendue(self):
        r = self.admin.patch(self.URL, {'api_key': CLE_MISTRAL, 'actif': True, 'modele': 'm'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('api_key', r.json())
        self.assertNotIn(CLE_MISTRAL, r.content.decode())
        r = self.admin.get(self.URL)
        self.assertEqual({k: r.json()[k] for k in ('actif', 'has_key', 'modele')},
                         {'actif': True, 'has_key': True, 'modele': 'm'})
        self.assertNotIn('api_key', r.json())
        self.assertNotIn(CLE_MISTRAL, r.content.decode())

    def test_la_cle_est_chiffree_en_base(self):
        self.admin.patch(self.URL, {'api_key': CLE_MISTRAL}, format='json')
        with connection.cursor() as cur:
            cur.execute('SELECT api_key FROM configuration_mistral')
            (brut,), = cur.fetchall()
        self.assertTrue(brut)
        self.assertNotIn('SECRET', brut)
        self.assertEqual(ConfigurationMistral.get().api_key, CLE_MISTRAL)

    def test_un_champ_vide_n_efface_pas_la_cle(self):
        self.admin.patch(self.URL, {'api_key': CLE_MISTRAL, 'actif': True}, format='json')
        for corps in ({'api_key': '', 'modele': 'autre'}, {'actif': False}):
            self.assertEqual(self.admin.patch(self.URL, corps, format='json').status_code, 200)
        cfg = ConfigurationMistral.get()
        self.assertEqual((cfg.api_key, cfg.modele, cfg.actif), (CLE_MISTRAL, 'autre', False))
        self.assertEqual(ConfigurationMistral.objects.count(), 1)

    def test_aucune_reponse_ne_contient_la_cle(self):
        """Balayage : lectures d'admin et d'usager, génération et assistant en panne."""
        self.activer_mistral()
        theme = creer_theme()
        creer_question(theme)
        self.mistral.chat.complete.side_effect = RuntimeError('401 Unauthorized')
        self.mistral.beta.agents.create.side_effect = RuntimeError('401 Unauthorized')
        from api import tasks
        generation = GenerationIA.objects.create(theme=theme, difficulte='facile', nombre_demande=1)
        tasks.generer_questions(generation.id)
        tasks.analyser_resultats('alice@ssolab.local')
        reponses = [
            self.admin.get(self.URL), self.admin.get('/api/me/'), self.admin.get('/api/generation-ia/'),
            self.admin.get(f'/api/generation-ia/{generation.id}/statut/'), self.admin.get('/api/questions/'),
            self.admin.post('/api/assistant-fiches/message/', {'message': 'x', 'theme_id': theme.id}, format='json'),
            self.alice.get('/api/me/'), self.alice.get('/api/themes/'), self.alice.get('/api/quiz/historique/'),
        ]
        self.assertEqual([r.status_code for r in reponses], [200, 200, 200, 200, 200, 502, 200, 200, 200])
        for r in reponses:
            self.assertNotIn('SECRET', r.content.decode())
        # La clé a bien servi (sinon le balayage ne prouverait rien).
        self.Mistral.assert_called_with(api_key=CLE_MISTRAL)
        self.assertEqual(GenerationIA.objects.get().statut, 'erreur')

    def test_amorcage_depuis_l_environnement_n_ecrase_jamais_une_cle(self):
        with override_settings(MISTRAL_API_KEY_BOOTSTRAP=''):
            call_command('seed_config_mistral', stdout=StringIO())
        self.assertEqual((ConfigurationMistral.get().api_key, ConfigurationMistral.get().actif), ('', False))
        with override_settings(MISTRAL_API_KEY_BOOTSTRAP='cle-env'):
            sortie = StringIO()
            call_command('seed_config_mistral', stdout=sortie)
            self.assertNotIn('cle-env', sortie.getvalue())
        self.assertEqual((ConfigurationMistral.get().api_key, ConfigurationMistral.get().actif), ('cle-env', True))
        # Un administrateur la change : le déploiement suivant ne la remet pas d'aplomb.
        self.admin.patch(self.URL, {'api_key': 'cle-admin'}, format='json')
        with override_settings(MISTRAL_API_KEY_BOOTSTRAP='cle-env'):
            call_command('seed_config_mistral', stdout=StringIO())
        self.assertEqual(ConfigurationMistral.get().api_key, 'cle-admin')
