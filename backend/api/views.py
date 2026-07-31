import json
import mimetypes
from uuid import uuid4

from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import storage_client
from .models import Theme, FicheCours, SiteExterne
from .permissions import IsAdmin, IsAdminOrReadOnly
from .serializers import ThemeSerializer, FicheCoursSerializer, SiteExterneSerializer

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
