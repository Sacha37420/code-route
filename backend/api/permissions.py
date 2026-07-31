from rest_framework.permissions import BasePermission
from django.conf import settings


class IsAdmin(BasePermission):
    """Email de l'utilisateur présent dans settings.ADMIN_EMAILS.

    Séparation simple admin/usager (pas de système de rôles complet) — voir
    dev/CLAUDE.md et to_do_code_route.md, section « Intégration Mistral ».
    """

    def has_permission(self, request, view) -> bool:
        email = getattr(request.user, 'email', '') or ''
        return email.lower() in settings.ADMIN_EMAILS


class IsAdminOrReadOnly(BasePermission):
    """Lecture pour tout utilisateur authentifié (déjà cloisonné par groupe via
    le JWT), écriture réservée aux ADMIN_EMAILS."""

    def has_permission(self, request, view) -> bool:
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        email = getattr(request.user, 'email', '') or ''
        return email.lower() in settings.ADMIN_EMAILS
