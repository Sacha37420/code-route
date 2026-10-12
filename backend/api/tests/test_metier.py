"""Règles métier : moteur de quiz et notation, banque de questions, illustrations
(storage simulé), tâches d'analyse et de génération, client Mistral, assistant."""
import json
from unittest import mock

import requests
from django.core.files.uploadedfile import SimpleUploadedFile

from api import mistral_client, storage_client, tasks, views
from api.models import (
    AnalyseIA, ConfigurationMistral, FicheCours, GenerationIA, Question, QuizReponse, QuizSession, Reponse,
)
from .outils import CLE_MISTRAL, CasRoute, creer_question, creer_theme


class DemarrerQuizTests(CasRoute):

    def setUp(self):
        super().setUp()
        self.t1, self.t2 = creer_theme('Signalisation'), creer_theme('Priorités', 1)
        self.faciles = [creer_question(self.t1, f'F{i}')[0] for i in range(3)]
        self.dure = creer_question(self.t2, 'D1', difficulte='difficile')[0]
        self.proposee = creer_question(self.t1, 'IA en attente', statut='proposee', origine='ia')[0]
        self.rejetee = creer_question(self.t1, 'Rejetée', statut='rejetee')[0]

    def _demarrer(self, **corps):
        return self.alice.post('/api/quiz/demarrer/', corps, format='json')

    def test_seules_les_questions_validees_sont_tirees(self):
        for _ in range(3):      # tirage aléatoire : on répète
            ids = {q['id'] for q in self._demarrer(nombre_questions=50).json()['questions']}
            self.assertEqual(ids, {q.id for q in self.faciles} | {self.dure.id})

    def test_nombre_de_questions_borne(self):
        for demande, attendu in ((2, 2), (0, 1), (-5, 1), ('3', 3), (50, 4), (10 ** 6, 4)):
            with self.subTest(demande=demande):
                r = self._demarrer(nombre_questions=demande)
                self.assertEqual(r.status_code, 201)
                self.assertEqual(len(r.json()['questions']), attendu)
                # La session retient le nombre réellement servi, pas le nombre demandé.
                self.assertEqual(r.json()['session']['nombre_questions'], attendu)
                self.assertEqual(QuizReponse.objects.filter(session_id=r.json()['session']['id']).count(), attendu)

    def test_plafond_de_cinquante(self):
        for i in range(55):
            creer_question(self.t1, f'X{i}', fausses=())
        self.assertEqual(len(self._demarrer(nombre_questions=500).json()['questions']), 50)

    def test_dix_questions_par_defaut(self):
        for i in range(12):
            creer_question(self.t1, f'X{i}', fausses=())
        self.assertEqual(len(self._demarrer().json()['questions']), 10)

    def test_nombre_illisible_refuse(self):
        self.assertEqual(self._demarrer(nombre_questions='beaucoup').status_code, 400)
        self.assertEqual(QuizSession.objects.count(), 0)

    def test_filtres_theme_et_difficulte(self):
        r = self._demarrer(themes=[self.t2.id], nombre_questions=50).json()
        self.assertEqual([q['id'] for q in r['questions']], [self.dure.id])
        self.assertEqual(r['session']['themes_filtres'], str(self.t2.id))
        r = self._demarrer(difficulte='facile', nombre_questions=50).json()
        self.assertEqual({q['id'] for q in r['questions']}, {q.id for q in self.faciles})
        self.assertEqual(r['session']['difficulte_filtree'], 'facile')

    def test_aucune_question_disponible_pas_de_session(self):
        r = self._demarrer(themes=[self.t2.id], difficulte='facile')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(QuizSession.objects.count(), 0)


