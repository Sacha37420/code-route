"""Champ de modèle chiffré au repos — coffre de l'app (`VAULT_ENCRYPTION_KEY`).

Avant le 2026-10-31 la clé Fernet était dérivée de `SECRET_KEY` : faire tourner
`SECRET_KEY` détruisait les secrets en silence, et une fuite de `SECRET_KEY` les
livrait. Désormais :

- on chiffre toujours avec `VAULT_ENCRYPTION_KEY` (clé Fernet propre au coffre) ;
- on lit aussi l'ancien chiffrement (clé dérivée de `SECRET_KEY`), par
  `MultiFernet` — la migration `0009_rechiffrer_coffre` réécrit chaque valeur
  existante sous la nouvelle clé ;
- une valeur qui ne se déchiffre sous aucune des deux clés n'est plus rendue
  telle quelle (c'était le texte chiffré, servi comme s'il était la clé) : elle
  est traitée comme absente, et journalisée sans sa valeur ;
- sauf si elle n'a pas la forme d'un jeton Fernet : c'est alors une valeur
  historique stockée en clair, rendue telle quelle (la migration la rechiffre).
"""
import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.db import models

logger = logging.getLogger(__name__)

# Tout jeton Fernet commence par l'octet de version 0x80 suivi de l'horodatage :
# en base64 urlsafe, « gAAAAA ».
FERNET_PREFIX = 'gAAAAA'


def _legacy_key() -> bytes:
    """Ancienne clé, dérivée de SECRET_KEY — lue seulement, jamais écrite."""
    return base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())


def _fernet() -> MultiFernet:
    # Pas de valeur par défaut : sans clé de coffre, l'app ne doit ni chiffrer
    # ni déchiffrer quoi que ce soit (AttributeError/ValueError bruyante).
    return MultiFernet([Fernet(settings.VAULT_ENCRYPTION_KEY), Fernet(_legacy_key())])


class Undecryptable(Exception):
    """Jeton Fernet qu'aucune des clés connues ne déchiffre."""


def decrypt_raw(raw: str) -> str:
    """Valeur en clair d'une valeur stockée.

    Lève `Undecryptable` pour un jeton Fernet qu'aucune clé ne déchiffre ; rend
    telle quelle une valeur qui n'a pas la forme d'un jeton (historique, en clair).
    """
    try:
        return _fernet().decrypt(raw.encode()).decode()
    except (InvalidToken, ValueError, UnicodeError):
        if raw.startswith(FERNET_PREFIX):
            raise Undecryptable from None
        return raw


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


class EncryptedTextField(models.TextField):
    """Chiffre la valeur avant écriture en base et la déchiffre à la lecture."""

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ''):
            return value
        return encrypt(value)

    def from_db_value(self, value, expression, connection):
        if value in (None, ''):
            return value
        try:
            return decrypt_raw(value)
        except Undecryptable:
            model = getattr(self, 'model', None)
            logger.warning(
                'Coffre : valeur indéchiffrable traitée comme absente (%s.%s)',
                model._meta.label if model is not None else '?', self.name,
            )
            return None if self.null else ''
