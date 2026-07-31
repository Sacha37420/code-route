"""Amorçage de la page « Autres ressources » — tarifs vérifiés le 2026-07-31
(recherche fraîche, pas une recopie du brief de conception). À revérifier
périodiquement : ces prix évoluent souvent (cf. to_do_code_route.md)."""
import datetime

from django.db import migrations

VERIF = datetime.date(2026, 7, 31)

SITES = [
    (
        'Sécurité routière (site officiel)',
        'https://www.securite-routiere.gouv.fr/passer-son-permis-de-conduire/preparation-de-lexamen-du-code-de-la-route',
        'gratuit',
        "Site officiel de la Sécurité routière — ressources de préparation à l'examen théorique. "
        "Pas un simulateur d'examen blanc complet comme les acteurs commerciaux.",
    ),
    (
        'Prévention Routière',
        'https://www.preventionroutiere.asso.fr/tests-code-de-la-route/',
        'gratuit',
        '4 tests gratuits proposés (partenariat superCode/digiSchool). Moins de contenu que les '
        'plateformes commerciales, mais aucune inscription ni carte bancaire requise.',
    ),
    (
        'Passe ton Code',
        'https://www.passetoncode.fr/',
        'gratuit',
        "Tests illimités et cours gratuits, confirmé 100% gratuit à la vérification (aucun "
        "abonnement payant identifié). Propose aussi l'inscription à l'examen officiel.",
    ),
    (
        'Codeclic',
        'https://www.codeclic.com/gratuit.php',
        'freemium',
        "Gratuit : 6 séries de 40 questions (240 questions). Offre complète à 17 € : accès "
        "illimité à 3 000 questions conformes 2026 (thèmes rares inclus : matières dangereuses, "
        "signalisation temporaire complexe).",
    ),
    (
        'Ornikar',
        'https://www.ornikar.com/code',
        'freemium',
        "Abonnement à partir de 2,99 €/mois (3 mois : 7,99 € ; 6 mois : 14,99 €). Plus de 1 700 "
        "questions conformes 2026, 135 fiches de cours, examens blancs illimités.",
    ),
    (
        'Codes Rousseau — Pass Rousseau',
        'https://www.envoituresimone.com/code-de-la-route/guides/code-rousseau',
        'payant',
        "Sources contradictoires au moment de la vérification (entre 19 € et 39,90 € pour 6 mois "
        "selon le revendeur) — vérifier directement sur le site de l'éditeur avant de s'engager. "
        "2 400 questions officielles annoncées avec corrections vidéo.",
    ),
    (
        'Code en Poche',
        'https://www.codeenpoche.fr/',
        'gratuit',
        "Application gratuite (plus de 500 000 utilisateurs) : cours, 16 tests gratuits, examens "
        "blancs, fiches mémo. Aucun abonnement payant obligatoire identifié à la vérification.",
    ),
]


def load_data(apps, schema_editor):
    SiteExterne = apps.get_model('api', 'SiteExterne')
    for ordre, (nom, url, statut, resume) in enumerate(SITES):
        SiteExterne.objects.get_or_create(
            nom=nom,
            defaults={
                'url': url, 'statut': statut, 'offre_resume': resume,
                'date_verification': VERIF, 'ordre': ordre,
            },
        )


def unload_data(apps, schema_editor):
    SiteExterne = apps.get_model('api', 'SiteExterne')
    SiteExterne.objects.filter(nom__in=[s[0] for s in SITES]).delete()


class Migration(migrations.Migration):

    dependencies = [('api', '0002_seed_themes')]

    operations = [
        migrations.RunPython(load_data, unload_data),
    ]
