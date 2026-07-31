"""Constructeurs de prompt Mistral — aucun import de modèle ici (évite les
imports circulaires, comme restauration/backend/api/prompts.py). Chaque
fonction reçoit des données déjà extraites par l'appelant (tasks.py / views.py)
et renvoie (system, message, schema) prêts pour mistral_client.completer_json().
"""

SCHEMA_ANALYSE = {
    'type': 'object',
    'properties': {
        'points_forts': {'type': 'array', 'items': {'type': 'string'}},
        'points_faibles': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'theme': {'type': 'string'},
                    'taux_reussite': {'type': 'number'},
                    'explication': {'type': 'string'},
                },
            },
        },
        'plan_revision': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'theme': {'type': 'string'},
                    'priorite': {'type': 'string', 'enum': ['haute', 'moyenne', 'basse']},
                    'conseil': {'type': 'string'},
                },
            },
        },
        'fiches_a_relire': {'type': 'array', 'items': {'type': 'string'}},
        'resume': {'type': 'string'},
    },
    'required': ['points_forts', 'points_faibles', 'plan_revision', 'fiches_a_relire', 'resume'],
}

_SYSTEM_ANALYSE = """Tu es un moniteur d'auto-école expérimenté qui prépare un candidat à l'épreuve
théorique du code de la route français.

On te fournit les statistiques de réussite d'un candidat par thème, ainsi que le
texte des questions qu'il a ratées récemment avec l'explication du piège associé.
Ne te sers d'aucune autre connaissance du code de la route que celle strictement
déductible des données fournies : ne complète jamais avec une règle non citée dans
les questions/fiches transmises.

Produis un diagnostic strictement au format JSON suivant :
{
  "points_forts": ["<theme>", ...],
  "points_faibles": [
    {"theme": "<theme>", "taux_reussite": <0-100>, "explication": "<texte>"}
  ],
  "plan_revision": [
    {"theme": "<theme>", "priorite": "haute|moyenne|basse", "conseil": "<texte>"}
  ],
  "fiches_a_relire": ["<id_theme>", ...],
  "resume": "<2-3 phrases, ton encourageant, jamais culpabilisant>"
}

Ceci est une aide à la révision, pas un verdict — le résumé doit rester encourageant
même si le taux de réussite global est faible."""


def construire_prompt_analyse(stats_par_theme: dict, questions_ratees: list[dict]) -> tuple[str, str, dict]:
    """`stats_par_theme` : {theme: {total, correctes, taux_reussite}}.
    `questions_ratees` : [{theme, enonce, explication_generale, pieges: [str]}], les
    plus récentes en premier — l'appelant (tasks.py) borne déjà la taille de cette
    liste avant de construire le prompt."""
    lignes_stats = [
        f"- {theme} : {s['correctes']}/{s['total']} bonnes réponses ({s['taux_reussite']}%)"
        for theme, s in stats_par_theme.items()
    ]
    lignes_questions = []
    for q in questions_ratees:
        pieges = ' ; '.join(q.get('pieges', [])) or 'non précisé'
        lignes_questions.append(
            f"- [{q['theme']}] « {q['enonce']} » — piège : {pieges}"
            + (f" — explication : {q['explication_generale']}" if q.get('explication_generale') else '')
        )

    message = (
        "Statistiques de réussite par thème :\n" + '\n'.join(lignes_stats) +
        "\n\nQuestions ratées récemment (les plus récentes en premier) :\n" +
        ('\n'.join(lignes_questions) if lignes_questions else "(aucune question ratée récemment)")
    )
    return _SYSTEM_ANALYSE, message, SCHEMA_ANALYSE


SCHEMA_GENERATION = {
    'type': 'object',
    'properties': {
        'questions': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'enonce': {'type': 'string'},
                    'type': {'type': 'string', 'enum': ['qcm_unique', 'qcm_multiple', 'vrai_faux']},
                    'reponses': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'texte': {'type': 'string'},
                                'correcte': {'type': 'boolean'},
                                'explication': {'type': ['string', 'null']},
                            },
                        },
                    },
                    'explication_generale': {'type': 'string'},
                    'piege_utilise': {'type': 'string'},
                },
            },
        },
    },
    'required': ['questions'],
}

