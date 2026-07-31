"""Amorçage d'un premier corpus complet de fiches de révision.

Contenu rédigé à partir des règles du Code de la route français (texte
réglementaire public, cf. to_do_code_route.md section « Sources de contenu »)
— aucune reformulation d'un contenu commercial (Codeclic, Ornikar, Codes
Rousseau...). Les chiffres cités (vitesses, taux d'alcoolémie, délais...) sont
les règles stables et bien établies du Code de la route ; à vérifier/ajuster
par un admin si la réglementation évolue (voir CRUD Fiches, page Paramétrage
n'est pas nécessaire ici, une simple édition de fiche suffit).
"""
from django.db import migrations

# (nom_theme, [(titre, contenu_markdown), ...])
FICHES = [
    ("La route", [
        (
            "Les différents types de route",
            "## Les catégories de voies\n\n"
            "Le réseau routier français distingue plusieurs catégories de voies, "
            "chacune avec ses propres règles (vitesse, accès, équipements) :\n\n"
            "- **Autoroute** : signalée par des panneaux bleus, accès réservé aux véhicules "
            "à moteur capables de dépasser 40 km/h. Pas de croisement à niveau, pas de piétons, "
            "cyclistes ni engins agricoles.\n"
            "- **Route express** et **voie rapide** : chaussées séparées ou non, accès parfois "
            "limité, règles proches de l'autoroute mais signalisation blanche/verte.\n"
            "- **Routes hors agglomération** (nationales, départementales) : à double ou simple "
            "sens, avec ou sans séparateur central.\n"
            "- **Agglomération** : délimitée par les panneaux d'entrée (nom de la ville, fond "
            "blanc) et de sortie (même panneau barré). La limite de vitesse par défaut y est de "
            "50 km/h dès le panneau d'entrée, même avant la première maison.\n\n"
            "Le type de route détermine la vitesse maximale autorisée par défaut et certaines "
            "obligations (ex. gilet/triangle en cas d'arrêt d'urgence, interdiction des piétons "
            "sur autoroute).",
        ),
        (
            "Comprendre la signalisation routière",
            "## Les grandes familles de panneaux\n\n"
            "La signalisation française est organisée en catégories reconnaissables par leur "
            "forme et leur couleur :\n\n"
            "- **Panneaux de danger (A)** : triangle à fond blanc, liseré rouge. Annoncent un "
            "danger à environ 150 m en agglomération et davantage hors agglomération.\n"
            "- **Panneaux d'interdiction (B)** : cercle à fond blanc, liseré rouge (ex. sens "
            "interdit, interdiction de dépasser, limitation de vitesse).\n"
            "- **Panneaux d'obligation (B)** : cercle à fond bleu (ex. direction obligatoire, "
            "piste cyclable obligatoire).\n"
            "- **Panneaux d'indication (C)** : carré ou rectangle bleu, informent sans imposer "
            "de comportement particulier (parking, hôpital, sens unique...).\n"
            "- **Panneaux de fin d'interdiction/obligation (C)** : fond blanc ou gris barré.\n"
            "- **Panneaux de direction (D)** : rectangulaires, couleur selon le type de route "
            "(vert autoroute, blanc départementale...).\n\n"
            "**Règle générale** : en cas de contradiction entre un panneau et un agent qui règle "
            "la circulation, les ordres de l'agent priment toujours sur la signalisation, elle-même "
            "prioritaire sur les feux, eux-mêmes prioritaires sur les règles générales de priorité.",
        ),
        (
            "Le marquage au sol",
            "## Lire les lignes et symboles peints sur la chaussée\n\n"
            "- **Ligne continue** : infranchissable, sauf pour accéder à une propriété riveraine "
            "ou en cas d'obstacle imprévu.\n"
            "- **Ligne discontinue** : franchissable pour dépasser, tourner ou changer de file, "
            "en s'assurant que la manœuvre est possible sans danger.\n"
            "- **Ligne mixte** (continue d'un côté, discontinue de l'autre) : seul le conducteur "
            "situé du côté discontinu peut franchir la ligne.\n"
            "- **Ligne continue en bordure de chaussée** : matérialise l'accotement, à ne pas "
            "franchir sauf arrêt d'urgence.\n"
            "- **Damiers et hachures** : zones où l'arrêt et le stationnement sont interdits, "
            "utilisées notamment sur les zones de danger ou de dégagement (passages piétons, "
            "carrefours).\n"
            "- **Flèches de direction** : obligent à suivre la direction indiquée à la prochaine "
            "intersection ; on ne peut pas changer de file après les avoir franchies si cela "
            "revient à ne pas respecter la direction indiquée.\n\n"
            "En cas de contradiction entre le marquage au sol et un panneau, c'est le panneau, "
            "plus récent en général, qui doit être suivi — mais les deux sont normalement cohérents.",
        ),
        (
            "Les intersections et le franchissement de priorité",
            "## Les règles de priorité aux intersections\n\n"
            "- **Priorité à droite** : règle par défaut en l'absence de toute signalisation, y "
            "compris en agglomération. Le véhicule venant de la droite est prioritaire.\n"
            "- **Panneau Cédez le passage** (triangle pointe en bas, fond blanc liseré rouge) : "
            "obligation de céder le passage aux véhicules circulant sur la voie abordée, sans "
            "obligation de marquer un arrêt si la voie est libre.\n"
            "- **Panneau Stop** (octogone rouge) : arrêt total obligatoire au niveau de la ligne "
            "d'effet, même si aucun véhicule n'est visible, avant de céder le passage.\n"
            "- **Rond-point** : sauf signalisation contraire, priorité aux véhicules déjà engagés "
            "dans l'anneau ; ceux qui abordent le rond-point doivent céder le passage (panneau "
            "Cédez le passage systématiquement présent à chaque entrée).\n"
            "- **Passage à niveau** : priorité absolue au train, arrêt obligatoire dès que les "
            "barrières s'abaissent ou que le feu rouge clignote.\n\n"
            "**À retenir** : la priorité n'est jamais un droit à exercer aveuglément — un "
            "conducteur prioritaire doit rester prudent et peut être tenu responsable s'il ne "
            "pouvait pas éviter un accident alors qu'il aurait pu ralentir.",
        ),
    ]),
    ("Le conducteur", [
        (
            "L'aptitude à la conduite",
            "## Être en état de conduire\n\n"
            "Conduire exige des capacités physiques et psychologiques intactes :\n\n"
            "- **La vue** : un champ visuel et une acuité suffisants sont exigés pour l'obtention "
            "du permis ; le port de lunettes/lentilles prescrites est une obligation légale au "
            "même titre que la ceinture si mentionné sur le permis.\n"
            "- **La fatigue** : première cause d'accident mortel sur autoroute. Elle réduit la "
            "vigilance, allonge le temps de réaction et peut provoquer des micro-sommeils de "
            "quelques secondes, suffisants pour perdre le contrôle du véhicule.\n"
            "- **Le stress et les émotions fortes** : dégradent la capacité de jugement et "
            "d'anticipation.\n"
            "- **L'âge et la santé** : certaines pathologies (épilepsie non stabilisée, troubles "
            "cardiaques sévères...) peuvent rendre la conduite incompatible, temporairement ou "
            "définitivement, sur avis médical.\n\n"
            "**Bonnes pratiques** : faire une pause de 15-20 minutes toutes les deux heures sur "
            "long trajet, ne jamais reprendre la route après une nuit blanche, s'arrêter au "
            "premier signe de somnolence (bâillements répétés, paupières lourdes, difficulté à "
            "rester dans sa file).",
        ),
        (
            "Alcool et conduite : les seuils et les risques",
            "## Les taux légaux d'alcoolémie\n\n"
            "- **Permis classique** : taux maximal autorisé de **0,5 gramme d'alcool par litre "
            "de sang** (0,25 mg par litre d'air expiré).\n"
            "- **Permis probatoire** (les 3 premières années, 2 ans en conduite accompagnée) et "
            "**conducteurs de transport en commun** : taux abaissé à **0,2 g/L de sang** "
            "(0,10 mg/L d'air expiré) — en pratique, une tolérance zéro.\n\n"
            "## Les effets de l'alcool\n\n"
            "L'alcool réduit le champ visuel, allonge le temps de réaction, donne une fausse "
            "confiance en soi et altère l'appréciation des distances et des vitesses — dès les "
            "premiers verres, bien avant l'ivresse ressentie.\n\n"
            "## Les sanctions\n\n"
            "La conduite avec un taux supérieur au seuil légal est une infraction pénale, "
            "sanctionnée par un retrait de points, une amende, et selon la gravité une suspension "
            "ou une annulation du permis, voire une peine de prison en cas de récidive ou "
            "d'accident. Au-delà de 0,8 g/L, il s'agit d'un délit (et non plus d'une simple "
            "contravention).",
        ),
        (
            "Stupéfiants, médicaments et conduite",
            "## Stupéfiants\n\n"
            "La conduite sous l'emprise de stupéfiants est un délit, **quel que soit le taux "
            "détecté** — contrairement à l'alcool, il n'existe aucun seuil de tolérance. Le "
            "dépistage se fait par test salivaire, confirmé ensuite par prise de sang. Les effets "
            "(altération de la vigilance, de la coordination, somnolence ou au contraire "
            "excès de confiance) persistent parfois plusieurs heures après la consommation, bien "
            "au-delà de la sensation d'effet immédiat.\n\n"
            "## Médicaments\n\n"
            "De nombreux médicaments courants (antihistaminiques, somnifères, anxiolytiques, "
            "certains antidouleurs) peuvent altérer la vigilance. Ils sont signalés par un "
            "pictogramme sur la boîte, à trois niveaux de risque croissant :\n\n"
            "- **Niveau 1 (triangle jaune)** : soyez prudent, lisez la notice.\n"
            "- **Niveau 2 (triangle orange)** : soyez très prudent, demandez l'avis d'un "
            "professionnel de santé avant de prendre le volant.\n"
            "- **Niveau 3 (triangle rouge)** : danger, ne pas conduire sans l'avis d'un médecin.\n\n"
            "Le cumul de plusieurs médicaments, ou de médicaments avec de l'alcool, amplifie "
            "fortement les risques même à faible dose.",
        ),
        (
            "Distance de freinage, distance d'arrêt et temps de réaction",
            "## Trois notions à ne pas confondre\n\n"
            "- **Le temps de réaction** : délai entre la perception d'un danger et le début de "
            "l'action (freiner, tourner). En moyenne 1 seconde chez un conducteur reposé et "
            "attentif, bien plus en cas de fatigue, distraction ou alcool.\n"
            "- **La distance de réaction** : distance parcourue pendant le temps de réaction. "
            "Elle augmente proportionnellement à la vitesse (à 50 km/h : environ 14 m ; à "
            "130 km/h : environ 36 m, pour 1 seconde de réaction).\n"
            "- **La distance de freinage** : distance parcourue une fois le freinage engagé "
            "jusqu'à l'arrêt complet. Elle augmente avec le **carré** de la vitesse : rouler deux "
            "fois plus vite quadruple la distance de freinage, à adhérence égale.\n\n"
            "**Distance d'arrêt = distance de réaction + distance de freinage.**\n\n"
            "Ces distances sont fortement dégradées par une chaussée mouillée ou verglacée, des "
            "pneus usés, un véhicule chargé, ou une vitesse excessive par rapport aux conditions. "
            "C'est pourquoi la règle des **2 secondes** de distance de sécurité avec le véhicule "
            "qui précède (à doubler par mauvais temps) est essentielle : elle s'adapte "
            "automatiquement à la vitesse réelle, contrairement à une distance fixe en mètres.",
        ),
    ]),
    ("La circulation routière", [
        (
            "Les règles de priorité",
            "## Rappel des priorités selon le contexte\n\n"
            "- **Absence de signalisation** : priorité à droite.\n"
            "- **Panneaux Stop / Cédez le passage** : voir la fiche « Les intersections » du "
            "thème La route.\n"
            "- **Feux tricolores** : rouge = arrêt obligatoire ; orange fixe = arrêt obligatoire "
            "sauf si l'arrêt est impossible en toute sécurité ; orange clignotant = prudence, "
            "l'intersection redevient réglée par les règles de priorité classiques ; vert = "
            "passage autorisé si la voie est dégagée (ne jamais s'engager si cela bloque le "
            "carrefour).\n"
            "- **Véhicules prioritaires** (pompiers, SAMU, police en intervention, gyrophare + "
            "avertisseur sonore activés) : priorité absolue, il faut faciliter leur passage même "
            "en cas de feu vert en leur faveur inversé.\n"
            "- **Bus quittant un arrêt en agglomération** : le bus est prioritaire pour se "
            "réinsérer dans la circulation, dans la limite du raisonnable et de la sécurité.\n\n"
            "**Cas particulier** : sur une route prioritaire signalée (panneau losange jaune), la "
            "priorité est maintenue à toutes les intersections suivantes jusqu'au panneau de fin "
            "de priorité, sans avoir besoin de panneau Cédez le passage à chaque carrefour.",
        ),
        (
            "Les limitations de vitesse",
            "## Les vitesses maximales par défaut\n\n"
            "- **Agglomération** : 50 km/h (30 km/h dans les zones signalées « zone 30 », "
            "20 km/h dans les zones de rencontre).\n"
            "- **Hors agglomération, route à double sens sans séparateur central** : 80 km/h "
            "(certains départements ont relevé cette limite à 90 km/h sur certains axes, "
            "signalée explicitement).\n"
            "- **Route à chaussées séparées par un terre-plein central** : 110 km/h (100 km/h "
            "par temps de pluie).\n"
            "- **Autoroute** : 130 km/h (110 km/h par temps de pluie, 50 km/h en cas de "
            "visibilité inférieure à 50 m, ex. brouillard dense).\n\n"
            "## Vitesses minimales et réduites\n\n"
            "Une vitesse minimale peut être imposée sur autoroute pour la voie de gauche. À "
            "l'inverse, le conducteur doit toujours adapter sa vitesse aux conditions (visibilité, "
            "état de la chaussée, densité du trafic), même en dessous de la limite affichée : "
            "rouler à la limite autorisée dans le brouillard ou sur route glissante reste une "
            "infraction si cela crée un danger.\n\n"
            "Le permis probatoire n'impose pas de limitation de vitesse différente des autres "
            "conducteurs (contrairement à une idée reçue), mais un seuil d'alcoolémie plus bas.",
        ),
        (
            "Le dépassement",
            "## Les conditions pour dépasser en sécurité\n\n"
            "Avant de dépasser, il faut vérifier successivement :\n\n"
            "1. Que le dépassement n'est pas interdit (ligne continue, panneau, proximité d'une "
            "intersection ou d'un sommet de côte sans visibilité).\n"
            "2. Que la voie est suffisamment dégagée devant, pour effectuer la manœuvre et se "
            "rabattre sans gêner ni le véhicule dépassé, ni un véhicule arrivant en sens inverse.\n"
            "3. Que personne ne s'apprête à vous dépasser (angle mort, rétroviseurs).\n\n"
            "## Pendant et après\n\n"
            "Signaler son intention avec le clignotant, s'écarter suffisamment du véhicule "
            "dépassé (davantage pour un cycliste ou un piéton, au moins 1 m en agglomération et "
            "1,5 m hors agglomération), puis se rabattre après avoir vérifié dans le rétroviseur "
            "intérieur que le véhicule dépassé est visible en entier.\n\n"
            "## Interdictions classiques\n\n"
            "- Dépasser à l'approche d'un passage piéton où un piéton s'engage.\n"
            "- Dépasser par la droite (sauf cas particuliers : file de gauche à l'arrêt, "
            "circulation en files parallèles en agglomération dense).\n"
            "- Dépasser un convoi exceptionnel ou un cortège sans visibilité suffisante.",
        ),
        (
            "L'arrêt et le stationnement",
            "## Différence entre arrêt et stationnement\n\n"
            "- **L'arrêt** : immobilisation temporaire du véhicule, le conducteur restant à "
            "proximité pour pouvoir le déplacer immédiatement (ex. dépose d'un passager).\n"
            "- **Le stationnement** : immobilisation prolongée, que le conducteur soit présent ou "
            "non.\n\n"
            "## Où l'arrêt et le stationnement sont interdits\n\n"
            "- Sur les passages piétons et à moins de 5 m avant ceux-ci.\n"
            "- Sur les emplacements réservés (personnes à mobilité réduite, taxis, livraisons) "
            "sans autorisation.\n"
            "- À proximité des intersections, sauf marquage autorisant explicitement.\n"
            "- Sur les zones matérialisées par des hachures ou un damier au sol.\n"
            "- Sur une place réservée aux véhicules électriques en recharge, pour un véhicule "
            "thermique.\n\n"
            "## Le stationnement gênant, très gênant et dangereux\n\n"
            "Selon la zone concernée (passage piéton, arrêt de bus, place handicapé, double file), "
            "la sanction est graduée : simple gênant, très gênant (mise en fourrière possible), "
            "ou dangereux (le plus sévère, ex. stationnement sur une voie rapide).",
        ),
    ]),
    ("Les autres usagers de la route", [
        (
            "Partager la route avec les piétons",
            "## Les règles de base\n\n"
            "- Un conducteur doit **s'arrêter** dès qu'un piéton manifeste l'intention de "
            "traverser sur un passage piéton, même sans feu.\n"
            "- Le dépassement d'un véhicule arrêté ou ralentissant à l'approche d'un passage "
            "piéton est interdit : un autre véhicule pourrait masquer un piéton en train de "
            "traverser.\n"
            "- En l'absence de passage piéton à proximité (moins de 50 m), les piétons ont le "
            "droit de traverser mais doivent le faire dans les meilleures conditions de sécurité "
            "et n'ont pas de priorité formelle — la prudence du conducteur reste néanmoins de "
            "mise en toutes circonstances.\n\n"
            "## Les usagers vulnérables\n\n"
            "Enfants, personnes âgées ou à mobilité réduite nécessitent une vigilance accrue : "
            "leur comportement est moins prévisible, leur vitesse de déplacement plus faible ou "
            "irrégulière. Une canne blanche ou blanche et rouge signale une personne aveugle ou "
            "malvoyante, à qui la priorité absolue doit être laissée pour traverser.\n\n"
            "En agglomération, dans une **zone de rencontre**, les piétons sont prioritaires sur "
            "tous les véhicules et peuvent circuler sur toute la largeur de la voie ; la vitesse y "
            "est limitée à 20 km/h.",
        ),
        (
            "Cyclistes et engins de déplacement personnel motorisés",
            "## Les cyclistes\n\n"
            "- Doivent circuler sur les pistes ou bandes cyclables quand elles existent et sont "
            "obligatoires (panneau rond bleu avec vélo).\n"
            "- Peuvent circuler à deux de front, sauf s'ils gênent le dépassement, et doivent se "
            "mettre en file simple dès la tombée de la nuit ou si les conditions de circulation "
            "l'exigent.\n"
            "- Bénéficient d'un **sas vélo** à de nombreux feux tricolores : zone avancée réservée, "
            "où les voitures doivent s'arrêter derrière la ligne, en retrait.\n"
            "- Le dépassement d'un cycliste doit se faire à au moins 1 m en agglomération, "
            "1,5 m hors agglomération.\n\n"
            "## Les engins de déplacement personnel motorisés (EDPM)\n\n"
            "Trottinettes électriques et engins similaires : interdits aux moins de 12 ans, "
            "casque non obligatoire mais recommandé, interdiction de rouler sur les trottoirs "
            "(sauf autorisation locale à vitesse pas), circulation sur pistes cyclables ou, à "
            "défaut, sur la chaussée en agglomération à 50 km/h ou moins. Un seul utilisateur par "
            "engin, gilet rétro-réfléchissant recommandé la nuit ou par visibilité réduite.",
        ),
        (
            "Les deux-roues motorisés",
            "## Motos et scooters : spécificités\n\n"
            "- **Équipement obligatoire** : casque homologué attaché, gants homologués CE pour "
            "le conducteur et le passager.\n"
            "- **La chasse aux angles morts** : un deux-roues est plus difficile à repérer, "
            "notamment dans les angles morts des véhicules lourds — les conducteurs de voiture ou "
            "de poids lourd doivent redoubler de vigilance avant tout changement de file.\n"
            "- **La circulation inter-files** : autorisée uniquement dans les zones et conditions "
            "expérimentales définies par arrêté préfectoral, jamais un droit général.\n\n"
            "## Freinage et trajectoires\n\n"
            "Un deux-roues freine et manœuvre différemment d'une voiture : distance de freinage "
            "plus sensible à l'état de la chaussée, trajectoire de virage qui peut sembler "
            "irrégulière à un observateur non averti. Un automobiliste ne doit jamais couper la "
            "route d'un deux-roues en sous-estimant sa vitesse d'approche, souvent plus rapide "
            "qu'elle n'y paraît.",
        ),
        (
            "Véhicules prioritaires et transports en commun",
            "## Les véhicules d'intérêt général prioritaires\n\n"
            "Pompiers, SAMU, police et gendarmerie en intervention (gyrophare bleu **et** "
            "avertisseur sonore deux tons simultanément activés) bénéficient d'une priorité de "
            "passage absolue. Le conducteur doit faciliter leur progression : ralentir, se "
            "serrer sur le côté, s'arrêter si nécessaire, y compris en franchissant un feu rouge "
            "avec la plus grande prudence si aucune autre option n'est sûre.\n\n"
            "## Les véhicules d'intérêt général bénéficiant de facilités\n\n"
            "Certains véhicules (transport de fonds, dépannage sur autoroute...) disposent d'un "
            "gyrophare orange sans priorité de passage : il signale simplement leur présence et "
            "invite à la prudence, sans obligation de leur céder le passage.\n\n"
            "## Les transports en commun\n\n"
            "Un bus qui signale son intention de quitter un arrêt en agglomération est prioritaire "
            "pour se réinsérer dans la circulation. Les couloirs réservés aux bus et taxis sont "
            "interdits aux autres véhicules, sauf mention contraire (ex. autorisation ponctuelle "
            "pour les vélos).",
        ),
    ]),
    ("Dispositions administratives diverses", [
        (
            "Le permis de conduire et le permis probatoire",
            "## Les grandes catégories de permis\n\n"
            "- **B** : véhicules légers (jusqu'à 3,5 t, 9 places max).\n"
            "- **A1/A2/A** : deux-roues motorisés, par paliers de puissance et d'âge.\n"
            "- **C, D, E** : poids lourds, transport en commun, remorques lourdes.\n\n"
            "## Le permis probatoire\n\n"
            "Tout nouveau permis est probatoire pendant **3 ans** (réduit à **2 ans** en cas de "
            "conduite accompagnée ou supervisée). Il démarre avec **6 points** (au lieu de 12) et "
            "en gagne 2 par an sans infraction jusqu'à atteindre 12. Un disque « A » (ou "
            "autocollant) doit être apposé à l'arrière du véhicule pendant cette période, et une "
            "limitation de vitesse spécifique s'applique parfois selon les évolutions "
            "réglementaires en vigueur.\n\n"
            "## Le retrait de points et l'invalidation\n\n"
            "Chaque infraction retire un nombre de points défini par son niveau de gravité. Le "
            "permis est invalidé lorsque le solde atteint 0 : le conducteur doit alors le "
            "repasser après un délai minimal. Un stage de récupération de points (2 jours, une "
            "fois par an maximum) permet de regagner jusqu'à 4 points.",
        ),
        (
            "Les documents obligatoires à bord",
            "## À présenter en cas de contrôle\n\n"
            "- **Le permis de conduire** correspondant à la catégorie du véhicule conduit.\n"
            "- **La carte grise (certificat d'immatriculation)** du véhicule, à son nom ou avec "
            "l'autorisation du titulaire.\n"
            "- **L'attestation d'assurance** en cours de validité.\n"
            "- **Le certificat du dernier contrôle technique**, si le véhicule y est soumis.\n\n"
            "## Format numérique\n\n"
            "Certains documents peuvent désormais être présentés sous forme dématérialisée "
            "(application officielle), mais il reste recommandé de conserver une preuve physique "
            "ou de vérifier au préalable que le format numérique est accepté par les forces de "
            "l'ordre.\n\n"
            "L'absence de présentation de l'un de ces documents lors d'un contrôle constitue une "
            "infraction, distincte du fait de ne pas les détenir du tout (ex. défaut d'assurance, "
            "bien plus grave).",
        ),
        (
            "L'assurance automobile",
            "## Une obligation légale\n\n"
            "Tout véhicule motorisé, même à l'arrêt sur la voie publique ou un terrain privé "
            "ouvert à la circulation, doit être couvert par une assurance **responsabilité "
            "civile** au minimum — c'est la garantie qui indemnise les tiers en cas de dommage "
            "causé par le véhicule assuré.\n\n"
            "## Les niveaux de garantie\n\n"
            "- **Au tiers** : couverture minimale légale, uniquement les dommages causés à "
            "autrui.\n"
            "- **Intermédiaire** : ajoute souvent le vol, l'incendie, le bris de glace.\n"
            "- **Tous risques** : couvre également les dommages au véhicule assuré lui-même, y "
            "compris en cas de responsabilité totale du conducteur assuré.\n\n"
            "## Le défaut d'assurance\n\n"
            "Rouler sans assurance est un délit sévèrement sanctionné (amende importante, "
            "confiscation possible du véhicule, suspension du permis), en plus d'exposer "
            "personnellement le conducteur à indemniser toutes les victimes d'un accident sur "
            "ses propres deniers.",
        ),
        (
            "Le contrôle technique",
            "## Pourquoi et pour qui\n\n"
            "Le contrôle technique vérifie l'état de sécurité et le respect des normes "
            "environnementales d'un véhicule. Il est **obligatoire pour tout véhicule léger de "
            "plus de 4 ans**, puis renouvelé **tous les 2 ans**.\n\n"
            "## Ce qui est vérifié\n\n"
            "Freinage, direction, visibilité (pare-brise, essuie-glaces, rétroviseurs), "
            "éclairage et signalisation, liaison au sol (pneus, suspensions), structure du "
            "véhicule, pollution et niveau sonore, entre autres points de contrôle.\n\n"
            "## Les issues possibles\n\n"
            "- **Favorable** : aucun défaut ou défauts mineurs, contrôle valable pour 2 ans.\n"
            "- **Défavorable avec contre-visite** : défaut(s) majeur(s) à corriger, contre-visite "
            "sous un délai limité (généralement 2 mois).\n"
            "- **Défavorable, interdiction de circuler** : défaut critique compromettant "
            "gravement la sécurité, immobilisation immédiate du véhicule.\n\n"
            "Circuler avec un contrôle technique expiré ou défavorable non régularisé est une "
            "infraction sanctionnée par une amende, indépendamment de l'état réel du véhicule.",
        ),
    ]),
    ("Notions diverses", [
        (
            "Notions de mécanique utiles au conducteur",
            "## Les vérifications de base\n\n"
            "- **Les pneumatiques** : pression conforme aux préconisations du constructeur, "
            "profondeur de sculpture minimale légale de 1,6 mm, état général (pas de "
            "déformation, de coupure profonde).\n"
            "- **Les niveaux** : huile moteur, liquide de refroidissement, liquide de frein, "
            "lave-glace — à vérifier régulièrement, surtout avant un long trajet.\n"
            "- **L'éclairage** : phares, feux de position, feux stop, clignotants — un feu "
            "défaillant est à la fois un risque et une infraction.\n"
            "- **Les freins** : tout bruit anormal (grincement, sifflement) ou perte d'efficacité "
            "doit être signalé sans délai à un professionnel.\n\n"
            "## Pourquoi ces vérifications comptent pour l'examen\n\n"
            "L'épreuve théorique évalue la capacité du futur conducteur à reconnaître un défaut "
            "évident (pneu lisse, voyant allumé) et à en comprendre la conséquence sur la "
            "sécurité — pas une expertise mécanique poussée.",
        ),
        (
            "L'éco-conduite",
            "## Les principes de base\n\n"
            "- **Anticiper** : lever le pied tôt plutôt que de freiner au dernier moment, "
            "regarder loin devant pour lisser sa conduite.\n"
            "- **Limiter les régimes moteur élevés** : passer les vitesses à un régime modéré, "
            "utiliser le frein moteur en descente plutôt que le frein seul.\n"
            "- **Couper le moteur** lors d'un arrêt prolongé plutôt que de le laisser tourner au "
            "ralenti.\n"
            "- **Vérifier la pression des pneus** : un pneu sous-gonflé augmente la consommation "
            "de carburant et l'usure.\n"
            "- **Alléger le véhicule** : éviter de transporter du poids inutile, retirer une "
            "galerie de toit non utilisée (résistance à l'air accrue).\n\n"
            "## Les bénéfices\n\n"
            "Au-delà de la réduction de la consommation de carburant et des émissions de CO2, "
            "l'éco-conduite (anticipation, souplesse) réduit également le risque d'accident : "
            "une conduite plus fluide est aussi une conduite plus prévisible et plus sûre pour "
            "les autres usagers.",
        ),
        (
            "Que faire en cas de panne ou d'accident",
            "## En cas de panne\n\n"
            "1. Allumer les feux de détresse et se déporter le plus possible sur la droite "
            "(bande d'arrêt d'urgence sur autoroute).\n"
            "2. Sortir du véhicule par la portière côté opposé à la circulation, en ayant "
            "revêtu le **gilet rétro-réfléchissant** avant de sortir.\n"
            "3. Se mettre à l'abri derrière les glissières de sécurité, jamais sur la chaussée "
            "ni sur la bande d'arrêt d'urgence elle-même.\n"
            "4. Placer le **triangle de présignalisation** à au moins 30 m en amont, uniquement "
            "hors autoroute (jamais à pied sur autoroute).\n\n"
            "## En cas d'accident : protéger, alerter, secourir\n\n"
            "Voir la fiche dédiée du thème « Les premiers secours » pour le détail de la conduite "
            "à tenir — la priorité absolue est toujours d'éviter le sur-accident avant toute "
            "autre action.",
        ),
    ]),
    ("La sécurité du passager et du véhicule", [
        (
            "La ceinture de sécurité",
            "## Une obligation à toutes les places\n\n"
            "Le port de la ceinture est obligatoire pour le conducteur **et tous les passagers**, "
            "à toutes les places équipées, y compris à l'arrière — quelle que soit la distance du "
            "trajet.\n\n"
            "## Pourquoi elle est indispensable\n\n"
            "Sans ceinture, un occupant est projeté vers l'avant lors d'un choc, même à faible "
            "vitesse : dès 50 km/h, le corps subit une décélération équivalente à une chute de "
            "plusieurs étages. La ceinture répartit la force du choc sur les parties les plus "
            "solides du corps (bassin, thorax) et empêche l'éjection du véhicule, cause majeure "
            "de décès en cas d'accident.\n\n"
            "## Cas particuliers\n\n"
            "Certaines exemptions médicales existent, sur présentation d'un certificat médical. "
            "Le non-port de la ceinture reste l'une des infractions les plus fréquemment "
            "constatées et l'un des facteurs aggravants les plus significatifs de la mortalité "
            "routière.",
        ),
        (
            "Les sièges enfants",
            "## Une obligation liée à la taille, pas seulement à l'âge\n\n"
            "Tout enfant de moins de **10 ans** (ou moins de 1,35 m) doit être installé dans un "
            "dispositif homologué adapté à son poids et à sa taille (siège coque, siège "
            "réhausseur...), jamais avec la ceinture adulte seule qui n'est pas conçue pour sa "
            "morphologie.\n\n"
            "## Le dos à la route le plus longtemps possible\n\n"
            "Les recommandations actuelles préconisent de maintenir un jeune enfant dos à la "
            "route le plus longtemps possible (au moins jusqu'à 1 an, idéalement au-delà) : en "
            "cas de choc frontal, cette position répartit bien mieux les forces sur la tête et la "
            "nuque, particulièrement fragiles à cet âge.\n\n"
            "## L'airbag passager\n\n"
            "Un siège enfant dos à la route ne doit **jamais** être installé à une place équipée "
            "d'un airbag frontal actif : le déploiement de l'airbag en cas de choc serait alors "
            "extrêmement dangereux pour l'enfant. L'airbag doit être désactivé si le siège avant "
            "est utilisé dans ce cas.",
        ),
        (
            "Airbags et systèmes de retenue",
            "## Le rôle des airbags\n\n"
            "Les airbags (frontaux, latéraux, rideaux) complètent la ceinture de sécurité : ils "
            "amortissent le choc de la tête et du buste contre l'habitacle lors d'une collision. "
            "Ils ne remplacent jamais la ceinture — un airbag se déploie en quelques millisecondes "
            "et un occupant non ceinturé est projeté avant même son déclenchement complet.\n\n"
            "## Précautions d'usage\n\n"
            "- Ne jamais s'installer trop près du volant ou du tableau de bord (distance "
            "minimale recommandée d'environ 25 cm pour le conducteur).\n"
            "- Ne rien fixer d'objet rigide sur le volant ou la planche de bord côté passager.\n"
            "- Toujours désactiver l'airbag passager si un siège enfant dos à la route y est "
            "installé (voir fiche « Les sièges enfants »).\n\n"
            "## Autres systèmes de retenue\n\n"
            "Les appuie-têtes, correctement réglés (haut du crâne, pas la nuque), réduisent "
            "fortement le risque de coup du lapin en cas de choc arrière — un réglage trop bas ou "
            "trop en arrière annule une grande partie de leur efficacité.",
        ),
    ]),
    ("Les équipements de sécurité et de confort", [
        (
            "Les équipements obligatoires du véhicule",
            "## À bord en permanence\n\n"
            "- **Un gilet rétro-réfléchissant homologué**, accessible sans sortir du véhicule "
            "(idéalement rangé dans l'habitacle, pas uniquement dans le coffre).\n"
            "- **Un triangle de présignalisation**, pour les véhicules qui en ont besoin hors "
            "autoroute en cas de panne ou d'accident.\n\n"
            "## Selon la saison ou la zone\n\n"
            "- **Équipements hiver** (pneus adaptés ou chaînes/chaussettes à neige) : "
            "obligatoires dans certaines zones montagneuses signalées, entre le 1er novembre et "
            "le 31 mars selon la réglementation locale (« loi Montagne »).\n"
            "- **Vignette Crit'Air** : obligatoire pour circuler dans les zones à faibles "
            "émissions (ZFE), classe le véhicule selon son niveau de pollution.\n\n"
            "## En bon état de fonctionnement\n\n"
            "Éclairage complet, essuie-glaces, avertisseur sonore (klaxon), rétroviseurs "
            "intacts et bien réglés : tous ces équipements sont soumis à une obligation générale "
            "de bon fonctionnement, vérifiée notamment lors du contrôle technique.",
        ),
        (
            "Les aides à la conduite (ADAS)",
            "## Des aides, pas des remplaçants du conducteur\n\n"
            "Les systèmes avancés d'aide à la conduite (ADAS) se généralisent sur les véhicules "
            "récents, avec une part croissante rendue obligatoire sur les nouveaux modèles :\n\n"
            "- **Le régulateur et le limiteur de vitesse** : maintiennent ou plafonnent la "
            "vitesse, mais ne remplacent pas la vigilance sur les distances de sécurité.\n"
            "- **L'aide au maintien dans la voie** : corrige légèrement la trajectoire si le "
            "véhicule dérive sans clignotant activé.\n"
            "- **Le freinage d'urgence autonome** : détecte un obstacle imminent et freine si le "
            "conducteur ne réagit pas à temps.\n"
            "- **Le détecteur d'angle mort** : signale un véhicule non visible dans les "
            "rétroviseurs avant un changement de file.\n"
            "- **L'avertisseur de somnolence** : analyse le comportement de conduite pour "
            "suggérer une pause.\n\n"
            "## Le point essentiel pour l'examen\n\n"
            "Aucun de ces systèmes ne dispense le conducteur de rester attentif et prêt à "
            "reprendre le contrôle à tout moment : ce sont des aides à la vigilance, pas des "
            "systèmes de conduite autonome.",
        ),
    ]),
    ("L'environnement", [
        (
            "Impact environnemental de la route",
            "## Les principaux impacts\n\n"
            "Le transport routier est une source majeure d'émissions de gaz à effet de serre "
            "(CO2) et de polluants atmosphériques locaux (particules fines, oxydes d'azote), "
            "avec des conséquences sur le climat et la qualité de l'air, en particulier en zone "
            "urbaine dense.\n\n"
            "## Les leviers d'action du conducteur\n\n"
            "- Adopter une conduite souple (voir fiche « L'éco-conduite »).\n"
            "- Entretenir régulièrement son véhicule (un moteur mal réglé pollue davantage).\n"
            "- Privilégier le covoiturage ou les alternatives (transports en commun, vélo) quand "
            "c'est possible.\n"
            "- Adapter son véhicule à son usage réel plutôt que de systématiquement sur-motoriser.\n\n"
            "## Le renouvellement du parc automobile\n\n"
            "Les véhicules électriques et hybrides réduisent les émissions locales (voire les "
            "annulent pour les émissions à l'échappement), mais leur impact environnemental "
            "global dépend aussi de la production de la batterie et de l'origine de l'électricité "
            "utilisée pour la recharge.",
        ),
        (
            "Les zones à faibles émissions (ZFE)",
            "## Le principe\n\n"
            "Une zone à faibles émissions mobilité (ZFE-m) restreint ou interdit la circulation "
            "des véhicules les plus polluants dans un périmètre urbain défini, dans le but "
            "d'améliorer la qualité de l'air. Ces zones se multiplient dans les grandes "
            "agglomérations françaises.\n\n"
            "## La vignette Crit'Air\n\n"
            "Chaque véhicule doit être identifié par une vignette Crit'Air, classée de 0 "
            "(véhicules électriques/hydrogène) à 5 (les plus anciens/polluants), déterminée en "
            "fonction de la motorisation et de la date de première immatriculation. L'accès à "
            "une ZFE peut être restreint à certaines classes seulement, en permanence ou "
            "uniquement lors des pics de pollution.\n\n"
            "## Sanctions\n\n"
            "Circuler dans une ZFE sans la vignette requise, ou avec une classe non autorisée, "
            "est une infraction sanctionnée par une amende — les règles précises (véhicules "
            "concernés, horaires, exemptions) varient d'une agglomération à l'autre et doivent "
            "être vérifiées localement avant un déplacement dans une zone inconnue.",
        ),
    ]),
    ("Les premiers secours", [
        (
            "Protéger, alerter, secourir : la conduite à tenir",
            "## 1. Protéger\n\n"
            "Avant toute chose, éviter le sur-accident : allumer les feux de détresse, "
            "revêtir le gilet rétro-réfléchissant avant de sortir du véhicule, sécuriser la zone "
            "(triangle de présignalisation hors autoroute, ou simplement s'éloigner en sécurité "
            "sur autoroute), et mettre les personnes valides à l'abri derrière les glissières.\n\n"
            "## 2. Alerter\n\n"
            "Appeler les secours (**15** SAMU, **18** pompiers, **112** numéro d'urgence "
            "européen, **114** pour les personnes sourdes/malentendantes par SMS) en donnant : "
            "le lieu précis (numéro de borne sur autoroute, point kilométrique), le nombre de "
            "victimes, leur état apparent, et la nature de l'accident. Rester en ligne pour "
            "suivre les instructions.\n\n"
            "## 3. Secourir\n\n"
            "N'intervenir que dans la limite de ses compétences : ne jamais déplacer une "
            "victime sauf danger immédiat (incendie, sur-accident imminent), rassurer les "
            "victimes conscientes, ne rien leur faire boire, et attendre les secours "
            "professionnels pour tout geste technique.\n\n"
            "**L'ordre protéger → alerter → secourir n'est jamais inversé** : porter secours "
            "sans avoir sécurisé la zone risque de créer une victime supplémentaire, soi-même.",
        ),
        (
            "Les gestes de premiers secours à connaître",
            "## Une victime consciente qui respire\n\n"
            "La rassurer, la maintenir immobile si elle se plaint de douleurs (notamment au dos "
            "ou au cou), ne pas retirer un casque de moto sauf absolue nécessité (arrêt "
            "respiratoire) et par une personne formée au geste spécifique.\n\n"
            "## Une victime inconsciente qui respire\n\n"
            "La placer en **position latérale de sécurité (PLS)** pour éviter qu'elle "
            "s'étouffe avec sa langue ou des vomissements, puis surveiller sa respiration en "
            "attendant les secours.\n\n"
            "## Une victime inconsciente qui ne respire pas\n\n"
            "Débuter immédiatement un **massage cardiaque** (compressions thoraciques) si l'on "
            "est formé, en alertant simultanément ou en faisant alerter les secours sans délai. "
            "Utiliser un défibrillateur automatisé externe (DAE) s'il y en a un à proximité — "
            "l'appareil guide vocalement chaque étape, y compris pour une personne non formée.\n\n"
            "## Une hémorragie externe importante\n\n"
            "Comprimer directement la plaie avec un tissu propre (ou la main à défaut), sans "
            "jamais retirer un objet planté dans la plaie — le retirer pourrait aggraver le "
            "saignement.\n\n"
            "**Se former réellement** (PSC1) reste la meilleure préparation : ces fiches "
            "rappellent la logique des gestes, elles ne remplacent pas un apprentissage pratique "
            "encadré.",
        ),
    ]),
]


def load_data(apps, schema_editor):
    Theme = apps.get_model('api', 'Theme')
    FicheCours = apps.get_model('api', 'FicheCours')
    for theme_nom, fiches in FICHES:
        try:
            theme = Theme.objects.get(nom=theme_nom)
        except Theme.DoesNotExist:
            continue
        for ordre, (titre, contenu) in enumerate(fiches):
            FicheCours.objects.get_or_create(
                theme=theme, titre=titre,
                defaults={'contenu': contenu, 'ordre': ordre},
            )


def unload_data(apps, schema_editor):
    FicheCours = apps.get_model('api', 'FicheCours')
    titres = [titre for _, fiches in FICHES for titre, _ in fiches]
    FicheCours.objects.filter(titre__in=titres).delete()


class Migration(migrations.Migration):

    dependencies = [('api', '0003_seed_sites_externes')]

    operations = [
        migrations.RunPython(load_data, unload_data),
    ]
