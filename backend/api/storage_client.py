"""Client minimal de l'API fichiers de l'app storage.

Un seul partage fixe ouvert en lecture/écriture à tout le groupe Keycloak
requis de l'app (Share.required_groups, cf. CLAUDE.md racine — « carte
commune, tout le groupe lit/écrit tout », comme carto-lab) : le token de
l'utilisateur courant est simplement forwardé vers storage (azp=code-route
doit figurer dans KEYCLOAK_TRUSTED_CLIENTS côté storage), pas de compte de
service ici.
"""
from __future__ import annotations

import os
import tempfile

import requests
from django.conf import settings

_TIMEOUT = 30


class StorageClientError(RuntimeError):
    """Erreur de communication avec l'API storage."""


def _namespace_url(suffix: str = '') -> str:
    return f"{settings.STORAGE_INTERNAL_URL}/api/files/{settings.STORAGE_NAMESPACE}/{suffix}"


def upload(auth_header: str, relative_path: str, fileobj, filename: str, content_type: str = '') -> dict:
    """Dépose `fileobj` dans le partage code-route, sous `relative_path`.
    Retourne le JSON de StoredFileSerializer (storage/backend/api/views.py)."""
    files = {'file': (filename, fileobj, content_type or 'application/octet-stream')}
    data = {'relative_path': relative_path}
    try:
        resp = requests.post(
            _namespace_url(), headers={'Authorization': auth_header},
            data=data, files=files, timeout=_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise StorageClientError(f'storage injoignable : {exc}') from exc
    if resp.status_code != 201:
        raise StorageClientError(f'Upload storage échoué (HTTP {resp.status_code}) : {resp.text[:200]}')
    return resp.json()


def download_to_tempfile(auth_header: str, relative_path: str) -> tempfile._TemporaryFileWrapper:
    """Télécharge le fichier dans un fichier temporaire ouvert (delete=True) et
    le retourne positionné au début. À l'appelant de le fermer (auto-suppression)."""
    url = f"{_namespace_url('content/')}{relative_path}"
    try:
        resp = requests.get(url, headers={'Authorization': auth_header}, stream=True, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise StorageClientError(f'storage injoignable : {exc}') from exc
    if resp.status_code != 200:
        raise StorageClientError(f'Téléchargement storage échoué (HTTP {resp.status_code}).')

    tmp = tempfile.NamedTemporaryFile(suffix=os.path.splitext(relative_path)[1])
    for chunk in resp.iter_content(chunk_size=65536):
        tmp.write(chunk)
    tmp.flush()
    tmp.seek(0)
    return tmp


def delete(auth_header: str, relative_path: str) -> None:
    url = f"{_namespace_url('content/')}{relative_path}"
    try:
        resp = requests.delete(url, headers={'Authorization': auth_header}, timeout=_TIMEOUT)
    except requests.RequestException as exc:
        raise StorageClientError(f'storage injoignable : {exc}') from exc
    if resp.status_code not in (204, 404):
        raise StorageClientError(f'Suppression storage échouée (HTTP {resp.status_code}).')
