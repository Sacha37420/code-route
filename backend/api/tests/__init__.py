"""Tests backend de code-route (chantier « tests », contrat v1).

Lancer : `python manage.py test` dans /app, base PostgreSQL jetable, aucun réseau.
Tout ce qui sort du conteneur est simulé : JWKS de Keycloak (clé locale), SDK
Mistral, appels HTTP vers `storage`, envoi des tâches Celery (les tâches sont
jouées en appel direct, sans courtier).
"""
