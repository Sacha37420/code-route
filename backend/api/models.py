from django.db import models

from .fields import EncryptedTextField


class Theme(models.Model):
    """Grand thème de l'épreuve théorique (route, conducteur, sécurité...)."""

    nom = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True, default='')
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'themes'
        ordering = ['ordre', 'nom']

    def __str__(self) -> str:
        return self.nom


class FicheCours(models.Model):
    """Fiche de révision (markdown) rattachée à un thème."""

    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='fiches')
    titre = models.CharField(max_length=200)
    contenu = models.TextField(help_text='Markdown')
    ordre = models.PositiveIntegerField(default=0)
    illustration_path = models.CharField(max_length=500, blank=True, default='')
    illustration_credit = models.CharField(max_length=300, blank=True, default='')

    class Meta:
        db_table = 'fiches_cours'
        ordering = ['theme__ordre', 'ordre', 'titre']

    def __str__(self) -> str:
        return self.titre


class GenerationIA(models.Model):
    """Trace d'un lot de génération de questions par Mistral."""

    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('erreur', 'Erreur'),
    ]

    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='generations')
    difficulte = models.CharField(max_length=20, choices=[('facile', 'Facile'), ('moyen', 'Moyen'), ('difficile', 'Difficile')])
    date = models.DateTimeField(auto_now_add=True)
    prompt_utilise = models.TextField(blank=True, default='')
    modele = models.CharField(max_length=100, blank=True, default='')
    nombre_demande = models.PositiveIntegerField(default=0)
    nombre_genere = models.PositiveIntegerField(default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    erreur_message = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'generations_ia'
        ordering = ['-date']

    def __str__(self) -> str:
        return f'Génération {self.theme} / {self.difficulte} — {self.statut}'


class Question(models.Model):
    """Question de la banque, qu'elle soit d'origine humaine ou générée par IA."""

    TYPE_CHOICES = [
        ('qcm_unique', 'QCM à réponse unique'),
        ('qcm_multiple', 'QCM à réponses multiples'),
        ('vrai_faux', 'Vrai / Faux'),
    ]
    DIFFICULTE_CHOICES = [
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile'),
    ]
    ORIGINE_CHOICES = [
        ('humaine', 'Humaine'),
        ('ia', 'IA'),
    ]
    STATUT_CHOICES = [
        ('validee', 'Validée'),
        ('proposee', 'Proposée'),
        ('rejetee', 'Rejetée'),
    ]

    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='questions')
    enonce = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    difficulte = models.CharField(max_length=20, choices=DIFFICULTE_CHOICES)
    illustration_path = models.CharField(max_length=500, blank=True, default='')
    illustration_credit = models.CharField(max_length=300, blank=True, default='')
    explication_generale = models.TextField(blank=True, default='')
    origine = models.CharField(max_length=10, choices=ORIGINE_CHOICES, default='humaine')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='validee')
    generation = models.ForeignKey(
        GenerationIA, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions',
    )
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'questions'
        ordering = ['-cree_le']

    def __str__(self) -> str:
        return self.enonce[:80]


class Reponse(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reponses')
    texte = models.CharField(max_length=500)
    correcte = models.BooleanField(default=False)
    explication = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'reponses'

    def __str__(self) -> str:
        return self.texte[:60]


class QuizSession(models.Model):
    utilisateur_email = models.EmailField(max_length=255)
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    themes_filtres = models.CharField(max_length=200, blank=True, default='', help_text='CSV d\'IDs de Theme, vide = tous')
    difficulte_filtree = models.CharField(max_length=20, blank=True, default='')
    nombre_questions = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(null=True, blank=True, help_text='Nombre de bonnes réponses')

    class Meta:
        db_table = 'quiz_sessions'
        ordering = ['-date_debut']

    def __str__(self) -> str:
        return f'{self.utilisateur_email} — {self.date_debut:%Y-%m-%d %H:%M}'


class QuizReponse(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='reponses_donnees')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='+')
    reponses_choisies = models.JSONField(default=list, help_text='IDs de Reponse choisis')
    correcte = models.BooleanField(default=False)
    temps_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'quiz_reponses'
        unique_together = [('session', 'question')]

    def __str__(self) -> str:
        return f'{self.session_id} / {self.question_id}'


class AnalyseIA(models.Model):
    utilisateur_email = models.EmailField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    contenu = models.JSONField(default=dict)
    resume_texte = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'analyses_ia'
        ordering = ['-date']

    def __str__(self) -> str:
        return f'Analyse {self.utilisateur_email} — {self.date:%Y-%m-%d}'


class ConfigurationMistral(models.Model):
    """Singleton (pk=1) — clé API et modèle Mistral utilisés par le lab entier."""

    actif = models.BooleanField(default=False)
    api_key = EncryptedTextField(blank=True, default='')
    modele = models.CharField(max_length=100, default='mistral-large-latest')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'configuration_mistral'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self) -> str:
        return 'Configuration Mistral'


class SiteExterne(models.Model):
    STATUT_CHOICES = [
        ('gratuit', 'Gratuit'),
        ('freemium', 'Freemium'),
        ('payant', 'Payant'),
    ]

    nom = models.CharField(max_length=150)
    url = models.URLField(max_length=500)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES)
    offre_resume = models.TextField(blank=True, default='')
    date_verification = models.DateField(null=True, blank=True)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'sites_externes'
        ordering = ['ordre', 'nom']

    def __str__(self) -> str:
        return self.nom
