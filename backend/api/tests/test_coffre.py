"""Coffre des secrets (contrat failles, I3) : clé propre au coffre, lecture de
l'ancien chiffrement, migration qui rechiffre, valeur corrompue = absente."""
import base64
import hashlib
import importlib

from cryptography.fernet import Fernet, InvalidToken
from django.apps import apps as django_apps
from django.db import connection
from django.test import TestCase, override_settings

from api.models import ConfigurationMistral

CLE_COFFRE = Fernet.generate_key().decode()
SECRET = 'secret-de-test-pour-le-coffre'
CLE_MISTRAL = 'mistral-SECRET-0123456789abcdef'


def ancienne_cle(secret_key=SECRET):
    return base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())


def brut():
    with connection.cursor() as cur:
        cur.execute('SELECT api_key FROM configuration_mistral WHERE id = 1')
        return cur.fetchone()[0]


def ecrire_brut(valeur):
    ConfigurationMistral.objects.update_or_create(pk=1, defaults={'actif': True})
    with connection.cursor() as cur:
        cur.execute('UPDATE configuration_mistral SET api_key = %s WHERE id = 1', [valeur])


def rejouer_migration():
    module = importlib.import_module('api.migrations.0009_rechiffrer_coffre')

    class SchemaEditor:
        def __init__(self):
            self.connection = connection

        quote_name = staticmethod(connection.ops.quote_name)

    module.rechiffrer(django_apps, SchemaEditor())


@override_settings(SECRET_KEY=SECRET, VAULT_ENCRYPTION_KEY=CLE_COFFRE)
class CoffreTests(TestCase):

    def test_ecrit_sous_la_cle_du_coffre_et_jamais_sous_secret_key(self):
        cfg = ConfigurationMistral.get()
        cfg.api_key = CLE_MISTRAL
        cfg.save()
        valeur = brut()
        self.assertNotIn(CLE_MISTRAL, valeur)
        self.assertEqual(Fernet(CLE_COFFRE.encode()).decrypt(valeur.encode()).decode(), CLE_MISTRAL)
        with self.assertRaises(InvalidToken):
            Fernet(ancienne_cle()).decrypt(valeur.encode())

    def test_rotation_de_secret_key_ne_perd_plus_le_secret(self):
        cfg = ConfigurationMistral.get()
        cfg.api_key = CLE_MISTRAL
        cfg.save()
        with override_settings(SECRET_KEY='une-toute-autre-secret-key'):
            self.assertEqual(ConfigurationMistral.get().api_key, CLE_MISTRAL)

    def test_ancienne_cle_relue_puis_rechiffree_par_la_migration(self):
        ecrire_brut(Fernet(ancienne_cle()).encrypt(CLE_MISTRAL.encode()).decode())
        self.assertEqual(ConfigurationMistral.get().api_key, CLE_MISTRAL)  # lecture MultiFernet
        rejouer_migration()
        valeur = brut()
        self.assertEqual(Fernet(CLE_COFFRE.encode()).decrypt(valeur.encode()).decode(), CLE_MISTRAL)
        with self.assertRaises(InvalidToken):
            Fernet(ancienne_cle()).decrypt(valeur.encode())
        # L'ancienne SECRET_KEY peut maintenant tourner sans rien perdre.
        with override_settings(SECRET_KEY='nouvelle'):
            self.assertEqual(ConfigurationMistral.get().api_key, CLE_MISTRAL)

    def test_valeur_historique_en_clair_rendue_puis_chiffree(self):
        ecrire_brut(CLE_MISTRAL)
        self.assertEqual(ConfigurationMistral.get().api_key, CLE_MISTRAL)
        rejouer_migration()
        valeur = brut()
        self.assertNotEqual(valeur, CLE_MISTRAL)
        self.assertEqual(Fernet(CLE_COFFRE.encode()).decrypt(valeur.encode()).decode(), CLE_MISTRAL)

    def test_valeur_corrompue_traitee_comme_absente_et_journalisee_sans_sa_valeur(self):
        # Chiffrée sous une SECRET_KEY perdue : avant, ce texte chiffré était
        # rendu tel quel et envoyé à Mistral comme s'il était la clé.
        corrompu = Fernet(ancienne_cle('secret-key-perdue')).encrypt(CLE_MISTRAL.encode()).decode()
        ecrire_brut(corrompu)
        with self.assertLogs('api.fields', level='WARNING') as journal:
            self.assertEqual(ConfigurationMistral.get().api_key, '')
        self.assertNotIn(corrompu, '\n'.join(journal.output))
        self.assertNotIn(CLE_MISTRAL, '\n'.join(journal.output))

    def test_migration_laisse_intacte_une_valeur_indechiffrable(self):
        corrompu = Fernet(ancienne_cle('secret-key-perdue')).encrypt(CLE_MISTRAL.encode()).decode()
        ecrire_brut(corrompu)
        with self.assertLogs('api.migrations.0009_rechiffrer_coffre', level='WARNING') as journal:
            rejouer_migration()
        self.assertEqual(brut(), corrompu)
        self.assertNotIn(corrompu, '\n'.join(journal.output))

    def test_valeur_vide_inchangee(self):
        ecrire_brut('')
        rejouer_migration()
        self.assertEqual(brut(), '')
        self.assertEqual(ConfigurationMistral.get().api_key, '')
