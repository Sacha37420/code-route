from django.db import migrations

THEMES = [
    ('La route', "Types de routes, intersections, signalisation liée à la route elle-même."),
    ('Le conducteur', "Aptitude à conduire, capacités physiques et psychologiques, fatigue, substances."),
    ('La circulation routière', "Règles de circulation, priorités, vitesse, dépassement, stationnement."),
    ('Les autres usagers de la route', "Piétons, cyclistes, motards, transports en commun, cohabitation."),
    ('Dispositions administratives diverses', "Permis de conduire, documents obligatoires, assurance, contrôle technique."),
    ('Notions diverses', "Mécanique de base, éco-conduite, comportement en cas d'accident."),
    ('La sécurité du passager et du véhicule', "Ceinture, sièges enfants, airbags, entretien du véhicule."),
    ('Les équipements de sécurité et de confort', "Systèmes d'aide à la conduite, équipements obligatoires."),
    ('L\'environnement', "Impact environnemental de la conduite, pollution, éco-conduite."),
    ('Les premiers secours', "Comportement et gestes à adopter en cas d'accident."),
]


def load_data(apps, schema_editor):
    Theme = apps.get_model('api', 'Theme')
    for ordre, (nom, description) in enumerate(THEMES):
        Theme.objects.get_or_create(nom=nom, defaults={'description': description, 'ordre': ordre})


def unload_data(apps, schema_editor):
    Theme = apps.get_model('api', 'Theme')
    Theme.objects.filter(nom__in=[n for n, _ in THEMES]).delete()


class Migration(migrations.Migration):

    dependencies = [('api', '0001_initial')]

    operations = [
        migrations.RunPython(load_data, unload_data),
    ]
