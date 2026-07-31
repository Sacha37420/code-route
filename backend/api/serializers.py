from rest_framework import serializers

from .models import (
    Theme, FicheCours, SiteExterne, Question, Reponse, QuizSession, QuizReponse,
    ConfigurationMistral, AnalyseIA, GenerationIA,
)


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


# ── Banque de questions (admin) ─────────────────────────────────────────────

class ReponseAdminSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = Reponse
        fields = ['id', 'texte', 'correcte', 'explication']


class QuestionAdminSerializer(serializers.ModelSerializer):
    """Vue complète (réponses + statut) — réservée aux admins, cf. IsAdmin sur
    QuestionViewSet. Un usager ne doit jamais parcourir la banque brute avec
    les bonnes réponses visibles en dehors d'un quiz (cf. QuestionQuizSerializer)."""

    reponses = ReponseAdminSerializer(many=True)
    illustration_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    theme_nom = serializers.CharField(source='theme.nom', read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'theme', 'theme_nom', 'enonce', 'type', 'difficulte',
            'illustration_path', 'illustration_credit', 'illustration_file',
            'explication_generale', 'origine', 'statut', 'generation', 'cree_le',
            'reponses',
        ]
        read_only_fields = ['origine', 'generation', 'cree_le']

    def create(self, validated_data):
        reponses_data = validated_data.pop('reponses')
        question = Question.objects.create(**validated_data)
        for reponse_data in reponses_data:
            reponse_data.pop('id', None)
            Reponse.objects.create(question=question, **reponse_data)
        return question

    def update(self, instance, validated_data):
        reponses_data = validated_data.pop('reponses', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if reponses_data is not None:
            gardees = set()
            for reponse_data in reponses_data:
                rid = reponse_data.pop('id', None)
                if rid and instance.reponses.filter(id=rid).exists():
                    Reponse.objects.filter(id=rid).update(**reponse_data)
                    gardees.add(rid)
                else:
                    nouvelle = Reponse.objects.create(question=instance, **reponse_data)
                    gardees.add(nouvelle.id)
            instance.reponses.exclude(id__in=gardees).delete()
        return instance


# ── Moteur de quiz (usager) ─────────────────────────────────────────────────

class ReponseQuizSerializer(serializers.ModelSerializer):
    """Sans `correcte` ni `explication` — envoyée pendant le quiz, avant
    correction, pour ne jamais exposer la bonne réponse au client."""

    class Meta:
        model = Reponse
        fields = ['id', 'texte']


class QuestionQuizSerializer(serializers.ModelSerializer):
    reponses = ReponseQuizSerializer(many=True)
    theme_nom = serializers.CharField(source='theme.nom', read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'theme', 'theme_nom', 'enonce', 'type', 'difficulte',
            'illustration_path', 'illustration_credit', 'reponses',
        ]


class QuestionReviewSerializer(serializers.ModelSerializer):
    """Vue complète d'une question une fois répondue — historique/correction."""

    reponses = ReponseAdminSerializer(many=True)
    theme_nom = serializers.CharField(source='theme.nom', read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'theme', 'theme_nom', 'enonce', 'type', 'difficulte',
            'illustration_path', 'illustration_credit', 'explication_generale', 'reponses',
        ]


class QuizReponseDetailSerializer(serializers.ModelSerializer):
    question = QuestionReviewSerializer(read_only=True)

    class Meta:
        model = QuizReponse
        fields = ['id', 'question', 'reponses_choisies', 'correcte', 'temps_ms']


class QuizSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSession
        fields = [
            'id', 'date_debut', 'date_fin', 'themes_filtres',
            'difficulte_filtree', 'nombre_questions', 'score',
        ]


class QuizSessionDetailSerializer(serializers.ModelSerializer):
    reponses_donnees = QuizReponseDetailSerializer(many=True, read_only=True)

    class Meta:
        model = QuizSession
        fields = [
            'id', 'date_debut', 'date_fin', 'themes_filtres',
            'difficulte_filtree', 'nombre_questions', 'score', 'reponses_donnees',
        ]


# ── Mistral (Lot 3) ──────────────────────────────────────────────────────────

class ConfigurationMistralSerializer(serializers.ModelSerializer):
    """`api_key` en écriture seule (jamais renvoyé par l'API, cf. brief) —
    `has_key` indique juste sa présence, comme restauration/robot-lab."""

    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_key = serializers.SerializerMethodField()

    class Meta:
        model = ConfigurationMistral
        fields = ['actif', 'api_key', 'has_key', 'modele', 'updated_at']
        read_only_fields = ['updated_at']

    def get_has_key(self, obj) -> bool:
        return bool(obj.api_key)

    def update(self, instance, validated_data):
        # Une chaîne vide dans api_key ne doit jamais effacer une clé déjà
        # enregistrée : le formulaire Paramétrage la laisse vide par défaut
        # (write-only, jamais réaffichée) pour ne pas changer la clé par erreur.
        nouvelle_cle = validated_data.pop('api_key', '')
        if nouvelle_cle:
            instance.api_key = nouvelle_cle
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AnalyseIASerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalyseIA
        fields = ['id', 'date', 'contenu', 'resume_texte']


# ── Génération IA de questions (Lot 4) ──────────────────────────────────────

class GenerationIASerializer(serializers.ModelSerializer):
    theme_nom = serializers.CharField(source='theme.nom', read_only=True)

    class Meta:
        model = GenerationIA
        fields = [
            'id', 'theme', 'theme_nom', 'difficulte', 'date', 'modele',
            'nombre_demande', 'nombre_genere', 'statut', 'erreur_message',
        ]
        read_only_fields = ['date', 'modele', 'nombre_genere', 'statut', 'erreur_message']


class GenerationIADetailSerializer(GenerationIASerializer):
    """Ajoute les questions produites par cette génération — pour la vue de
    résultat (polling), sans avoir à refaire un GET /api/questions/?generation=."""

    questions = QuestionAdminSerializer(many=True, read_only=True)

    class Meta(GenerationIASerializer.Meta):
        fields = GenerationIASerializer.Meta.fields + ['questions']
