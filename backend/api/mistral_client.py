"""Appel à l'API Mistral hébergée.

Deux familles de fonctions :
- `completer_json()` — appel simple (Chat Completions, json_object) pour les
  besoins structurés existants (analyse post-quiz, génération de questions).
- `demarrer_conversation()` / `continuer_conversation()` — API Agents/Conversations
  de Mistral, seule à supporter le connecteur intégré `web_search` (« Deepsearch »).
  Utilisée par l'assistant fiches (chat) et par `rechercher_web()` (vérification
  factuelle avant génération de questions).

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


def _avec_retries(appel):
    """Exécute `appel` (fonction sans argument) avec la politique de retry
    commune (429/5xx/timeout), partagée par les deux familles d'appels."""
    last_error = None
    for delay in RETRY_DELAYS + [None]:
        try:
            return appel()
        except Exception as exc:                    # noqa: BLE001 — SDK tiers, erreurs hétérogènes
            last_error = exc
            if delay is None or not _is_transient(exc):
                raise MistralError(f'Appel Mistral en échec : {exc}') from exc
            time.sleep(delay)
    raise MistralError(f'Appel Mistral en échec : {last_error}')


def _client_et_modele():
    config = ConfigurationMistral.get()
    if not config.actif or not config.api_key:
        raise MistralNonConfigure(
            "Aucune clé Mistral active — un administrateur doit la configurer "
            "dans la page Paramétrage."
        )
    Mistral = _mistral_class()
    model = config.modele.strip() or 'mistral-large-latest'
    return Mistral(api_key=config.api_key), model


# ── Chat Completions (sorties JSON structurées) ─────────────────────────────

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

    raw = _avec_retries(lambda: _appeler(config.api_key, model, system, message, schema))

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MistralError(f'Réponse Mistral illisible (JSON invalide) : {exc}') from exc


# ── Agents / Conversations (chat + connecteur web_search « Deepsearch ») ────

def _parser_reponse_conversation(response, conversation_id_repli: str = '') -> dict:
    """Extrait {conversation_id, texte, citations} de la réponse de l'API
    Conversations. `content` d'une entrée 'message.output' est soit une simple
    chaîne (pas d'outil utilisé), soit une liste de chunks {type: text|tool_reference}
    quand un connecteur (ex. web_search) a été sollicité — vérifié en réel
    (2026-07-31) sur les deux cas."""
    conversation_id = getattr(response, 'conversation_id', None) or conversation_id_repli

    textes = []
    citations = []
    for entree in getattr(response, 'outputs', None) or []:
        if getattr(entree, 'type', None) != 'message.output':
            continue
        content = getattr(entree, 'content', None)
        if isinstance(content, str):
            textes.append(content)
            continue
        for chunk in content or []:
            chunk_type = getattr(chunk, 'type', None)
            if chunk_type == 'text':
                textes.append(getattr(chunk, 'text', ''))
            elif chunk_type == 'tool_reference':
                citations.append({
                    'title': getattr(chunk, 'title', ''),
                    'url': getattr(chunk, 'url', ''),
                })

    return {
        'conversation_id': conversation_id,
        'texte': ''.join(t for t in textes if t).strip(),
        'citations': citations,
    }


def demarrer_conversation(instructions: str, message: str, deepsearch: bool = False) -> dict:
    """Démarre une conversation Agents Mistral. `deepsearch=True` ajoute le
    connecteur intégré `web_search` — fonctionne uniquement via cette API
    (Agents/Conversations), pas via Chat Completions."""
    client, model = _client_et_modele()
    tools = [{'type': 'web_search'}] if deepsearch else []

    def _appel():
        agent = client.beta.agents.create(
            model=model,
            name='Assistant code-route',
            description="Assistant de rédaction des fiches de révision et de vérification factuelle du lab code-route.",
            instructions=instructions,
            tools=tools,
        )
        return client.beta.conversations.start(agent_id=agent.id, inputs=message)

    response = _avec_retries(_appel)
    return _parser_reponse_conversation(response)


def continuer_conversation(conversation_id: str, message: str) -> dict:
    client, _model = _client_et_modele()
    response = _avec_retries(
        lambda: client.beta.conversations.append(conversation_id=conversation_id, inputs=message)
    )
    return _parser_reponse_conversation(response, conversation_id_repli=conversation_id)


def rechercher_web(requete: str) -> dict:
    """Recherche web ponctuelle (Deepsearch), hors chat — utilisée par la
    génération de questions pour vérifier des faits avant de produire le
    few-shot. Best-effort : l'appelant doit tolérer un échec sans bloquer."""
    return demarrer_conversation(
        "Tu es un assistant de recherche qui vérifie des faits réglementaires "
        "du Code de la route français. Réponds de façon factuelle, concise "
        "(quelques phrases), en te fondant sur des sources officielles ou "
        "fiables trouvées via la recherche web.",
        requete,
        deepsearch=True,
    )
