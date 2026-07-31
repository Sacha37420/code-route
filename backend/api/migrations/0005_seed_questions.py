"""Premier lot de questions écrites à la main (origine='humaine', statut='validee'
directement, cf. modèle Question). Amorçage nécessaire avant le Lot 4 : la
génération IA a besoin d'un échantillon de questions déjà validées par
thème/difficulté en few-shot (voir to_do_code_route.md, section Lot 4) — un
thème sans aucune question validée ne peut donner lieu à aucune génération
cohérente.

Contenu construit à partir des mêmes règles publiques du Code de la route que
les fiches de cours (0004_seed_fiches_cours), jamais reformulé d'une source
commerciale. Chaque question fausse porte une explication du piège dans son
`explication` — c'est ce texte que Mistral réutilisera en few-shot (Lot 4).
"""
from django.db import migrations

# (theme_nom, [(enonce, type, difficulte, explication_generale, [(texte, correcte, explication), ...])])
QUESTIONS = [
    ("La route", [
        (
            "À partir de quel repère la limitation à 50 km/h s'applique-t-elle en entrant "
            "dans une agglomération ?",
            "qcm_unique", "facile",
            "La limite s'applique dès le panneau d'entrée d'agglomération, qu'il y ait ou non "
            "des habitations visibles à cet endroit précis.",
            [
                ("Dès le panneau d'entrée d'agglomération", True, ""),
                ("Seulement à partir de la première maison rencontrée", False,
                 "Idée reçue fréquente : c'est le panneau, pas la présence visible d'habitations, "
                 "qui fixe la limite."),
                ("Uniquement le jour", False, "La limitation de vitesse ne dépend jamais de l'heure."),
            ],
        ),
        (
            "Une ligne continue au sol peut être franchie...",
            "qcm_unique", "moyen",
            "Une ligne continue est infranchissable, sauf exception précise comme l'accès à "
            "une propriété riveraine.",
            [
                ("Jamais, en aucune circonstance", False,
                 "Trop absolu : il existe une exception légale (accès à une propriété riveraine)."),
                ("Pour accéder à une propriété riveraine", True, ""),
                ("Pour dépasser un cycliste, dans tous les cas", False,
                 "Le fait de dépasser un cycliste ne rend pas une ligne continue franchissable."),
            ],
        ),
        (
            "Un panneau de danger (triangle à fond blanc, liseré rouge) annonce un risque "
            "situé à environ 150 m en agglomération.",
            "vrai_faux", "facile",
            "En agglomération, la distance d'annonce est plus courte que hors agglomération, "
            "où elle est généralement plus grande compte tenu des vitesses plus élevées.",
            [
                ("Vrai", True, ""),
                ("Faux", False, "C'est bien la distance d'annonce habituelle en agglomération."),
            ],
        ),
    ]),
    ("Le conducteur", [
        (
            "Quel est le taux d'alcoolémie maximal autorisé pour un conducteur en permis "
            "probatoire ?",
            "qcm_unique", "moyen",
            "Le seuil est abaissé à 0,2 g/L de sang pendant toute la durée du permis probatoire, "
            "contre 0,5 g/L pour un permis définitif.",
            [
                ("0,5 g/L de sang", False,
                 "C'est le seuil applicable à un permis définitif, pas au permis probatoire."),
                ("0,2 g/L de sang", True, ""),
                ("0,8 g/L de sang", False, "C'est le seuil au-delà duquel l'infraction devient un délit."),
            ],
        ),
        (
            "Si la vitesse d'un véhicule double, sa distance de freinage double également.",
            "vrai_faux", "difficile",
            "La distance de freinage augmente avec le carré de la vitesse : rouler deux fois "
            "plus vite quadruple la distance de freinage, à adhérence égale.",
            [
                ("Vrai", False,
                 "Piège classique : la relation n'est pas linéaire mais quadratique, la distance "
                 "est multipliée par 4, pas par 2."),
                ("Faux", True, ""),
            ],
        ),
        (
            "La conduite sous l'emprise de stupéfiants est sanctionnée...",
            "qcm_unique", "moyen",
            "Contrairement à l'alcool, il n'existe aucun seuil de tolérance pour les stupéfiants "
            "au volant.",
            [
                ("Seulement au-delà d'un certain taux, comme pour l'alcool", False,
                 "Confusion avec la règle de l'alcool : pour les stupéfiants, il n'y a pas de seuil."),
                ("Quel que soit le taux détecté", True, ""),
                ("Uniquement en cas d'accident", False, "L'infraction existe indépendamment de tout accident."),
            ],
        ),
    ]),
    ("La circulation routière", [
        (
            "Au feu orange fixe, un conducteur doit...",
            "qcm_unique", "facile",
            "L'arrêt est obligatoire au feu orange fixe, sauf si le freiner en sécurité est "
            "impossible à ce moment précis.",
            [
                ("Accélérer pour passer avant le rouge", False,
                 "C'est l'inverse de la règle : l'orange fixe impose l'arrêt, pas l'accélération."),
                ("S'arrêter, sauf si l'arrêt est impossible en toute sécurité", True, ""),
                ("S'arrêter uniquement si un piéton est visible", False,
                 "L'obligation d'arrêt ne dépend pas de la présence d'un piéton."),
            ],
        ),
        (
            "Parmi les situations suivantes, lesquelles rendent un dépassement interdit ?",
            "qcm_multiple", "difficile",
            "Le dépassement est interdit dès qu'il compromet la visibilité ou la sécurité d'un "
            "usager vulnérable — respecter une distance latérale suffisante n'est pas une "
            "interdiction, c'est au contraire la bonne pratique.",
            [
                ("Un piéton s'engage sur le passage piéton devant vous", True, ""),
                ("Un cortège ou convoi exceptionnel sans visibilité suffisante", True, ""),
                ("Dépasser un cycliste en le laissant à 1,5 m hors agglomération", False,
                 "Ce n'est pas une situation interdite : c'est au contraire la distance minimale "
                 "recommandée pour dépasser un cycliste en sécurité."),
            ],
        ),
        (
            "Le stationnement est autorisé sur un passage piéton s'il n'y a aucun piéton en vue.",
            "vrai_faux", "facile",
            "L'interdiction de stationner sur un passage piéton (et à moins de 5 m avant) est "
            "permanente, indépendamment de la présence visible de piétons.",
            [
                ("Vrai", False, "L'interdiction est permanente, pas conditionnée à la présence de piétons."),
                ("Faux", True, ""),
            ],
        ),
    ]),
    ("Les autres usagers de la route", [
        (
            "Que doit faire un conducteur lorsqu'un piéton s'engage sur un passage piéton "
            "devant lui ?",
            "qcm_unique", "facile",
            "L'arrêt est obligatoire dès qu'un piéton manifeste l'intention de traverser sur "
            "un passage piéton.",
            [
                ("Ralentir seulement, sans s'arrêter", False,
                 "Ralentir ne suffit pas : l'arrêt est obligatoire dans cette situation."),
                ("S'arrêter pour le laisser traverser", True, ""),
                ("Klaxonner et continuer sa route", False,
                 "Un piéton engagé sur un passage piéton est prioritaire, klaxonner ne change rien à cette obligation."),
            ],
        ),
        (
            "Quelle distance latérale minimale doit-on laisser pour dépasser un cycliste "
            "hors agglomération ?",
            "qcm_unique", "moyen",
            "La distance minimale est de 1,5 m hors agglomération (1 m en agglomération).",
            [
                ("1 mètre", False, "C'est la distance minimale en agglomération, pas hors agglomération."),
                ("1,5 mètre", True, ""),
                ("0,5 mètre", False, "Cette distance est insuffisante dans tous les cas."),
            ],
        ),
        (
            "Les cyclistes peuvent circuler à deux de front tant qu'ils ne gênent pas le "
            "dépassement.",
            "vrai_faux", "moyen",
            "C'est une règle explicitement autorisée par le Code de la route, à condition de "
            "ne pas empêcher les dépassements.",
            [
                ("Vrai", True, ""),
                ("Faux", False, "C'est bien une règle autorisée, sous cette condition précise."),
            ],
        ),
    ]),
    ("Dispositions administratives diverses", [
        (
            "Combien de points sont attribués au départ à un permis probatoire ?",
            "qcm_unique", "facile",
            "Le permis probatoire démarre avec 6 points et en gagne 2 par an sans infraction, "
            "jusqu'à atteindre les 12 points du permis définitif.",
            [
                ("6 points", True, ""),
                ("12 points", False, "12 points est le capital d'un permis déjà confirmé, pas d'un permis probatoire."),
                ("8 points", False, "Ce n'est pas le capital de départ du permis probatoire."),
            ],
        ),
        (
            "Le contrôle technique d'un véhicule léger est obligatoire...",
            "qcm_unique", "facile",
            "Le contrôle technique concerne les véhicules de plus de 4 ans, renouvelé tous les 2 ans.",
            [
                ("Tous les ans, dès la première immatriculation", False,
                 "Le rythme est de 2 ans, et l'obligation ne démarre qu'à partir de 4 ans."),
                ("Tous les 2 ans, à partir de 4 ans", True, ""),
                ("Jamais pour un véhicule de particulier", False, "C'est faux : l'obligation concerne aussi les particuliers."),
            ],
        ),
        (
            "Rouler sans assurance est une simple contravention.",
            "vrai_faux", "moyen",
            "Le défaut d'assurance est un délit, sanctionné bien plus sévèrement qu'une simple contravention.",
            [
                ("Vrai", False, "C'est un délit, pas une simple contravention."),
                ("Faux", True, ""),
            ],
        ),
    ]),
    ("Notions diverses", [
        (
            "Quelle est la profondeur minimale légale des sculptures d'un pneu ?",
            "qcm_unique", "moyen",
            "La profondeur minimale légale est de 1,6 mm.",
            [
                ("1,6 mm", True, ""),
                ("3 mm", False, "Ce seuil est plus élevé que le minimum légal réel."),
                ("Aucune obligation légale", False, "Il existe bien un seuil légal minimal."),
            ],
        ),
        (
            "Couper le moteur lors d'un arrêt prolongé réduit la consommation de carburant.",
            "vrai_faux", "facile",
            "C'est l'un des principes de base de l'éco-conduite.",
            [
                ("Vrai", True, ""),
                ("Faux", False, "C'est au contraire l'une des recommandations de base de l'éco-conduite."),
            ],
        ),
        (
            "En cas de panne sur autoroute, que doit-on faire avant de sortir du véhicule ?",
            "qcm_unique", "moyen",
            "Le gilet doit être enfilé avant de sortir, puis on se met à l'abri derrière les "
            "glissières — jamais à pied sur la chaussée ou la bande d'arrêt d'urgence.",
            [
                ("Rester dans le véhicule sur la bande d'arrêt d'urgence", False,
                 "C'est dangereux : il faut sortir et se mettre à l'abri derrière les glissières."),
                ("Enfiler le gilet rétro-réfléchissant avant de sortir", True, ""),
                ("Poser le triangle de présignalisation à pied sur la voie", False,
                 "Le triangle ne s'utilise jamais à pied sur autoroute, contrairement à une route classique."),
            ],
        ),
    ]),
    ("La sécurité du passager et du véhicule", [
        (
            "Le port de la ceinture de sécurité est obligatoire...",
            "qcm_unique", "facile",
            "La ceinture est obligatoire à toutes les places équipées, y compris à l'arrière.",
            [
                ("Uniquement à l'avant du véhicule", False,
                 "Idée reçue fréquente : l'obligation concerne aussi les places arrière équipées."),
                ("À toutes les places équipées, y compris à l'arrière", True, ""),
                ("Uniquement hors agglomération", False, "L'obligation ne dépend pas du type de route."),
            ],
        ),
        (
            "Un siège enfant dos à la route peut être installé à une place avant équipée "
            "d'un airbag frontal actif.",
            "vrai_faux", "difficile",
            "C'est extrêmement dangereux : l'airbag doit être désactivé si un siège dos à la "
            "route est utilisé à cette place.",
            [
                ("Vrai", False, "C'est dangereux — l'airbag frontal doit être désactivé dans ce cas précis."),
                ("Faux", True, ""),
            ],
        ),
        (
            "À partir de quelle taille un enfant n'a-t-il plus l'obligation d'utiliser un "
            "dispositif de retenue homologué ?",
            "qcm_unique", "moyen",
            "Le seuil réglementaire est de 1,35 m (ou 10 ans), au-delà duquel la ceinture "
            "adulte standard peut suffire.",
            [
                ("1,35 mètre", True, ""),
                ("1,50 mètre", False, "Ce seuil est plus élevé que celui réellement fixé par la réglementation."),
                ("1,20 mètre", False, "Ce seuil est plus bas que celui réellement fixé par la réglementation."),
            ],
        ),
    ]),
    ("Les équipements de sécurité et de confort", [
        (
            "Le régulateur de vitesse dispense-t-il le conducteur de respecter les "
            "distances de sécurité ?",
            "qcm_unique", "moyen",
            "Les aides à la conduite ne remplacent jamais la vigilance du conducteur, qui "
            "reste responsable des distances de sécurité.",
            [
                ("Non, le conducteur reste responsable des distances de sécurité", True, ""),
                ("Oui, c'est le rôle de ce système", False,
                 "Un régulateur de vitesse ne gère pas les distances de sécurité avec le véhicule qui précède."),
                ("Oui, mais uniquement sur autoroute", False, "Le conducteur reste responsable en toutes circonstances."),
            ],
        ),
        (
            "Le gilet rétro-réfléchissant doit être enfilé avant de sortir du véhicule en "
            "cas d'arrêt d'urgence.",
            "vrai_faux", "facile",
            "L'enfiler après être sorti expose le conducteur, non visible, au danger qu'il "
            "cherche justement à éviter.",
            [
                ("Vrai", True, ""),
                ("Faux", False, "C'est bien la règle : l'enfiler après être sorti du véhicule est dangereux."),
            ],
        ),
    ]),
    ("L'environnement", [
        (
            "Que signale une vignette Crit'Air de classe 0 ?",
            "qcm_unique", "moyen",
            "La classe 0 correspond aux véhicules les moins polluants (électrique, hydrogène).",
            [
                ("Un véhicule électrique ou à hydrogène", True, ""),
                ("Un véhicule très polluant", False,
                 "C'est l'inverse : la classe 0 est la moins polluante, pas la plus polluante."),
                ("Un véhicule diesel récent", False, "Un diesel récent obtient une classe supérieure à 0."),
            ],
        ),
        (
            "Les règles d'accès aux zones à faibles émissions (ZFE) sont identiques dans "
            "toutes les agglomérations françaises.",
            "vrai_faux", "moyen",
            "Les règles précises (véhicules concernés, horaires) varient d'une agglomération "
            "à l'autre et doivent être vérifiées localement.",
            [
                ("Vrai", False, "Les règles varient au contraire d'une agglomération à l'autre."),
                ("Faux", True, ""),
            ],
        ),
    ]),
    ("Les premiers secours", [
        (
            "Quel est l'ordre correct de la conduite à tenir face à un accident de la route ?",
            "qcm_unique", "facile",
            "L'ordre protéger → alerter → secourir n'est jamais inversé : sécuriser la zone "
            "avant tout évite un sur-accident.",
            [
                ("Protéger, alerter, secourir", True, ""),
                ("Secourir, alerter, protéger", False,
                 "Inverser l'ordre expose à un sur-accident avant même d'avoir sécurisé la zone."),
                ("Alerter, secourir, protéger", False, "La protection de la zone doit toujours venir en premier."),
            ],
        ),
        (
            "Il faut toujours retirer le casque d'un motard accidenté pour vérifier son état.",
            "vrai_faux", "difficile",
            "Retirer un casque est un geste risqué (mobilisation du rachis cervical), réservé "
            "aux cas d'arrêt respiratoire et à un geste technique précis.",
            [
                ("Vrai", False,
                 "Retirer le casque est déconseillé sauf arrêt respiratoire, en raison du risque "
                 "pour la colonne cervicale."),
                ("Faux", True, ""),
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

    dependencies = [('api', '0004_seed_fiches_cours')]

    operations = [
        migrations.RunPython(load_data, unload_data),
    ]
