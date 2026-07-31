"""Complément de fiches suite à une revue face aux 10 thématiques officielles
de l'épreuve théorique (recherche du 2026-07-31 sur securite-routiere.gouv.fr
et sites relais officiels/gouv.fr, + Légifrance pour le chargement — article
R.312-19 du Code de la route cité explicitement ci-dessous). Comble des sujets
couverts par l'examen réel mais absents des 32 fiches initiales (0004) :
conduite de nuit/intempéries, tunnels/passages à niveau/travaux, précautions
en quittant le véhicule, chargement du véhicule, poids lourds."""
from django.db import migrations

FICHES = [
    ("La route", [
        (
            "Conduite de nuit et par mauvais temps",
            "## L'éclairage du véhicule\n\n"
            "- **Feux de croisement** (codes) : obligatoires dès la nuit tombée ou dès que la "
            "visibilité est insuffisante (pluie forte, brouillard léger), y compris en ville.\n"
            "- **Feux de route** (pleins phares) : utilisables sur route non éclairée en l'absence "
            "de véhicule en face ou devant — à basculer en feux de croisement dès qu'un autre "
            "usager risque d'être ébloui (véhicule en face, cycliste, piéton).\n"
            "- **Feux de brouillard avant** : en complément ou à la place des feux de croisement "
            "si la visibilité est fortement réduite.\n"
            "- **Feu de brouillard arrière** : à utiliser uniquement si la visibilité descend sous "
            "50 m, et à éteindre dès que les conditions s'améliorent — laissé allumé par temps "
            "clair, il éblouit et masque les feux stop pour le conducteur qui suit.\n\n"
            "## Adapter sa conduite\n\n"
            "La nuit, les distances sont plus difficiles à évaluer et la fatigue s'installe plus "
            "vite : réduire sa vitesse permet de garder une distance d'arrêt compatible avec la "
            "portée réelle de son éclairage (souvent inférieure à la distance de freinage à "
            "vitesse autorisée). Par pluie ou brouillard, réduire sa vitesse et augmenter "
            "fortement la distance de sécurité (au moins doublée) : l'adhérence diminue et la "
            "visibilité des feux d'un véhicule qui précède est elle-même réduite.",
        ),
        (
            "Tunnels, passages à niveau et zones de travaux",
            "## Les tunnels\n\n"
            "- Allumer les feux de croisement en entrant, même en plein jour.\n"
            "- Augmenter la distance de sécurité : l'effet tunnel et l'éclairage artificiel "
            "faussent la perception des distances.\n"
            "- Changement de voie, dépassement, arrêt et marche arrière sont interdits sauf "
            "obligation signalée ou danger immédiat.\n"
            "- En cas d'incident, suivre la signalisation des issues de secours (généralement "
            "espacées de quelques centaines de mètres) plutôt que de faire demi-tour.\n\n"
            "## Les passages à niveau\n\n"
            "- Ne jamais s'engager si une file de véhicules empêcherait de dégager complètement "
            "la voie ferrée de l'autre côté.\n"
            "- Feu rouge clignotant et/ou sonnerie : arrêt obligatoire, même si les barrières ne "
            "sont pas encore descendues.\n"
            "- Ne jamais s'arrêter sur les voies, quelle que soit la raison (panne, bouchon).\n"
            "- Panneau croix de Saint-André : rappelle la présence d'une voie ferrée, priorité "
            "absolue au train en toutes circonstances.\n\n"
            "## Les zones de travaux\n\n"
            "La signalisation temporaire (fond jaune/orange) prévaut toujours sur la signalisation "
            "permanente (fond blanc) en cas de contradiction. Les limitations de vitesse "
            "réduites en zone de travaux s'appliquent même en l'absence apparente d'ouvriers ou "
            "d'engins, et le non-respect y est souvent plus sévèrement sanctionné du fait du "
            "danger accru pour le personnel présent.",
        ),
    ]),
    ("Les autres usagers de la route", [
        (
            "Les poids lourds et leurs angles morts",
            "## Des angles morts bien plus grands qu'une voiture\n\n"
            "Un poids lourd a des angles morts étendus à l'avant, sur les côtés et à l'arrière — "
            "un cycliste ou un piéton peut se trouver juste devant ou à côté de la cabine sans "
            "que le conducteur ne le voie, même en vérifiant ses rétroviseurs. Règle simple pour "
            "un usager vulnérable : si vous ne voyez pas le visage du chauffeur dans son "
            "rétroviseur, lui non plus ne vous voit pas.\n\n"
            "## Vigilance particulière au moment des manœuvres\n\n"
            "- Un poids lourd qui tourne à droite balaie un espace bien plus large qu'une "
            "voiture (déport de la remorque) : ne jamais se placer entre un poids lourd à "
            "l'arrêt/ralenti et le trottoir à une intersection, même si un espace semble libre.\n"
            "- Les distances de freinage d'un poids lourd chargé sont nettement supérieures à "
            "celles d'une voiture : laisser une distance de sécurité accrue devant soi lorsqu'un "
            "poids lourd suit, et ne jamais se rabattre trop court après l'avoir dépassé.\n\n"
            "## Transport en commun et véhicules d'intérêt général\n\n"
            "Voir la fiche « Véhicules prioritaires et transports en commun » pour les règles de "
            "priorité qui leur sont propres.",
        ),
    ]),
    ("Dispositions administratives diverses", [
        (
            "Le chargement et l'arrimage du véhicule",
            "## Le principe général (article R.312-19 du Code de la route)\n\n"
            "« Toutes précautions utiles doivent être prises pour que le chargement d'un véhicule "
            "ne puisse être une cause de dommage ou de danger. » Cette obligation générale "
            "couvre aussi bien le poids que la fixation et le débordement du chargement.\n\n"
            "## Le poids\n\n"
            "Le poids total réel du véhicule chargé (PTR) ne doit jamais dépasser le poids total "
            "autorisé en charge (PTAC) indiqué sur la carte grise. Une charge mal répartie "
            "modifie aussi la tenue de route et allonge les distances de freinage.\n\n"
            "## L'encombrement\n\n"
            "- Largeur maximale du chargement : **2,55 m**.\n"
            "- À l'arrière, le chargement (véhicule ou remorque) ne doit pas dépasser de plus de "
            "**3 m** l'extrémité du véhicule.\n"
            "- Aucun dépassement autorisé à l'avant.\n"
            "- Le chargement ne doit jamais masquer les feux, la plaque d'immatriculation ou les "
            "catadioptres.\n\n"
            "## La fixation\n\n"
            "La charge doit être stable, solidement arrimée, et l'arrimage vérifié régulièrement "
            "pendant le trajet — un chargement qui se déplace ou tombe est un danger direct pour "
            "les autres usagers. Un chargement mal arrimé est sanctionné d'une amende forfaitaire "
            "de 68 € ; en cas de dépassement des limites réglementaires de plus de 20 %, l'amende "
            "peut atteindre 1 500 €.",
        ),
    ]),
    ("Notions diverses", [
        (
            "Quitter son véhicule en sécurité",
            "## Avant de sortir\n\n"
            "- Serrer le frein de stationnement (indispensable même en pente nulle).\n"
            "- Couper le moteur et retirer la clé/le badge.\n"
            "- En stationnement en pente, braquer les roues vers le trottoir (en descente) ou "
            "vers la chaussée (en montée) pour qu'elles butent en cas de défaillance du frein.\n"
            "- Enclencher une vitesse (ou le mode P en boîte automatique) en complément du frein "
            "à main.\n\n"
            "## Ouvrir la portière sans danger — la « méthode hollandaise »\n\n"
            "Ouvrir sa portière côté circulation sans se retourner est une cause fréquente "
            "d'accident avec un cycliste ou un motard qui remonte la file (« emportiérage »). La "
            "méthode recommandée consiste à attraper la poignée avec la main **opposée** à la "
            "portière (la main droite pour la portière conducteur en France) : ce geste oblige "
            "naturellement à pivoter le buste et à regarder vers l'arrière avant d'ouvrir. Il "
            "s'agit d'une bonne pratique de sécurité largement recommandée, pas encore d'une "
            "obligation formalisée dans le Code de la route à ce jour — à vérifier si la "
            "réglementation évolue.\n\n"
            "## Ne jamais laisser un enfant seul\n\n"
            "Ne jamais laisser un enfant seul dans un véhicule, même quelques instants, même "
            "vitres entrouvertes : risque de coup de chaleur (l'habitacle peut monter très vite "
            "en température au soleil) et risque de manipulation accidentelle des commandes.",
        ),
    ]),
]


