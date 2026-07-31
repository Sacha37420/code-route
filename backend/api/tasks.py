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


# Taille de l'échantillon few-shot fourni à Mistral — quelques exemples
# suffisent (cf. to_do_code_route.md Lot 4), pas besoin de tout le thème.
TAILLE_ECHANTILLON_GENERATION = 8


@shared_task
def generer_questions(generation_id: int) -> None:
    """Déclenchée manuellement (page admin « Génération IA »). Fournit à Mistral
    un échantillon de questions déjà validées du thème/difficulté demandés et
    insère les questions produites avec origine='ia', statut='proposee' —
    jamais validées automatiquement (cf. CLAUDE.md, aucune question IA n'est
    jamais servie dans un quiz réel sans validation humaine explicite)."""
    from . import mistral_client, prompts_mistral
    from .models import ConfigurationMistral, GenerationIA, Question, Reponse

    generation = GenerationIA.objects.select_related('theme').get(pk=generation_id)

    echantillon_qs = (
        Question.objects
        .filter(theme=generation.theme, difficulte=generation.difficulte, statut='validee')
        .prefetch_related('reponses')
        .order_by('?')[:TAILLE_ECHANTILLON_GENERATION]
    )
    echantillon = [
        {
            'enonce': q.enonce,
            'type': q.type,
            'explication_generale': q.explication_generale,
            'reponses': [
                {'texte': r.texte, 'correcte': r.correcte, 'explication': r.explication}
                for r in q.reponses.all()
            ],
        }
        for q in echantillon_qs
    ]

    if not echantillon:
        generation.statut = 'erreur'
        generation.erreur_message = (
            "Aucune question déjà validée pour ce thème et cette difficulté — "
            "un premier amorçage manuel est requis avant de pouvoir générer (cf. Lot 4)."
        )
        generation.save(update_fields=['statut', 'erreur_message'])
        return

    contexte_verifie = ''
    if generation.deepsearch:
        # Best-effort : un échec de la recherche web ne doit jamais bloquer la
        # génération elle-même, seulement priver le prompt de ce contexte en plus.
        try:
            resultat_recherche = mistral_client.rechercher_web(
                f"Vérifie les règles actuelles du Code de la route français pour le "
                f"thème « {generation.theme.nom} », niveau {generation.difficulte}, "
                f"pertinentes pour fiabiliser des questions d'examen théorique."
            )
            contexte_verifie = resultat_recherche['texte']
        except (mistral_client.MistralNonConfigure, mistral_client.MistralError):
            pass

    system, message, schema = prompts_mistral.construire_prompt_generation(
        generation.theme.nom, generation.difficulte, generation.nombre_demande, echantillon,
        contexte_verifie=contexte_verifie,
    )
    generation.prompt_utilise = message

    try:
        resultat = mistral_client.completer_json(system, message, schema)
    except (mistral_client.MistralNonConfigure, mistral_client.MistralError) as exc:
        generation.statut = 'erreur'
        generation.erreur_message = str(exc)
        generation.save(update_fields=['statut', 'erreur_message', 'prompt_utilise'])
        return

    nombre_genere = 0
    for q_data in resultat.get('questions', []):
        reponses_data = q_data.get('reponses', [])
        # Une question sans réponse correcte identifiée est inexploitable dans
        # un quiz — on l'écarte plutôt que de la proposer cassée à la validation.
        if not any(r.get('correcte') for r in reponses_data):
            continue
        question = Question.objects.create(
            theme=generation.theme,
            enonce=q_data.get('enonce', ''),
            type=q_data.get('type', 'qcm_unique'),
            difficulte=generation.difficulte,
            explication_generale=q_data.get('explication_generale', ''),
            origine='ia',
            statut='proposee',
            generation=generation,
        )
        for r_data in reponses_data:
            Reponse.objects.create(
                question=question,
                texte=r_data.get('texte', ''),
                correcte=bool(r_data.get('correcte')),
                explication=r_data.get('explication') or '',
            )
        nombre_genere += 1

    generation.nombre_genere = nombre_genere
    generation.statut = 'terminee' if nombre_genere > 0 else 'erreur'
    if nombre_genere == 0:
        generation.erreur_message = "Mistral n'a produit aucune question exploitable pour cette demande."
    generation.modele = ConfigurationMistral.get().modele
    generation.save(update_fields=['nombre_genere', 'statut', 'erreur_message', 'prompt_utilise', 'modele'])
