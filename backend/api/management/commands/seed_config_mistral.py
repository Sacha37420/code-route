"""Amorçage idempotent de ConfigurationMistral depuis la variable d'env
MISTRAL_API_KEY (code-route/.env, jamais commise). N'écrit qu'une fois : si
ConfigurationMistral a déjà une clé enregistrée (via cette commande ou via la
page Paramétrage), elle n'est jamais écrasée — un admin peut ensuite la
changer sans que ce script la remette d'aplomb au déploiement suivant.

Appelée automatiquement au démarrage du conteneur backend (voir Dockerfile),
donc idempotente et silencieuse par défaut (best-effort, ne doit jamais faire
échouer le démarrage de l'app)."""
from django.core.management.base import BaseCommand
from django.conf import settings

from api.models import ConfigurationMistral


class Command(BaseCommand):
    help = "Initialise ConfigurationMistral depuis MISTRAL_API_KEY si aucune clé n'est déjà enregistrée."

    def handle(self, *args, **options):
        cle = settings.MISTRAL_API_KEY_BOOTSTRAP
        config = ConfigurationMistral.get()

        if config.api_key:
            self.stdout.write("ConfigurationMistral a déjà une clé enregistrée — rien à faire.")
            return

        if not cle:
            self.stdout.write("MISTRAL_API_KEY absente de l'environnement — rien à amorcer.")
            return

        config.api_key = cle
        config.actif = True
        config.save(update_fields=['api_key', 'actif', 'updated_at'])
        self.stdout.write(self.style.SUCCESS(
            "Clé Mistral amorcée depuis MISTRAL_API_KEY et configuration activée."
        ))
