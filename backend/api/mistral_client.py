"""Appel à l'API Mistral hébergée — une seule fonction publique : `completer_json()`.

La clé n'est jamais loguée ni renvoyée : elle est lue en base (chiffrée au
repos, cf. `fields.EncryptedTextField` / `ConfigurationMistral`) juste avant
l'appel. Config globale au lab (pas de clé par utilisateur, cf.
to_do_code_route.md « Intégration Mistral ») : c'est le propriétaire du lab
qui paie l'usage API pour tout le groupe autorisé.
"""
import json
import time

from .models import ConfigurationMistral

MAX_TOKENS = 16000
# Le rate limit se dégage vite ; inutile d'attendre longtemps, mais il faut attendre.
RETRY_DELAYS = [3, 10]


class MistralNonConfigure(Exception):
    """Aucune clé active enregistrée (message affiché tel quel)."""


class MistralError(Exception):
    """Échec de l'appel — message affiché tel quel à l'appelant."""


def _is_transient(exc) -> bool:
    """429 (rate limit) et 5xx méritent une nouvelle tentative. Une clé invalide, non."""
    text = str(exc)
    return any(code in text for code in ('429', '500', '502', '503', '504', 'timeout', 'Timeout'))


def _mistral_class():
    """Le SDK Mistral a déplacé la classe en 2.x : `mistralai.client.Mistral`.
    En 1.x elle était à la racine. On accepte les deux plutôt que d'épingler
    une version précise."""
    try:
        from mistralai.client import Mistral
    except ImportError:
        from mistralai import Mistral
    return Mistral


def _appeler(api_key: str, model: str, system: str, message: str, schema: dict) -> str:
    Mistral = _mistral_class()  # import tardif : dépendance lourde, inutile hors usage IA
    client = Mistral(api_key=api_key)
    response = client.chat.complete(
        model=model,
        messages=[
            # Mistral n'a pas de sorties structurées par schéma : le schéma est
            # décrit dans le prompt, et `json_object` garantit au moins du JSON.
            {'role': 'system', 'content': f'{system}\n\nRéponds en JSON respectant ce schéma :\n'
                                          f'{json.dumps(schema, ensure_ascii=False)}'},
            {'role': 'user', 'content': message},
        ],
        response_format={'type': 'json_object'},
        temperature=0,
    )
    return response.choices[0].message.content or ''


def completer_json(system: str, message: str, schema: dict) -> dict:
    """Appelle Mistral avec la configuration active et renvoie le JSON désérialisé.

    Lève `MistralNonConfigure` si aucune clé n'est active, `MistralError` pour
    tout autre échec (après épuisement des tentatives sur erreurs transitoires).
    """
    config = ConfigurationMistral.get()
    if not config.actif or not config.api_key:
        raise MistralNonConfigure(
            "Aucune clé Mistral active — un administrateur doit la configurer "
            "dans la page Paramétrage."
        )
    model = config.modele.strip() or 'mistral-large-latest'

    last_error = None
    for delay in RETRY_DELAYS + [None]:
        try:
            raw = _appeler(config.api_key, model, system, message, schema)
            break
        except Exception as exc:                    # noqa: BLE001 — SDK tiers, erreurs hétérogènes
            last_error = exc
            if delay is None or not _is_transient(exc):
                raise MistralError(f'Appel Mistral en échec : {exc}') from exc
            time.sleep(delay)
    else:
        raise MistralError(f'Appel Mistral en échec : {last_error}')

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MistralError(f'Réponse Mistral illisible (JSON invalide) : {exc}') from exc
