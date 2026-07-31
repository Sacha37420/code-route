from celery import shared_task

# Nombre de questions ratées récentes transmises en contexte à Mistral —
# borne la taille du prompt, les plus récentes étant les plus pertinentes
# pour un plan de révision actuel.
NB_QUESTIONS_RATEES_CONTEXTE = 15


@shared_task
def analyser_resultats(utilisateur_email: str) -> None:
    """Déclenchée en fin de quiz (QuizTerminerView) — agrège l'historique complet
    de l'usager par thème et demande à Mistral un diagnostic structuré
    (points forts/faibles, plan de révision, résumé encourageant).

    Best-effort vis-à-vis de Mistral : si la configuration est absente ou
    l'appel échoue, une AnalyseIA est quand même enregistrée avec les seules
    statistiques et un résumé de repli — 'Mon bilan' affiche toujours quelque
    chose de cohérent, jamais une page cassée à cause d'un souci d'API externe.
    """
    from . import mistral_client, prompts_mistral
    from .models import AnalyseIA, QuizReponse, Reponse

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

    stats_par_theme = {
        theme: {
            'total': s['total'],
            'correctes': s['correctes'],
            'taux_reussite': round(100 * s['correctes'] / s['total']),
        }
        for theme, s in par_theme.items()
    }

    ratees = list(
        reponses.filter(correcte=False).order_by('-id')[:NB_QUESTIONS_RATEES_CONTEXTE]
    )
    questions_ratees = []
    for qr in ratees:
        pieges = list(
            Reponse.objects
            .filter(id__in=qr.reponses_choisies, correcte=False)
            .exclude(explication='')
            .values_list('explication', flat=True)
        )
        questions_ratees.append({
            'theme': qr.question.theme.nom,
            'enonce': qr.question.enonce,
            'explication_generale': qr.question.explication_generale,
            'pieges': pieges,
        })

    contenu = {'stats_par_theme': stats_par_theme}
    resume_texte = ''

    try:
        system, message, schema = prompts_mistral.construire_prompt_analyse(stats_par_theme, questions_ratees)
        diagnostic = mistral_client.completer_json(system, message, schema)
        contenu['diagnostic'] = diagnostic
        resume_texte = diagnostic.get('resume', '')
    except mistral_client.MistralNonConfigure:
        resume_texte = (
            "Voici vos statistiques de progression — activez Mistral dans la page "
            "Paramétrage pour obtenir un plan de révision personnalisé."
        )
    except mistral_client.MistralError:
        resume_texte = (
            "Vos statistiques de progression sont à jour ci-dessous — l'analyse IA "
            "détaillée n'a pas pu être générée cette fois, réessayez après un prochain quiz."
        )

    AnalyseIA.objects.create(
        utilisateur_email=utilisateur_email,
        contenu=contenu,
        resume_texte=resume_texte,
    )
