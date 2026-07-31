import json
import mimetypes
import re
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import mistral_client, prompts_mistral, storage_client
from .tasks import analyser_resultats, generer_questions
from .models import (
    Theme, FicheCours, SiteExterne, Question, Reponse, QuizSession, QuizReponse,
    ConfigurationMistral, AnalyseIA, GenerationIA,
)
from .permissions import IsAdmin, IsAdminOrReadOnly
from .serializers import (
    ThemeSerializer, FicheCoursSerializer, SiteExterneSerializer,
    QuestionAdminSerializer, QuestionQuizSerializer, QuestionReviewSerializer,
    QuizSessionSerializer, QuizSessionDetailSerializer,
    ConfigurationMistralSerializer, AnalyseIASerializer,
    GenerationIASerializer, GenerationIADetailSerializer,
)

# Chemin storage du manifeste écrit par seed_illustrations_wikimedia (voir ce
# module pour le format : liste de {relative_path, nom, credit}).
WIKIMEDIA_MANIFEST_PATH = 'wikimedia/manifest.json'


def _auth_header(request) -> str:
    return f'Bearer {request.auth}'


class MeView(APIView):
    """GET /api/me/ — identité de l'utilisateur authentifié, depuis le JWT."""

    def get(self, request):
        email = request.user.email
        return Response({
            'email': email,
            'username': request.user.username,
            'groups': request.user.claims.get('groups', []),
            'is_admin': email.lower() in settings.ADMIN_EMAILS,
        })


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


def _upload_illustration(request, relative_prefix: str, file_obj) -> str:
    relative_path = f'{relative_prefix}/{uuid4().hex}-{file_obj.name}'
    result = storage_client.upload(
        _auth_header(request), relative_path, file_obj, file_obj.name,
        file_obj.content_type,
    )
    return result['relative_path']


def _delete_owned_illustration(request, path: str) -> None:
    """Supprime le fichier storage sauf s'il vient de la banque partagée
    Wikimedia (wikimedia/…) — ces fichiers peuvent être référencés par
    plusieurs fiches/questions, jamais possédés par une seule."""
    if path and not path.startswith('wikimedia/'):
        storage_client.delete(_auth_header(request), path)


class FicheCoursViewSet(viewsets.ModelViewSet):
    queryset = FicheCours.objects.select_related('theme').all()
    serializer_class = FicheCoursSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        theme_id = self.request.query_params.get('theme')
        if theme_id:
            qs = qs.filter(theme_id=theme_id)
        return qs

    def perform_create(self, serializer):
        illustration_file = serializer.validated_data.pop('illustration_file', None)
        # Sans fichier uploadé, illustration_path peut avoir été fourni directement
        # (sélection depuis la banque Wikimedia, cf. GET /api/illustrations-disponibles/).
        if illustration_file:
            serializer.save(illustration_path=_upload_illustration(self.request, 'fiches', illustration_file))
        else:
            serializer.save()

    def perform_update(self, serializer):
        illustration_file = serializer.validated_data.pop('illustration_file', None)
        if not illustration_file:
            serializer.save()
            return
        old_path = serializer.instance.illustration_path
        serializer.save(illustration_path=_upload_illustration(self.request, 'fiches', illustration_file))
        _delete_owned_illustration(self.request, old_path)

    def perform_destroy(self, instance):
        path = instance.illustration_path
        instance.delete()
        _delete_owned_illustration(self.request, path)

    @action(detail=True, methods=['get'])
    def illustration(self, request, pk=None):
        """Téléchargement authentifié de l'illustration — jamais d'accès anonyme
        (le cloisonnement de l'app, via KeycloakJWTAuthentication + IsAuthenticated,
        s'applique déjà à toute cette vue, comme à toute route protégée)."""
        fiche = self.get_object()
        if not fiche.illustration_path:
            return Response(status=404)
        tmp = storage_client.download_to_tempfile(_auth_header(request), fiche.illustration_path)
        content_type = mimetypes.guess_type(fiche.illustration_path)[0] or 'application/octet-stream'
        return FileResponse(tmp, content_type=content_type)


