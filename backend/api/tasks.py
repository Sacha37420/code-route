from celery import shared_task


@shared_task
def analyser_resultats(utilisateur_email: str) -> None:
    """Déclenchée en fin de quiz (QuizTerminerView) — agrège l'historique complet
    de l'usager par thème et enregistre une AnalyseIA.

    Implémentation Lot 2 : agrégation statistique seule (taux de réussite par
    thème), sans appel Mistral. Le Lot 3 complète cette même tâche pour
    demander à Mistral un diagnostic structuré (points forts/faibles, plan de
    révision) à partir de ces statistiques — voir prompts_mistral.py.
    """
    from .models import AnalyseIA, QuizReponse

    reponses = (
        QuizReponse.objects
        .filter(session__utilisateur_email__iexact=utilisateur_email)
        .select_related('question__theme')
    )
    if not reponses.exists():
        return

    par_theme: dict[str, dict[str, int]] = {}
    for r in reponses:
        theme_nom = r.question.theme.nom
        stats = par_theme.setdefault(theme_nom, {'total': 0, 'correctes': 0})
        stats['total'] += 1
        if r.correcte:
            stats['correctes'] += 1

    contenu = {
        'stats_par_theme': {
            theme: {
                'total': s['total'],
                'correctes': s['correctes'],
                'taux_reussite': round(100 * s['correctes'] / s['total']),
            }
            for theme, s in par_theme.items()
        },
    }

    AnalyseIA.objects.create(
        utilisateur_email=utilisateur_email,
        contenu=contenu,
        resume_texte='',
    )
