from rest_framework import serializers

from .models import Theme, FicheCours, SiteExterne


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = ['id', 'nom', 'description', 'ordre']


class FicheCoursSerializer(serializers.ModelSerializer):
    illustration_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    theme_nom = serializers.CharField(source='theme.nom', read_only=True)

    class Meta:
        model = FicheCours
        fields = [
            'id', 'theme', 'theme_nom', 'titre', 'contenu', 'ordre',
            'illustration_path', 'illustration_credit', 'illustration_file',
        ]
        # illustration_path est normalement dérivé de illustration_file (upload) mais
        # reste écrivable directement pour réutiliser une image déjà en storage —
        # cf. le sélecteur alimenté par GET /api/illustrations-disponibles/
        # (banque Wikimedia amorcée par seed_illustrations_wikimedia).


class SiteExterneSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteExterne
        fields = ['id', 'nom', 'url', 'statut', 'offre_resume', 'date_verification', 'ordre']
