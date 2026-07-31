"""Comble les combinaisons thème × difficulté encore sans aucune question
validée (10 des 30 combinaisons) — amorçage requis avant de pouvoir lancer une
génération IA sur ces couples (cf. Lot 4 : zéro question validée = pas de
génération possible, voir GenerationIALancerView/generer_questions).

Contenu construit à partir des mêmes sources publiques que les fiches de
cours 0004/0006 (dont les faits sourcés Légifrance R.312-19 sur le
chargement, et la nuance sur la méthode « hollandaise » — bonne pratique
recommandée, pas une obligation légale confirmée à ce jour)."""
from django.db import migrations

QUESTIONS = [
    ("La route", [
        (
            "Dans un tunnel, en cas d'incident (panne, accident), que devez-vous faire ?",
            "qcm_unique", "difficile",
            "Les issues de secours d'un tunnel sont régulièrement espacées et signalées — "
            "s'y diriger est la conduite recommandée plutôt que de faire demi-tour ou de rester "
            "sur place sans agir.",
            [
                ("Faire immédiatement demi-tour pour sortir par où vous êtes entré", False,
                 "Le demi-tour est interdit et dangereux dans un tunnel — mieux vaut suivre la signalisation des issues de secours."),
                ("Suivre la signalisation des issues de secours", True, ""),
                ("Rester dans le véhicule sans réagir en attendant les secours", False,
                 "Ce n'est pas la conduite recommandée : il faut se diriger vers une issue de secours si la situation le permet."),
            ],
        ),
    ]),
    ("Le conducteur", [
        (
            "La fatigue est l'une des principales causes d'accident mortel sur autoroute.",
            "vrai_faux", "facile",
            "La fatigue réduit fortement la vigilance et peut provoquer des micro-sommeils, "
            "particulièrement dangereux sur autoroute où la vitesse est élevée et la conduite monotone.",
            [
                ("Vrai", True, ""),
                ("Faux", False, "C'est au contraire l'une des toutes premières causes de mortalité sur autoroute."),
            ],
        ),
    ]),
    ("La circulation routière", [
        (
            "Dans un rond-point, sauf signalisation contraire, qui est prioritaire ?",
            "qcm_unique", "moyen",
            "Les véhicules déjà engagés dans l'anneau sont prioritaires ; ceux qui abordent le "
            "rond-point doivent céder le passage (panneau Cédez le passage systématique à chaque entrée).",
            [
                ("Les véhicules déjà engagés dans l'anneau", True, ""),
                ("Les véhicules qui abordent le rond-point", False,
                 "C'est l'inverse : ceux qui abordent le rond-point doivent céder le passage à ceux déjà engagés."),
                ("Le véhicule arrivant le plus à droite", False, "La priorité à droite classique ne s'applique pas dans un rond-point signalé."),
            ],
        ),
    ]),
    ("Les autres usagers de la route", [
        (
            "Pourquoi ne faut-il jamais se placer entre un poids lourd à l'arrêt et le trottoir "
            "à une intersection ?",
            "qcm_unique", "difficile",
            "Un poids lourd a de grands angles morts et son arrière déporte largement vers "
            "l'intérieur du virage — un usager placé là risque de ne pas être vu et d'être heurté.",
            [
                ("Parce que le poids lourd a de grands angles morts et déporte en virage", True, ""),
                ("Parce qu'un panneau l'interdit spécifiquement à cet endroit", False,
                 "Ce n'est pas une interdiction signalée : c'est un danger lié aux angles morts et au déport du véhicule."),
                ("Parce que cela ralentit simplement la circulation", False, "Le danger est bien plus grave qu'un simple ralentissement."),
            ],
        ),
    ]),
    ("Dispositions administratives diverses", [
        (
            "Un chargement mal arrimé dont le dépassement excède les limites réglementaires de "
            "plus de 20 % est sanctionné par une amende pouvant atteindre :",
            "qcm_unique", "difficile",
            "L'amende forfaitaire de base pour un arrimage non conforme est de 68 €, mais un "
            "dépassement de plus de 20 % des limites réglementaires expose à une amende pénale "
            "pouvant atteindre 1 500 €.",
            [
                ("68 euros", False, "C'est l'amende forfaitaire de base pour un arrimage non conforme, pas le plafond en cas de fort dépassement."),
                ("1 500 euros", True, ""),
                ("3 750 euros", False, "Ce montant est supérieur à l'amende réellement prévue dans ce cas."),
            ],
        ),
    ]),
    ("Notions diverses", [
        (
            "La méthode dite « hollandaise » pour ouvrir sa portière est aujourd'hui une "
            "obligation légale inscrite au Code de la route français.",
            "vrai_faux", "difficile",
            "C'est une bonne pratique de sécurité largement recommandée pour éviter "
            "l'emportiérage d'un cycliste, mais pas encore une obligation légale formalisée en "
            "France à ce jour.",
            [
                ("Vrai", False, "C'est une bonne pratique recommandée, pas (encore) une obligation légale confirmée en France."),
                ("Faux", True, ""),
            ],
        ),
    ]),
    ("Les équipements de sécurité et de confort", [
        (
            "Un système de stationnement semi-autonome dispense le conducteur de toute "
            "vigilance pendant la manœuvre.",
            "vrai_faux", "difficile",
            "Comme tout ADAS, le stationnement semi-autonome reste une aide : le conducteur "
            "doit rester prêt à reprendre la main, notamment si un piéton s'engage dans un angle "
            "mort du système.",
            [
                ("Vrai", False, "Aucun ADAS ne dispense de vigilance — le conducteur reste responsable de la manœuvre."),
                ("Faux", True, ""),
            ],
        ),
    ]),
    ("L'environnement", [
        (
            "Une vignette Crit'Air de classe 1 correspond à un véhicule plus polluant qu'une "
            "vignette de classe 0.",
            "vrai_faux", "facile",
            "La classe 0 (électrique/hydrogène) est la moins polluante ; les classes suivantes "
            "(1, 2, 3...) sont attribuées par ordre croissant de pollution.",
            [
                ("Vrai", True, ""),
                ("Faux", False, "La classe 0 est bien la moins polluante ; la classe 1 l'est donc davantage."),
            ],
        ),
        (
            "Dans une zone à faibles émissions (ZFE), les règles d'accès (véhicules concernés, "
            "horaires) sont fixées :",
            "qcm_unique", "difficile",
            "Chaque agglomération dotée d'une ZFE fixe ses propres règles d'accès, à vérifier "
            "localement avant un déplacement dans une zone inconnue.",
            [
                ("De façon identique par la loi nationale, pour toutes les agglomérations", False,
                 "Les règles précises varient au contraire d'une agglomération à l'autre."),
                ("Localement, par chaque agglomération concernée", True, ""),
                ("Uniquement par arrêté préfectoral renouvelé chaque année", False, "Ce n'est pas le mécanisme général de fixation des règles d'une ZFE."),
            ],
        ),
    ]),
    ("Les premiers secours", [
        (
            "Face à une victime consciente qui respire mais se plaint de douleurs au dos, que "
            "faut-il faire en l'attendant les secours ?",
            "qcm_unique", "moyen",
            "Un traumatisme du dos ou de la nuque impose de ne pas mobiliser la victime — la "
            "maintenir immobile et la rassurer, sans tenter de la redresser ni de la déplacer.",
            [
                ("La maintenir immobile et la rassurer en attendant les secours", True, ""),
                ("La redresser pour la mettre plus à l'aise", False,
                 "Redresser une victime suspectée de traumatisme du dos risque d'aggraver une éventuelle lésion de la colonne."),
                ("Lui faire boire de l'eau pour la réconforter", False, "Il ne faut jamais faire boire une victime en attendant les secours."),
            ],
        ),
    ]),
]


def load_data(apps, schema_editor):
    Theme = apps.get_model('api', 'Theme')
    Question = apps.get_model('api', 'Question')
    Reponse = apps.get_model('api', 'Reponse')

    for theme_nom, questions in QUESTIONS:
        try:
            theme = Theme.objects.get(nom=theme_nom)
        except Theme.DoesNotExist:
            continue
        for enonce, qtype, difficulte, explication_generale, reponses in questions:
            if Question.objects.filter(theme=theme, enonce=enonce).exists():
                continue
            question = Question.objects.create(
                theme=theme, enonce=enonce, type=qtype, difficulte=difficulte,
                explication_generale=explication_generale,
                origine='humaine', statut='validee',
            )
            for texte, correcte, explication in reponses:
                Reponse.objects.create(
                    question=question, texte=texte, correcte=correcte, explication=explication,
                )


def unload_data(apps, schema_editor):
    Question = apps.get_model('api', 'Question')
    enonces = [enonce for _, questions in QUESTIONS for enonce, *_ in questions]
    Question.objects.filter(enonce__in=enonces).delete()


class Migration(migrations.Migration):

    dependencies = [('api', '0006_seed_fiches_complement')]

    operations = [
        migrations.RunPython(load_data, unload_data),
    ]