COMPLEMENT_ADAS = (
    "\n\n## Le stationnement semi-autonome\n\n"
    "De plus en plus de véhicules proposent une aide au stationnement semi-autonome : le "
    "système braque à la place du conducteur (qui garde la main sur l'accélérateur et le "
    "frein, ou parfois les deux également automatisés selon le niveau du système). Comme "
    "pour les autres ADAS, le conducteur reste responsable de la manœuvre et doit être prêt "
    "à reprendre la main à tout moment — notamment si un piéton s'engage derrière le véhicule "
    "pendant la manœuvre, un angle mort que le système ne couvre pas toujours entièrement."
)


def load_data(apps, schema_editor):
    Theme = apps.get_model('api', 'Theme')
    FicheCours = apps.get_model('api', 'FicheCours')

    # Complète la fiche ADAS existante (0004) avec le stationnement semi-autonome,
    # sujet ajouté à l'examen officiel lors de la réforme 2023 (cf. recherche 2026-07-31).
    adas = FicheCours.objects.filter(titre='Les aides à la conduite (ADAS)').first()
    if adas and 'stationnement semi-autonome' not in adas.contenu:
        adas.contenu += COMPLEMENT_ADAS
        adas.save(update_fields=['contenu'])

    for theme_nom, fiches in FICHES:
        try:
            theme = Theme.objects.get(nom=theme_nom)
        except Theme.DoesNotExist:
            continue
        ordre_depart = FicheCours.objects.filter(theme=theme).count()
        for i, (titre, contenu) in enumerate(fiches):
            FicheCours.objects.get_or_create(
                theme=theme, titre=titre,
                defaults={'contenu': contenu, 'ordre': ordre_depart + i},
            )


def unload_data(apps, schema_editor):
    FicheCours = apps.get_model('api', 'FicheCours')
    titres = [titre for _, fiches in FICHES for titre, _ in fiches]
    FicheCours.objects.filter(titre__in=titres).delete()


class Migration(migrations.Migration):

    dependencies = [('api', '0005_seed_questions')]

    operations = [
        migrations.RunPython(load_data, unload_data),
    ]