class SiteExterneViewSet(viewsets.ModelViewSet):
    queryset = SiteExterne.objects.all()
    serializer_class = SiteExterneSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class QuestionViewSet(viewsets.ModelViewSet):
    """Gestion de la banque de questions — réservée aux admins (IsAdmin, pas
    IsAdminOrReadOnly) : un usager ne parcourt jamais la banque brute avec les
    bonnes réponses visibles, seulement via le moteur de quiz (QuizDemarrerView),
    qui sert QuestionQuizSerializer sans les corrections."""

    queryset = Question.objects.select_related('theme').prefetch_related('reponses').all()
    serializer_class = QuestionAdminSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        theme_id = self.request.query_params.get('theme')
        statut = self.request.query_params.get('statut')
        if theme_id:
            qs = qs.filter(theme_id=theme_id)
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def perform_create(self, serializer):
        illustration_file = serializer.validated_data.pop('illustration_file', None)
        if illustration_file:
            serializer.save(illustration_path=_upload_illustration(self.request, 'questions', illustration_file))
        else:
            serializer.save()

    def perform_update(self, serializer):
        illustration_file = serializer.validated_data.pop('illustration_file', None)
        if not illustration_file:
            serializer.save()
            return
        old_path = serializer.instance.illustration_path
        serializer.save(illustration_path=_upload_illustration(self.request, 'questions', illustration_file))
        _delete_owned_illustration(self.request, old_path)

    def perform_destroy(self, instance):
        path = instance.illustration_path
        instance.delete()
        _delete_owned_illustration(self.request, path)

    @action(detail=True, methods=['get'])
    def illustration(self, request, pk=None):
        question = self.get_object()
        if not question.illustration_path:
            return Response(status=404)
        tmp = storage_client.download_to_tempfile(_auth_header(request), question.illustration_path)
        content_type = mimetypes.guess_type(question.illustration_path)[0] or 'application/octet-stream'
        return FileResponse(tmp, content_type=content_type)

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Fait passer une question `proposee` (générée par IA) à `validee` —
        jamais l'inverse d'une action de saisie manuelle (cf. Lot 4)."""
        question = self.get_object()
        question.statut = 'validee'
        question.save(update_fields=['statut'])
        return Response(QuestionAdminSerializer(question).data)

    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        """Une question rejetée reste en base (traçabilité) mais n'est plus
        jamais tirée dans un quiz — cf. QuizDemarrerView (statut='validee' uniquement)."""
        question = self.get_object()
        question.statut = 'rejetee'
        question.save(update_fields=['statut'])
        return Response(QuestionAdminSerializer(question).data)


def _questions_disponibles(themes_ids, difficulte):
    qs = Question.objects.filter(statut='validee').prefetch_related('reponses')
    if themes_ids:
        qs = qs.filter(theme_id__in=themes_ids)
    if difficulte:
        qs = qs.filter(difficulte=difficulte)
    return qs


class QuizDemarrerView(APIView):
    """POST /api/quiz/demarrer/ — {themes: [id...], difficulte, nombre_questions}."""

    def post(self, request):
        themes_ids = [int(t) for t in request.data.get('themes', []) if str(t).isdigit()]
        difficulte = request.data.get('difficulte') or ''
        try:
            nombre_questions = int(request.data.get('nombre_questions', 10))
        except (TypeError, ValueError):
            return Response({'detail': 'nombre_questions invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        nombre_questions = max(1, min(nombre_questions, 50))

        disponibles = list(_questions_disponibles(themes_ids, difficulte).order_by('?')[:nombre_questions])
        if not disponibles:
            return Response(
                {'detail': "Aucune question validée ne correspond à ces critères."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            session = QuizSession.objects.create(
                utilisateur_email=request.user.email,
                themes_filtres=','.join(str(t) for t in themes_ids),
                difficulte_filtree=difficulte,
                nombre_questions=len(disponibles),
            )
            QuizReponse.objects.bulk_create([
                QuizReponse(session=session, question=q, reponses_choisies=[], correcte=False)
                for q in disponibles
            ])

        return Response({
            'session': QuizSessionSerializer(session).data,
            'questions': QuestionQuizSerializer(disponibles, many=True).data,
        }, status=status.HTTP_201_CREATED)


def _get_owned_session(request, session_id) -> QuizSession:
    session = get_object_or_404(QuizSession, pk=session_id)
    if session.utilisateur_email.lower() != request.user.email.lower():
        raise PermissionDenied("Cette session de quiz ne vous appartient pas.")
    return session


class QuizRepondreView(APIView):
    """POST /api/quiz/<id>/repondre/ — {question: id, reponses_choisies: [id...], temps_ms}."""

    def post(self, request, session_id):
        session = _get_owned_session(request, session_id)
        if session.date_fin is not None:
            return Response({'detail': 'Cette session est déjà terminée.'}, status=status.HTTP_400_BAD_REQUEST)

        question_id = request.data.get('question')
        quiz_reponse = get_object_or_404(QuizReponse, session=session, question_id=question_id)
        reponses_choisies = request.data.get('reponses_choisies', [])
        if not isinstance(reponses_choisies, list):
            return Response({'detail': 'reponses_choisies doit être une liste.'}, status=status.HTTP_400_BAD_REQUEST)

        correct_ids = set(
            Reponse.objects.filter(question_id=question_id, correcte=True).values_list('id', flat=True)
        )
        choisies_ids = {int(r) for r in reponses_choisies if str(r).isdigit()}
        correcte = choisies_ids == correct_ids

        quiz_reponse.reponses_choisies = sorted(choisies_ids)
        quiz_reponse.correcte = correcte
        quiz_reponse.temps_ms = request.data.get('temps_ms')
        quiz_reponse.save()

        question = Question.objects.prefetch_related('reponses').get(pk=question_id)
        return Response({
            'correcte': correcte,
            'question': QuestionReviewSerializer(question).data,
        })


class QuizTerminerView(APIView):
    """POST /api/quiz/<id>/terminer/ — calcule le score, clôt la session."""

    def post(self, request, session_id):
        session = _get_owned_session(request, session_id)
        if session.date_fin is None:
            session.date_fin = timezone.now()
            session.score = session.reponses_donnees.filter(correcte=True).count()
            session.save(update_fields=['date_fin', 'score'])
            analyser_resultats.delay(session.utilisateur_email)

        return Response(QuizSessionSerializer(session).data)


class QuizHistoriqueView(APIView):
    """GET /api/quiz/historique/ — sessions de l'utilisateur courant, plus récentes d'abord."""

    def get(self, request):
        sessions = QuizSession.objects.filter(
            utilisateur_email__iexact=request.user.email,
        ).order_by('-date_debut')
        return Response(QuizSessionSerializer(sessions, many=True).data)


class QuizSessionDetailView(APIView):
    """GET /api/quiz/<id>/ — détail d'une session avec correction question par question."""

    def get(self, request, session_id):
        session = _get_owned_session(request, session_id)
        return Response(QuizSessionDetailSerializer(session).data)


