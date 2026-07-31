"""Application Celery pour les tâches asynchrones (analyse IA, génération de questions)."""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('code_route')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