class RepondreEtTerminerTests(CasRoute):

    def setUp(self):
        super().setUp()
        theme = creer_theme()
        self.unique, self.u_ok, self.u_ko = creer_question(theme, 'Unique')
        self.multiple, self.m_ok, self.m_ko = creer_question(theme, 'Multiple', bonnes=('A', 'B'), fausses=('C',))
        self.vf, self.v_ok, self.v_ko = creer_question(theme, 'Vrai ou faux', bonnes=('Vrai',), fausses=('Faux',),
                                                       type='vrai_faux')
        self.sid = self.alice.post('/api/quiz/demarrer/', {'nombre_questions': 3}, format='json').json()['session']['id']
        # Une question hors de cette session.
        self.autre, self.a_ok, _ = creer_question(theme, 'Hors session')

    def _repondre(self, question, choix, **plus):
        return self.alice.post(f'/api/quiz/{self.sid}/repondre/',
                               {'question': question.id, 'reponses_choisies': choix, **plus}, format='json')

    def test_notation_ensemble_exact(self):
        cas = [
            (self.unique, self.u_ok, True),
            (self.unique, self.u_ko[:1], False),
            (self.unique, [], False),
            (self.unique, self.u_ok + self.u_ko[:1], False),        # la bonne + une fausse
            (self.multiple, self.m_ok, True),
            (self.multiple, list(reversed(self.m_ok)), True),       # l'ordre ne compte pas
            (self.multiple, [str(i) for i in self.m_ok], True),     # identifiants en texte
            (self.multiple, self.m_ok[:1], False),                  # réponse partielle
            (self.multiple, self.m_ok + self.m_ko, False),          # tout cocher
            (self.unique, self.a_ok, False),                        # bonne réponse d'une autre question
            (self.vf, self.v_ok, True),
            (self.vf, self.v_ko, False),
        ]
        for question, choix, attendu in cas:
            with self.subTest(question=question.enonce, choix=choix):
                # Une question ne reçoit qu'une réponse par session : session neuve par cas.
                self.sid = self.alice.post('/api/quiz/demarrer/', {'nombre_questions': 50},
                                           format='json').json()['session']['id']
                r = self._repondre(question, choix)
                self.assertEqual(r.status_code, 200)
                self.assertIs(r.json()['correcte'], attendu)
                self.assertIs(QuizReponse.objects.get(session_id=self.sid, question=question).correcte, attendu)

    def test_la_correction_n_arrive_qu_apres_la_reponse_et_pour_cette_question(self):
        r = self._repondre(self.unique, self.u_ko[:1], temps_ms=4200).json()
        self.assertEqual(r['question']['id'], self.unique.id)
        self.assertEqual({x['id'] for x in r['question']['reponses'] if x['correcte']}, set(self.u_ok))
        self.assertNotIn('Multiple', json.dumps(r))
        qr = QuizReponse.objects.get(session_id=self.sid, question=self.unique)
        self.assertEqual((qr.reponses_choisies, qr.temps_ms), (self.u_ko[:1], 4200))

    def test_question_hors_session_ou_choix_mal_forme(self):
        self.assertEqual(self._repondre(self.autre, self.a_ok).status_code, 404)
        self.assertEqual(self._repondre(self.unique, 'tout').status_code, 400)
        self.assertEqual(self._repondre(self.unique, {'id': self.u_ok[0]}).status_code, 400)
        self.assertFalse(QuizReponse.objects.filter(correcte=True).exists())

    def test_terminer_calcule_le_score_une_seule_fois(self):
        self._repondre(self.unique, self.u_ok)
        self._repondre(self.multiple, self.m_ok[:1])
        r = self.alice.post(f'/api/quiz/{self.sid}/terminer/')
        self.assertEqual(r.status_code, 200)
        # 1 bonne, 1 fausse, 1 sans réponse.
        self.assertEqual((r.json()['score'], r.json()['nombre_questions']), (1, 3))
        self.assertIsNotNone(r.json()['date_fin'])
        self.tache_analyse.delay.assert_called_once_with('alice@ssolab.local')
        # Session close : plus de réponse, et terminer une seconde fois ne change rien.
        self.assertEqual(self._repondre(self.multiple, self.m_ok).status_code, 400)
        self.assertEqual(self._repondre(self.vf, self.v_ok).status_code, 400)
        r2 = self.alice.post(f'/api/quiz/{self.sid}/terminer/')
        self.assertEqual((r2.json()['score'], r2.json()['date_fin']), (1, r.json()['date_fin']))
        self.assertEqual(self.tache_analyse.delay.call_count, 1)
        self.assertEqual(QuizSession.objects.get().score, 1)

    def test_detail_d_une_session_terminee_avec_corrections(self):
        self._repondre(self.unique, self.u_ok)
        self.alice.post(f'/api/quiz/{self.sid}/terminer/')
        d = self.alice.get(f'/api/quiz/{self.sid}/').json()
        self.assertEqual(len(d['reponses_donnees']), 3)
        ligne = next(l for l in d['reponses_donnees'] if l['question']['id'] == self.unique.id)
        self.assertEqual((ligne['correcte'], ligne['reponses_choisies']), (True, self.u_ok))
        self.assertTrue(any(x['correcte'] for x in ligne['question']['reponses']))

    def test_entrees_mal_formees_refusees_proprement(self):
        """Corrigé le 2026-10-11 : ces entrées donnaient une erreur 500."""
        for temps in ('vite', -5, 1.5, True, 2 ** 31, [1], {'ms': 1}):
            with self.subTest(temps_ms=temps):
                self.assertEqual(self._repondre(self.unique, self.u_ok, temps_ms=temps).status_code, 400)
        # Refusée, la réponse n'est pas enregistrée.
        self.assertFalse(QuizReponse.objects.filter(correcte=True).exists())
        for question in ('abc', '', None, -1, 1.5, True, [self.unique.id], {'id': self.unique.id}):
            with self.subTest(question=question):
                r = self.alice.post(f'/api/quiz/{self.sid}/repondre/',
                                    {'question': question, 'reponses_choisies': []}, format='json')
                self.assertEqual(r.status_code, 400)
        for themes in (5, 'tous', {'id': 1}, True):
            with self.subTest(themes=themes):
                self.assertEqual(self.alice.post('/api/quiz/demarrer/', {'themes': themes}, format='json').status_code, 400)
        self.assertEqual(QuizSession.objects.count(), 1)

    def test_entrees_tolerees(self):
        # Ce que le frontend envoie réellement continue de passer.
        self.assertEqual(self._repondre(self.unique, self.u_ok, temps_ms=None).status_code, 200)
        self.assertEqual(QuizReponse.objects.get(session_id=self.sid, question=self.unique).temps_ms, 0)
        self.assertEqual(self._repondre(self.vf, self.v_ok, temps_ms='1500').status_code, 200)
        self.assertEqual(QuizReponse.objects.get(session_id=self.sid, question=self.vf).temps_ms, 1500)
        r = self.alice.post(f'/api/quiz/{self.sid}/repondre/',
                            {'question': str(self.multiple.id), 'reponses_choisies': self.m_ok}, format='json')
        self.assertEqual((r.status_code, r.json()['correcte']), (200, True))
        for themes in (None, [], ['abc']):
            self.assertEqual(self.alice.post('/api/quiz/demarrer/', {'themes': themes}, format='json').status_code, 201)

    def test_seconde_reponse_refusee_la_premiere_compte(self):
        premiere = self._repondre(self.unique, self.u_ko[:1], temps_ms=800)
        self.assertEqual(premiere.status_code, 200)
        # La correction vient d'être rendue : s'en servir pour re-répondre est refusé.
        bonnes = [x['id'] for x in premiere.json()['question']['reponses'] if x['correcte']]
        seconde = self._repondre(self.unique, bonnes, temps_ms=900)
        self.assertEqual(seconde.status_code, 409)
        self.assertNotIn('correcte', seconde.json())
        qr = QuizReponse.objects.get(session_id=self.sid, question=self.unique)
        self.assertEqual((qr.correcte, qr.reponses_choisies, qr.temps_ms), (False, self.u_ko[:1], 800))
        # Renvoi à l'identique (double clic) : refusé aussi, sans rien changer.
        self.assertEqual(self._repondre(self.unique, self.u_ko[:1], temps_ms=800).status_code, 409)
        # Les autres questions restent ouvertes, et le score ne compte que les premières réponses.
        self.assertEqual(self._repondre(self.multiple, self.m_ok).status_code, 200)
        self.assertEqual(self.alice.post(f'/api/quiz/{self.sid}/terminer/').json()['score'], 1)

    def test_une_reponse_vide_sans_temps_compte_aussi_comme_reponse(self):
        # Sinon : répondre « rien » pour lire la correction, puis répondre juste.
        r = self._repondre(self.unique, [])
        self.assertEqual((r.status_code, r.json()['correcte']), (200, False))
        self.assertEqual(self._repondre(self.unique, self.u_ok).status_code, 409)
        self.assertFalse(QuizReponse.objects.get(session_id=self.sid, question=self.unique).correcte)
        # Répondue, sa correction apparaît dans le détail de la session ouverte.
        lignes = {l['question']['id']: l for l in self.alice.get(f'/api/quiz/{self.sid}/').json()['reponses_donnees']}
        self.assertTrue(any(x.get('correcte') for x in lignes[self.unique.id]['question']['reponses']))


