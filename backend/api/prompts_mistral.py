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
ou implicitement, dans l'échantillon fourni. Si tu ne peux pas générer une question
sûre sans inventer une règle non couverte par l'échantillon, génère-en moins plutôt
que de deviner.

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


def construire_prompt_generation(theme_nom: str, difficulte: str, nombre_demande: int, echantillon: list[dict]) -> tuple[str, str, dict]:
    """`echantillon` : [{enonce, type, reponses: [{texte, correcte, explication}], explication_generale}]."""
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
    return _SYSTEM_GENERATION, message, SCHEMA_GENERATION