_SYSTEM_GENERATION = """Tu es un concepteur d'épreuves officielles du code de la route français. On te donne
un échantillon de questions déjà validées pour un thème et un niveau de difficulté
donnés (énoncé, réponses, réponse correcte, explication du piège).

Génère de nouvelles questions ORIGINALES pour le même thème et la même difficulté,
qui suivent la même logique pédagogique et réutilisent le même TYPE de piège que les
exemples (double négation, exception à une règle générale, priorité contre-intuitive,
distracteur plausible mais faux, confusion entre deux règles proches...), sans jamais
reformuler ou dupliquer une question de l'échantillon.

Ne fabrique aucune règle de circulation qui ne soit pas déjà présente, explicitement
ou implicitement, dans l'échantillon fourni — ni dans le contexte vérifié par recherche
web, si on t'en fournit un. Si tu ne peux pas générer une question sûre sans inventer
une règle non couverte par ces deux sources, génère-en moins plutôt que de deviner.

Réponds strictement au format JSON suivant :
{
  "questions": [
    {
      "enonce": "<texte>",
      "type": "qcm_unique|qcm_multiple|vrai_faux",
      "reponses": [{"texte": "<texte>", "correcte": <bool>, "explication": "<texte ou null>"}],
      "explication_generale": "<texte>",
      "piege_utilise": "<catégorie de piège reprise de l'échantillon>"
    }
  ]
}"""


def construire_prompt_generation(
    theme_nom: str, difficulte: str, nombre_demande: int, echantillon: list[dict],
    contexte_verifie: str = '',
) -> tuple[str, str, dict]:
    """`echantillon` : [{enonce, type, reponses: [{texte, correcte, explication}], explication_generale}].
    `contexte_verifie` : résumé factuel optionnel obtenu via Deepsearch
    (mistral_client.rechercher_web) — vient compléter, jamais contredire, l'échantillon."""
    lignes = []
    for q in echantillon:
        reponses_txt = ' / '.join(
            f"{r['texte']}{' [correcte]' if r['correcte'] else ''}" for r in q['reponses']
        )
        lignes.append(
            f"- « {q['enonce']} » (type {q['type']}) — réponses : {reponses_txt}"
            + (f" — explication : {q['explication_generale']}" if q.get('explication_generale') else '')
        )

    message = (
        f"Thème : {theme_nom}\nDifficulté : {difficulte}\nNombre de questions demandé : {nombre_demande}\n\n"
        "Échantillon de questions déjà validées :\n" + '\n'.join(lignes)
    )
    if contexte_verifie:
        message += f"\n\nContexte vérifié par recherche web (Deepsearch) :\n{contexte_verifie}"
    return _SYSTEM_GENERATION, message, SCHEMA_GENERATION


_SYSTEM_ASSISTANT_FICHES = """Tu es l'assistant de rédaction des fiches de révision du code de la route
français pour ce lab de préparation au permis. Tu aides un administrateur à
analyser, corriger, étendre ou créer des fiches de cours pour un thème donné.

Règles impératives :
- Ne jamais inventer une règle de circulation dont tu n'es pas certain — en cas de
  doute, dis-le explicitement plutôt que d'affirmer un chiffre ou un seuil approximatif.
- Le contenu doit rester cohérent avec les autres fiches déjà existantes du thème
  (fournies ci-dessous), sans les contredire ni les dupliquer inutilement.
- Quand tu proposes une modification concrète (corriger une fiche existante, l'étendre,
  ou en créer une nouvelle), termine ta réponse par un unique bloc JSON, dans un bloc
  de code ```json, au format suivant :
{
  "action": "creer" | "modifier",
  "fiche_id": <id de la fiche à modifier, ou null si action="creer">,
  "titre": "<titre de la fiche>",
  "contenu": "<contenu complet en markdown — pas un extrait, le texte final entier>",
  "illustration_credit": "<texte d'attribution, ou chaîne vide si sans objet>"
}
- Si tu poses une question, demandes une précision, ou discutes sans proposition
  concrète prête à appliquer, ne mets AUCUN bloc JSON dans ta réponse.
- Le contenu proposé n'est jamais publié automatiquement : un administrateur le relit
  et clique explicitement sur « Appliquer » avant toute écriture en base.

Fiches déjà existantes pour le thème « __THEME_NOM__ » :
__FICHES_EXISTANTES__"""


def construire_contexte_assistant_fiches(theme_nom: str, fiches: list[dict]) -> str:
    """`fiches` : [{id, titre, contenu}] — toutes les fiches déjà en base pour ce
    thème, données en contexte à l'assistant (pas de function-calling à la volée :
    l'accès aux fiches existantes est déjà résolu ici, avant le premier message).

    Substitution par remplacement simple (pas .format()) : le gabarit contient
    un exemple de bloc JSON avec de vraies accolades, que .format() interpréterait
    à tort comme des placeholders."""
    if fiches:
        lignes = [f"### [id={f['id']}] {f['titre']}\n{f['contenu']}" for f in fiches]
        fiches_existantes = '\n\n'.join(lignes)
    else:
        fiches_existantes = "(aucune fiche existante pour ce thème pour l'instant)"

    return (
        _SYSTEM_ASSISTANT_FICHES
        .replace('__THEME_NOM__', theme_nom)
        .replace('__FICHES_EXISTANTES__', fiches_existantes)
    )