class BanqueDeQuestionsTests(CasRoute):

    def setUp(self):
        super().setUp()
        self.theme = creer_theme()

    def _corps(self, **plus):
        return {'theme': self.theme.id, 'enonce': 'Vitesse en ville ?', 'type': 'qcm_unique', 'difficulte': 'facile',
                'reponses': [{'texte': '50 km/h', 'correcte': True}, {'texte': '70 km/h', 'correcte': False}], **plus}

    def test_creation_avec_reponses_et_origine_imposee(self):
        r = self.admin.post('/api/questions/', self._corps(origine='ia', generation=999), format='json')
        self.assertEqual(r.status_code, 201)
        q = Question.objects.get()
        # Une saisie manuelle ne peut pas se faire passer pour une génération IA.
        self.assertEqual((q.origine, q.generation_id, q.statut), ('humaine', None, 'validee'))
        self.assertEqual(sorted(q.reponses.values_list('texte', 'correcte')), [('50 km/h', True), ('70 km/h', False)])

    def test_mise_a_jour_des_reponses_sans_toucher_celles_d_une_autre_question(self):
        self.admin.post('/api/questions/', self._corps(), format='json')
        q = Question.objects.get()
        gardee, retiree = q.reponses.order_by('id')
        autre, autre_ok, _ = creer_question(self.theme, 'Autre')
        r = self.admin.patch(f'/api/questions/{q.id}/', {'reponses': [
            {'id': gardee.id, 'texte': '50 km/h (agglomération)', 'correcte': True},
            {'texte': '30 km/h', 'correcte': False},
            # Identifiant d'une réponse d'une AUTRE question : ne doit pas la modifier.
            {'id': autre_ok[0], 'texte': 'détournée', 'correcte': False},
        ]}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(sorted(q.reponses.values_list('texte', flat=True)),
                         ['30 km/h', '50 km/h (agglomération)', 'détournée'])
        self.assertTrue(q.reponses.filter(id=gardee.id).exists())
        self.assertFalse(Reponse.objects.filter(id=retiree.id).exists())
        intacte = Reponse.objects.get(id=autre_ok[0])
        self.assertEqual((intacte.question_id, intacte.texte, intacte.correcte), (autre.id, 'Stop', True))

    def test_modifier_sans_reponses_les_conserve(self):
        self.admin.post('/api/questions/', self._corps(), format='json')
        q = Question.objects.get()
        self.assertEqual(self.admin.patch(f'/api/questions/{q.id}/', {'enonce': 'Reformulée'}, format='json').status_code, 200)
        self.assertEqual(q.reponses.count(), 2)

    def test_valider_rejeter_et_tirage(self):
        q, _, _ = creer_question(self.theme, 'Générée', statut='proposee', origine='ia')

        def tirables():
            r = self.alice.post('/api/quiz/demarrer/', {'nombre_questions': 50}, format='json')
            return [x['id'] for x in r.json().get('questions', [])]

        self.assertEqual(tirables(), [])
        r = self.admin.post(f'/api/questions/{q.id}/valider/')
        self.assertEqual((r.status_code, r.json()['statut'], r.json()['origine']), (200, 'validee', 'ia'))
        self.assertEqual(tirables(), [q.id])
        r = self.admin.post(f'/api/questions/{q.id}/rejeter/')
        self.assertEqual(r.json()['statut'], 'rejetee')
        self.assertEqual(tirables(), [])
        # Rejetée, elle reste en base (traçabilité).
        self.assertTrue(Question.objects.filter(pk=q.id).exists())

    def test_filtres_de_la_banque(self):
        creer_question(self.theme, 'A')
        creer_question(self.theme, 'B', statut='proposee')
        creer_question(creer_theme('Autre'), 'C')
        self.assertEqual([q['enonce'] for q in self.admin.get('/api/questions/?statut=proposee').json()], ['B'])
        self.assertEqual({q['enonce'] for q in self.admin.get(f'/api/questions/?theme={self.theme.id}').json()}, {'A', 'B'})


class IllustrationsTests(CasRoute):
    """Fichiers dans `storage`, au nom de l'utilisateur (jeton transmis tel quel)."""

    def setUp(self):
        super().setUp()
        self.theme = creer_theme()
        self.depots, self.suppressions = [], []

        def post(url, headers=None, data=None, files=None, timeout=None):
            self.depots.append({'url': url, 'auth': headers['Authorization'], 'chemin': data['relative_path'],
                                'nom': files['file'][0], 'type': files['file'][2], 'timeout': timeout})
            return mock.Mock(status_code=201, json=lambda: {'relative_path': data['relative_path']})

        def delete(url, headers=None, timeout=None):
            self.suppressions.append((url, headers['Authorization']))
            return mock.Mock(status_code=204)

        self.http_post.side_effect = post
        self.http_delete.side_effect = delete

    def _image(self, nom='panneau.png'):
        return SimpleUploadedFile(nom, b'\x89PNG', content_type='image/png')

    def _creer_fiche(self, **plus):
        r = self.admin.post('/api/fiches/', {'theme': self.theme.id, 'titre': 'Fiche', 'contenu': 'texte', **plus},
                            format='multipart')
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()

    def test_depot_au_nom_de_l_utilisateur_dans_le_partage_de_l_app(self):
        fiche = self._creer_fiche(illustration_file=self._image())
        depot, = self.depots
        self.assertEqual(depot['url'], 'http://storage.test/api/files/code-route/')
        self.assertEqual(depot['auth'], f'Bearer {self.admin.jeton}')
        self.assertRegex(depot['chemin'], r'^fiches/[0-9a-f]{32}-panneau\.png$')
        self.assertEqual((depot['nom'], depot['type']), ('panneau.png', 'image/png'))
        self.assertTrue(depot['timeout'])
        self.assertEqual(fiche['illustration_path'], depot['chemin'])
        self.assertNotIn('illustration_file', fiche)

    def test_remplacement_supprime_l_ancien_fichier(self):
        fiche = self._creer_fiche(illustration_file=self._image())
        ancien = fiche['illustration_path']
        r = self.admin.patch(f"/api/fiches/{fiche['id']}/", {'illustration_file': self._image('neuf.png')},
                             format='multipart')
        self.assertEqual(r.status_code, 200)
        self.assertNotEqual(r.json()['illustration_path'], ancien)
        self.assertEqual(self.suppressions,
                         [(f'http://storage.test/api/files/code-route/content/{ancien}', f'Bearer {self.admin.jeton}')])
        # Modifier le texte seul ne touche à aucun fichier.
        self.admin.patch(f"/api/fiches/{fiche['id']}/", {'titre': 'Autre titre'}, format='json')
        self.assertEqual((len(self.depots), len(self.suppressions)), (2, 1))

    def test_suppression_emporte_le_fichier_possede(self):
        fiche = self._creer_fiche(illustration_file=self._image())
        self.assertEqual(self.admin.delete(f"/api/fiches/{fiche['id']}/").status_code, 204)
        self.assertEqual(len(self.suppressions), 1)
        self.assertIn(fiche['illustration_path'], self.suppressions[0][0])

    def test_une_image_de_la_banque_partagee_n_est_jamais_supprimee(self):
        """`wikimedia/…` peut illustrer plusieurs fiches et questions : jamais possédée."""
        fiche = self._creer_fiche(illustration_path='wikimedia/stop.png', illustration_credit='CC BY-SA')
        self.assertEqual(self.depots, [])
        self.admin.patch(f"/api/fiches/{fiche['id']}/", {'illustration_file': self._image()}, format='multipart')
        autre = self._creer_fiche(illustration_path='wikimedia/stop.png')
        self.admin.delete(f"/api/fiches/{autre['id']}/")
        q, _, _ = creer_question(self.theme, illustration_path='wikimedia/stop.png')
        self.admin.delete(f'/api/questions/{q.id}/')
        self.assertEqual(self.suppressions, [])
        # Une question, elle, possède son image déposée.
        q, _, _ = creer_question(self.theme, illustration_path='questions/abc-x.png')
        self.admin.delete(f'/api/questions/{q.id}/')
        self.assertEqual(len(self.suppressions), 1)

    def test_lecture_de_l_illustration_d_une_fiche(self):
        sans = FicheCours.objects.create(theme=self.theme, titre='Sans image', contenu='x')
        self.assertEqual(self.alice.get(f'/api/fiches/{sans.id}/illustration/').status_code, 404)
        avec = FicheCours.objects.create(theme=self.theme, titre='Avec', contenu='x',
                                         illustration_path='fiches/abc-panneau.png')
        self.http_get.side_effect = None
        self.http_get.return_value = mock.Mock(status_code=200, iter_content=lambda chunk_size: [b'\x89PN', b'G'])
        r = self.alice.get(f'/api/fiches/{avec.id}/illustration/')
        self.assertEqual((r.status_code, r['Content-Type']), (200, 'image/png'))
        self.assertEqual(b''.join(r.streaming_content), b'\x89PNG')
        appel = self.http_get.call_args
        self.assertEqual(appel.args[0], 'http://storage.test/api/files/code-route/content/fiches/abc-panneau.png')
        # C'est le jeton de la lectrice qui part vers storage, pas celui d'un admin.
        self.assertEqual(appel.kwargs['headers'], {'Authorization': f'Bearer {self.alice.jeton}'})

    def test_banque_d_images_disponibles(self):
        manifeste = [{'relative_path': 'wikimedia/stop.png', 'nom': 'Stop', 'credit': 'CC'}]
        self.http_get.side_effect = None
        self.http_get.return_value = mock.Mock(
            status_code=200, iter_content=lambda chunk_size: [json.dumps(manifeste).encode()])
        self.assertEqual(self.admin.get('/api/illustrations-disponibles/').json(), manifeste)
        self.assertTrue(self.http_get.call_args.args[0].endswith('/content/wikimedia/manifest.json'))
        # Manifeste absent ou storage en panne : liste vide, pas une erreur.
        self.http_get.return_value = mock.Mock(status_code=404)
        self.assertEqual(self.admin.get('/api/illustrations-disponibles/').json(), [])
        self.http_get.side_effect = requests.ConnectionError('injoignable')
        self.assertEqual(self.admin.get('/api/illustrations-disponibles/').json(), [])

    def test_erreurs_de_storage(self):
        self.http_post.side_effect = None
        self.http_post.return_value = mock.Mock(status_code=403, text='interdit')
        with self.assertRaises(storage_client.StorageClientError):
            storage_client.upload('Bearer x', 'fiches/a.png', self._image(), 'a.png')
        self.http_post.side_effect = requests.Timeout('trop long')
        with self.assertRaises(storage_client.StorageClientError):
            storage_client.upload('Bearer x', 'fiches/a.png', self._image(), 'a.png')
        self.http_delete.side_effect = None
        self.http_delete.return_value = mock.Mock(status_code=404)      # déjà supprimé : toléré
        storage_client.delete('Bearer x', 'fiches/a.png')
        self.http_delete.return_value = mock.Mock(status_code=500)
        with self.assertRaises(storage_client.StorageClientError):
            storage_client.delete('Bearer x', 'fiches/a.png')


class AnalyseDesResultatsTests(CasRoute):
    """Tâche Celery de fin de quiz, jouée en appel direct."""

    def setUp(self):
        super().setUp()
        self.signal, self.prio = creer_theme('Signalisation'), creer_theme('Priorités', 1)
        self.questions = [creer_question(self.signal, f'S{i}') for i in range(3)] + [creer_question(self.prio, 'P0')]

    def _jouer(self, c, bonnes):
        """Quiz complet : répond juste aux questions dont l'énoncé est dans `bonnes`."""
        sid = c.post('/api/quiz/demarrer/', {'nombre_questions': 50}, format='json').json()['session']['id']
        for q, ok, ko in self.questions:
            c.post(f'/api/quiz/{sid}/repondre/',
                   {'question': q.id, 'reponses_choisies': ok if q.enonce in bonnes else ko[:1]}, format='json')
        c.post(f'/api/quiz/{sid}/terminer/')

    def test_sans_reponse_pas_d_analyse(self):
        tasks.analyser_resultats('alice@ssolab.local')
        self.assertEqual(AnalyseIA.objects.count(), 0)

    def test_statistiques_par_theme_et_repli_sans_mistral(self):
        self._jouer(self.alice, {'S0'})
        self._jouer(self.bob, {'S0', 'S1', 'S2', 'P0'})        # ne doit pas entrer dans le bilan d'Alice
        tasks.analyser_resultats('Alice@SSOLAB.local')
        analyse = AnalyseIA.objects.get()
        self.assertEqual(analyse.contenu, {'stats_par_theme': {
            'Signalisation': {'total': 3, 'correctes': 1, 'taux_reussite': 33},
            'Priorités': {'total': 1, 'correctes': 0, 'taux_reussite': 0},
        }})
        self.assertIn('activez Mistral', analyse.resume_texte)
        self.Mistral.assert_not_called()

    def test_diagnostic_mistral_et_contexte_transmis(self):
        self.activer_mistral()
        self.mistral_repond(json.dumps({'resume': 'Bravo, continuez.', 'points_faibles': ['Priorités']}))
        self._jouer(self.alice, {'S0', 'S1'})
        tasks.analyser_resultats('alice@ssolab.local')
        analyse = AnalyseIA.objects.get()
        self.assertEqual(analyse.resume_texte, 'Bravo, continuez.')
        self.assertEqual(analyse.contenu['diagnostic']['points_faibles'], ['Priorités'])
        self.assertEqual(analyse.contenu['stats_par_theme']['Signalisation']['taux_reussite'], 67)
        envoi = self.mistral.chat.complete.call_args.kwargs
        self.assertEqual(envoi['model'], 'mistral-test')
        message = envoi['messages'][1]['content']
        self.assertIn('- Signalisation : 2/3 bonnes réponses (67%)', message)
        # Les questions ratées, avec le piège de la réponse choisie — pas les réussies.
        self.assertIn('« S2 » — piège : piège : Cédez', message)
        self.assertIn('« P0 »', message)
        self.assertNotIn('« S0 »', message)
        self.Mistral.assert_called_with(api_key=CLE_MISTRAL)
        # Rendu par « Mon bilan ».
        self.assertEqual(self.alice.get('/api/mon-bilan/').json()['resume_texte'], 'Bravo, continuez.')

    def test_panne_mistral_le_bilan_existe_quand_meme(self):
        self.activer_mistral()
        self.mistral.chat.complete.side_effect = RuntimeError('503 Service Unavailable')
        self._jouer(self.alice, set())
        tasks.analyser_resultats('alice@ssolab.local')
        analyse = AnalyseIA.objects.get()
        self.assertIn("n'a pas pu être générée", analyse.resume_texte)
        self.assertNotIn('diagnostic', analyse.contenu)
        self.assertEqual(self.mistral.chat.complete.call_count, 3)      # 1 essai + 2 reprises

    def test_questions_ratees_bornees_aux_plus_recentes(self):
        self.activer_mistral()
        self.mistral_repond('{"resume": "ok"}')
        self.questions = [creer_question(self.signal, f'N{i:02d}') for i in range(20)]
        self._jouer(self.alice, set())
        tasks.analyser_resultats('alice@ssolab.local')
        message = self.mistral.chat.complete.call_args.kwargs['messages'][1]['content']
        self.assertEqual(message.count('— piège :'), tasks.NB_QUESTIONS_RATEES_CONTEXTE)


class GenerationDeQuestionsTests(CasRoute):
    """Tâche Celery de génération : jamais de question IA servie sans validation humaine."""

    PRODUCTION = {'questions': [
        {'enonce': 'Nouvelle 1', 'type': 'qcm_unique', 'explication_generale': 'parce que',
         'reponses': [{'texte': 'oui', 'correcte': True, 'explication': None}, {'texte': 'non', 'correcte': False}]},
        {'enonce': 'Sans bonne réponse', 'reponses': [{'texte': 'a', 'correcte': False}]},
        {'enonce': 'Sans réponse du tout'},
        {'enonce': 'Nouvelle 2', 'type': 'vrai_faux', 'reponses': [{'texte': 'vrai', 'correcte': True}]},
    ]}

    def setUp(self):
        super().setUp()
        self.theme = creer_theme()
        self.exemple, _, _ = creer_question(self.theme, 'Exemple validé', explication_generale='règle')
        creer_question(self.theme, 'Exemple difficile', difficulte='difficile')
        creer_question(self.theme, 'Exemple non validé', statut='proposee')
        creer_question(creer_theme('Autre'), 'Exemple autre thème')

    def _generation(self, **plus):
        return GenerationIA.objects.create(theme=self.theme, difficulte='facile', nombre_demande=4, **plus)

    def test_lancement_borne_et_tache_envoyee(self):
        url = '/api/generation-ia/lancer/'
        self.assertEqual(self.admin.post(url, {'theme_id': 999999, 'difficulte': 'facile'}, format='json').status_code, 404)
        self.assertEqual(self.admin.post(url, {'theme_id': self.theme.id, 'difficulte': 'expert'}, format='json').status_code, 400)
        self.assertEqual(self.admin.post(url, {'theme_id': self.theme.id, 'difficulte': 'facile',
                                               'nombre_demande': 'plein'}, format='json').status_code, 400)
        self.tache_generation.delay.assert_not_called()
        self.assertEqual(GenerationIA.objects.count(), 0)
        for demande, attendu in ((3, 3), (0, 1), (500, 20), (None, 5)):
            corps = {'theme_id': self.theme.id, 'difficulte': 'moyen', 'deepsearch': True}
            if demande is not None:
                corps['nombre_demande'] = demande
            r = self.admin.post(url, corps, format='json')
            self.assertEqual((r.status_code, r.json()['nombre_demande'], r.json()['statut'], r.json()['deepsearch']),
                             (201, attendu, 'en_cours', True))
            self.tache_generation.delay.assert_called_with(r.json()['id'])

    def test_sans_exemple_valide_pas_d_appel_a_l_ia(self):
        self.activer_mistral()
        g = GenerationIA.objects.create(theme=self.theme, difficulte='moyen', nombre_demande=3)
        tasks.generer_questions(g.id)
        g.refresh_from_db()
        self.assertEqual(g.statut, 'erreur')
        self.assertIn('amorçage manuel', g.erreur_message)
        self.Mistral.assert_not_called()

    def test_questions_produites_proposees_jamais_validees(self):
        self.activer_mistral()
        self.mistral_repond(json.dumps(self.PRODUCTION))
        g = self._generation()
        tasks.generer_questions(g.id)
        g.refresh_from_db()
        self.assertEqual((g.statut, g.nombre_genere, g.modele, g.erreur_message), ('terminee', 2, 'mistral-test', ''))
        produites = Question.objects.filter(generation=g).order_by('id')
        self.assertEqual([q.enonce for q in produites], ['Nouvelle 1', 'Nouvelle 2'])
        for q in produites:
            self.assertEqual((q.origine, q.statut, q.theme_id, q.difficulte), ('ia', 'proposee', self.theme.id, 'facile'))
        self.assertEqual(list(produites[0].reponses.order_by('id').values_list('texte', 'correcte', 'explication')),
                         [('oui', True, ''), ('non', False, '')])
        # L'échantillon : seulement le validé du même thème et de la même difficulté.
        self.assertIn('« Exemple validé »', g.prompt_utilise)
        self.assertIn('Stop [correcte]', g.prompt_utilise)
        for absent in ('Exemple difficile', 'Exemple non validé', 'Exemple autre thème'):
            self.assertNotIn(absent, g.prompt_utilise)
        # Aucune n'entre dans un quiz avant validation humaine.
        tirees = self.alice.post('/api/quiz/demarrer/', {'themes': [self.theme.id], 'difficulte': 'facile',
                                                         'nombre_questions': 50}, format='json').json()['questions']
        self.assertEqual([q['id'] for q in tirees], [self.exemple.id])
        # Le suivi rend les questions produites à l'administrateur.
        suivi = self.admin.get(f'/api/generation-ia/{g.id}/statut/').json()
        self.assertEqual((suivi['statut'], len(suivi['questions'])), ('terminee', 2))

    def test_rien_d_exploitable(self):
        self.activer_mistral()
        self.mistral_repond(json.dumps({'questions': self.PRODUCTION['questions'][1:3]}))
        g = self._generation()
        tasks.generer_questions(g.id)
        g.refresh_from_db()
        self.assertEqual((g.statut, g.nombre_genere), ('erreur', 0))
        self.assertIn('aucune question exploitable', g.erreur_message)
        self.assertEqual(Question.objects.filter(origine='ia').count(), 0)

    def test_mistral_absent_ou_en_panne(self):
        g = self._generation()
        tasks.generer_questions(g.id)          # aucune clé active
        g.refresh_from_db()
        self.assertEqual(g.statut, 'erreur')
        self.assertIn('Aucune clé Mistral active', g.erreur_message)
        self.assertIn('Exemple validé', g.prompt_utilise)

        self.activer_mistral()
        self.mistral.chat.complete.side_effect = RuntimeError('401 Unauthorized')
        g2 = self._generation()
        tasks.generer_questions(g2.id)
        g2.refresh_from_db()
        self.assertEqual(g2.statut, 'erreur')
        self.assertIn('Appel Mistral en échec', g2.erreur_message)
        self.assertEqual(self.mistral.chat.complete.call_count, 1)      # clé refusée : pas de reprise

        self.mistral_repond('Voici vos questions : …')
        g3 = self._generation()
        tasks.generer_questions(g3.id)
        g3.refresh_from_db()
        self.assertEqual(g3.statut, 'erreur')
        self.assertIn('JSON invalide', g3.erreur_message)

    def test_recherche_web_facultative(self):
        self.activer_mistral()
        self.mistral_repond(json.dumps(self.PRODUCTION))
        # Recherche réussie : son texte complète le prompt.
        self.mistral.beta.conversations.start.return_value = mock.Mock(
            conversation_id='c1', outputs=[mock.Mock(type='message.output', content='Limite : 50 km/h en ville.')])
        g = self._generation(deepsearch=True)
        tasks.generer_questions(g.id)
        g.refresh_from_db()
        self.assertEqual(g.statut, 'terminee')
        self.assertIn('Contexte vérifié par recherche web', g.prompt_utilise)
        self.assertIn('Limite : 50 km/h en ville.', g.prompt_utilise)
        self.assertEqual(self.mistral.beta.agents.create.call_args.kwargs['tools'], [{'type': 'web_search'}])
        # Recherche en panne : la génération se fait quand même, sans ce contexte.
        self.mistral.beta.agents.create.side_effect = RuntimeError('400 web_search indisponible')
        g2 = self._generation(deepsearch=True)
        tasks.generer_questions(g2.id)
        g2.refresh_from_db()
        self.assertEqual((g2.statut, g2.nombre_genere), ('terminee', 2))
        self.assertNotIn('Contexte vérifié', g2.prompt_utilise)
        # Sans l'option, aucune recherche.
        self.mistral.beta.agents.create.reset_mock()
        tasks.generer_questions(self._generation().id)
        self.mistral.beta.agents.create.assert_not_called()

    def test_reponse_de_forme_inattendue_ne_laisse_pas_la_generation_en_cours(self):
        """Corrigé le 2026-10-11 : une exception dans la tâche laissait « en_cours » pour toujours."""
        self.activer_mistral()
        formes = [
            {'questions': ['Une question en texte libre']},
            ['pas', 'un', 'objet'],
            {'questions': {'enonce': 'un objet au lieu d\'une liste'}},
            {'questions': [{'enonce': 'x', 'reponses': 'oui'}]},
            {'questions': [{'enonce': 'x', 'reponses': [{'texte': None, 'correcte': True}]}]},
            # La première est bonne, la seconde casse : rien du lot n'est gardé.
            {'questions': [self.PRODUCTION['questions'][0], 'cassée']},
        ]
        for forme in formes:
            with self.subTest(forme=forme):
                self.mistral_repond(json.dumps(forme))
                g = self._generation()
                tasks.generer_questions(g.id)
                g.refresh_from_db()
                self.assertEqual((g.statut, g.nombre_genere), ('erreur', 0))
                self.assertIn('forme inattendue', g.erreur_message)
                self.assertEqual(Question.objects.filter(origine='ia').count(), 0)


class ClientMistralTests(CasRoute):

    def test_cle_absente_ou_configuration_inactive(self):
        for actif, cle in ((False, CLE_MISTRAL), (True, ''), (False, '')):
            with self.subTest(actif=actif, cle=bool(cle)):
                cfg = ConfigurationMistral.get()
                cfg.actif, cfg.api_key = actif, cle
                cfg.save()
                for appel in (lambda: mistral_client.completer_json('s', 'm', {}),
                              lambda: mistral_client.demarrer_conversation('i', 'm'),
                              lambda: mistral_client.continuer_conversation('c', 'm')):
                    with self.assertRaises(mistral_client.MistralNonConfigure):
                        appel()
        self.Mistral.assert_not_called()

    def test_reprises_sur_erreur_passagere_seulement(self):
        self.activer_mistral(modele='   ')
        ok = mock.Mock(choices=[mock.Mock(message=mock.Mock(content='{"a": 1}'))])
        self.mistral.chat.complete.side_effect = [RuntimeError('429 Too Many Requests'), RuntimeError('timeout'), ok]
        self.assertEqual(mistral_client.completer_json('sys', 'msg', {'type': 'object'}), {'a': 1})
        self.assertEqual([c.args[0] for c in self.sommeil.call_args_list], mistral_client.RETRY_DELAYS)
        envoi = self.mistral.chat.complete.call_args.kwargs
        self.assertEqual(envoi['model'], 'mistral-large-latest')        # modèle vide : valeur par défaut
        self.assertEqual(envoi['response_format'], {'type': 'json_object'})
        self.assertIn('sys', envoi['messages'][0]['content'])

        self.sommeil.reset_mock()
        self.mistral.chat.complete.side_effect = [RuntimeError('401 Unauthorized'), ok]
        with self.assertRaises(mistral_client.MistralError):
            mistral_client.completer_json('s', 'm', {})
        self.sommeil.assert_not_called()

        self.mistral.chat.complete.side_effect = RuntimeError('503')
        self.mistral.chat.complete.reset_mock(side_effect=False)
        with self.assertRaises(mistral_client.MistralError):
            mistral_client.completer_json('s', 'm', {})
        self.assertEqual(self.mistral.chat.complete.call_count, 3)

    def test_lecture_d_une_reponse_de_conversation(self):
        lire = mistral_client._parser_reponse_conversation
        simple = mock.Mock(conversation_id='c1', outputs=[
            mock.Mock(type='tool.execution', content='ignoré'),
            mock.Mock(type='message.output', content='  Bonjour.  ')])
        self.assertEqual(lire(simple), {'conversation_id': 'c1', 'texte': 'Bonjour.', 'citations': []})
        morceaux = mock.Mock(conversation_id=None, outputs=[mock.Mock(type='message.output', content=[
            mock.Mock(type='text', text='En ville : '),
            mock.Mock(type='tool_reference', title='Légifrance', url='https://legifrance.test/r413'),
            mock.Mock(type='text', text='50 km/h.')])])
        self.assertEqual(lire(morceaux, conversation_id_repli='c9'), {
            'conversation_id': 'c9', 'texte': 'En ville : 50 km/h.',
            'citations': [{'title': 'Légifrance', 'url': 'https://legifrance.test/r413'}]})
        self.assertEqual(lire(mock.Mock(conversation_id='c', outputs=None))['texte'], '')


class AssistantFichesTests(CasRoute):

    URL = '/api/assistant-fiches/message/'

    def setUp(self):
        super().setUp()
        self.theme = creer_theme()
        FicheCours.objects.create(theme=self.theme, titre='Le stop', contenu='Arrêt absolu.', ordre=1)
        FicheCours.objects.create(theme=creer_theme('Autre'), titre='Hors thème', contenu='x')
        self.activer_mistral()
        self.mistral.beta.agents.create.return_value = mock.Mock(id='agent-1')

    def _reponse(self, texte, conversation_id='conv-1'):
        r = mock.Mock(conversation_id=conversation_id, outputs=[mock.Mock(type='message.output', content=texte)])
        self.mistral.beta.conversations.start.return_value = r
        self.mistral.beta.conversations.append.return_value = r

    def test_premier_message_avec_les_fiches_du_theme_en_contexte(self):
        self._reponse('Que voulez-vous corriger ?')
        r = self.admin.post(self.URL, {'message': ' Relis la fiche ', 'theme_id': self.theme.id}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'conversation_id': 'conv-1', 'reponse_texte': 'Que voulez-vous corriger ?',
                                    'proposition': None, 'citations': []})
        agent = self.mistral.beta.agents.create.call_args.kwargs
        self.assertIn('Le stop', agent['instructions'])
        self.assertIn('Arrêt absolu.', agent['instructions'])
        self.assertNotIn('Hors thème', agent['instructions'])
        self.assertEqual((agent['tools'], agent['model']), ([], 'mistral-test'))
        self.mistral.beta.conversations.start.assert_called_once_with(agent_id='agent-1', inputs='Relis la fiche')

    def test_recherche_web_a_la_demande(self):
        self._reponse('ok')
        self.admin.post(self.URL, {'message': 'x', 'theme_id': self.theme.id, 'deepsearch': True}, format='json')
        self.assertEqual(self.mistral.beta.agents.create.call_args.kwargs['tools'], [{'type': 'web_search'}])

    def test_suite_de_conversation(self):
        self._reponse('Suite.', conversation_id=None)
        r = self.admin.post(self.URL, {'message': 'continue', 'conversation_id': 'conv-7'}, format='json')
        self.assertEqual((r.status_code, r.json()['conversation_id']), (200, 'conv-7'))
        self.mistral.beta.conversations.append.assert_called_once_with(conversation_id='conv-7', inputs='continue')
        self.mistral.beta.agents.create.assert_not_called()

    def test_proposition_extraite_jamais_appliquee(self):
        proposition = {'action': 'modifier', 'fiche_id': 1, 'titre': 'Le stop', 'contenu': 'Arrêt {absolu}.',
                       'illustration_credit': ''}
        cas = [
            (f'Voici.\n```json\n{json.dumps(proposition)}\n```', proposition),
            ('```json\n{"action": "supprimer", "fiche_id": 1}\n```', None),      # action hors liste
            ('```json\n{"action": "creer", \n```', None),                         # JSON cassé
            ('{"action": "creer"} sans bloc de code', None),
            ('Une simple question ?', None),
        ]
        for texte, attendu in cas:
            with self.subTest(texte=texte[:30]):
                self._reponse(texte)
                r = self.admin.post(self.URL, {'message': 'x', 'theme_id': self.theme.id}, format='json')
                self.assertEqual(r.json()['proposition'], attendu)
        # Rien n'est écrit : c'est l'administrateur qui applique.
        self.assertEqual(FicheCours.objects.get(theme=self.theme).contenu, 'Arrêt absolu.')
        self.assertEqual(FicheCours.objects.count(), 2)

    def test_demandes_refusees_et_pannes(self):
        self.assertEqual(self.admin.post(self.URL, {'message': '  ', 'theme_id': self.theme.id}, format='json').status_code, 400)
        self.assertEqual(self.admin.post(self.URL, {'message': 'x', 'theme_id': 999999}, format='json').status_code, 404)
        self.Mistral.assert_not_called()
        self.mistral.beta.agents.create.side_effect = RuntimeError('500')
        self.assertEqual(self.admin.post(self.URL, {'message': 'x', 'theme_id': self.theme.id}, format='json').status_code, 502)
        ConfigurationMistral.objects.update(actif=False)
        r = self.admin.post(self.URL, {'message': 'x', 'theme_id': self.theme.id}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('Aucune clé Mistral active', r.json()['detail'])