class IllustrationsDisponiblesView(APIView):
    """GET /api/illustrations-disponibles/ — banque d'images Wikimedia amorcée
    par `seed_illustrations_wikimedia`, pour le sélecteur d'illustration côté
    admin (réutiliser une image déjà en storage plutôt que d'en uploader une
    nouvelle à chaque fiche/question)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        try:
            tmp = storage_client.download_to_tempfile(_auth_header(request), WIKIMEDIA_MANIFEST_PATH)
        except storage_client.StorageClientError:
            return Response([])
        with tmp:
            manifest = json.load(tmp)
        return Response(manifest)


class ConfigurationMistralView(APIView):
    """GET/PATCH /api/configuration-mistral/ — singleton, réservé aux
    ADMIN_EMAILS. `api_key` n'est jamais renvoyé (write-only, cf. serializer)."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response(ConfigurationMistralSerializer(ConfigurationMistral.get()).data)

    def patch(self, request):
        serializer = ConfigurationMistralSerializer(
            ConfigurationMistral.get(), data=request.data, partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MonBilanView(APIView):
    """GET /api/mon-bilan/ — dernière analyse IA de l'utilisateur courant.
    404 tant qu'aucun quiz n'a encore été terminé (pas d'AnalyseIA générée)."""

    def get(self, request):
        analyse = (
            AnalyseIA.objects
            .filter(utilisateur_email__iexact=request.user.email)
            .order_by('-date')
            .first()
        )
        if analyse is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(AnalyseIASerializer(analyse).data)


class GenerationIALancerView(APIView):
    """POST /api/generation-ia/lancer/ — {theme_id, difficulte, nombre_demande}.
    Toujours manuel (page admin), jamais déclenché automatiquement."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        theme = get_object_or_404(Theme, pk=request.data.get('theme_id'))
        difficulte = request.data.get('difficulte')
        if difficulte not in ('facile', 'moyen', 'difficile'):
            return Response({'detail': 'difficulte invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            nombre_demande = int(request.data.get('nombre_demande', 5))
        except (TypeError, ValueError):
            return Response({'detail': 'nombre_demande invalide.'}, status=status.HTTP_400_BAD_REQUEST)
        nombre_demande = max(1, min(nombre_demande, 20))
        deepsearch = bool(request.data.get('deepsearch'))

        generation = GenerationIA.objects.create(
            theme=theme, difficulte=difficulte, nombre_demande=nombre_demande,
            statut='en_cours', deepsearch=deepsearch,
        )
        generer_questions.delay(generation.id)
        return Response(GenerationIASerializer(generation).data, status=status.HTTP_201_CREATED)


class GenerationIAListView(APIView):
    """GET /api/generation-ia/ — historique des générations, plus récentes d'abord."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        generations = GenerationIA.objects.select_related('theme').order_by('-date')[:50]
        return Response(GenerationIASerializer(generations, many=True).data)


class GenerationIAStatutView(APIView):
    """GET /api/generation-ia/<id>/statut/ — polling (même pattern que la page
    Debug de lab-admin) : statut + questions produites une fois terminée."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, generation_id):
        generation = get_object_or_404(
            GenerationIA.objects.select_related('theme').prefetch_related('questions__reponses'),
            pk=generation_id,
        )
        return Response(GenerationIADetailSerializer(generation).data)


_RE_BLOC_JSON = re.compile(r'```json\s*(\{.*?\})\s*```', re.DOTALL)


def _extraire_proposition(texte: str) -> dict | None:
    """Cherche un bloc ```json {...} ``` dans la réponse de l'assistant fiches
    et le désérialise — best-effort, une réponse purement conversationnelle
    (question, discussion) n'en contient légitimement aucun."""
    match = _RE_BLOC_JSON.search(texte)
    if not match:
        return None
    try:
        proposition = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if proposition.get('action') not in ('creer', 'modifier'):
        return None
    return proposition


class AssistantFichesView(APIView):
    """POST /api/assistant-fiches/message/ — chat admin pour analyser, corriger,
    étendre ou créer des fiches de cours, avec le contenu déjà existant du thème
    en contexte. `deepsearch=True` (au premier message seulement — les outils
    sont fixés au démarrage de la conversation) active le connecteur web_search."""

    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        message = (request.data.get('message') or '').strip()
        if not message:
            return Response({'detail': 'message requis.'}, status=status.HTTP_400_BAD_REQUEST)

        conversation_id = request.data.get('conversation_id')
        deepsearch = bool(request.data.get('deepsearch'))

        try:
            if conversation_id:
                resultat = mistral_client.continuer_conversation(conversation_id, message)
            else:
                theme = get_object_or_404(Theme, pk=request.data.get('theme_id'))
                fiches = [
                    {'id': f.id, 'titre': f.titre, 'contenu': f.contenu}
                    for f in FicheCours.objects.filter(theme=theme).order_by('ordre')
                ]
                instructions = prompts_mistral.construire_contexte_assistant_fiches(theme.nom, fiches)
                resultat = mistral_client.demarrer_conversation(instructions, message, deepsearch=deepsearch)
        except mistral_client.MistralNonConfigure as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except mistral_client.MistralError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            'conversation_id': resultat['conversation_id'],
            'reponse_texte': resultat['texte'],
            'proposition': _extraire_proposition(resultat['texte']),
            'citations': resultat['citations'],
        })
