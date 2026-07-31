"""Amorçage (seed) d'une banque de panneaux/marquages depuis Wikimedia Commons.

Travail ponctuel d'admin, pas un flux automatisé (voir to_do_code_route.md,
section « Sources de contenu ») : ce script dépose un premier lot de SVG
« France road sign » (catégorie Commons « Road signs of France », licence
CC-BY-SA) dans le partage storage de l'app, avec attribution. Il n'associe
RIEN automatiquement à une FicheCours/Question — c'est un admin qui choisit
ensuite, dans l'UI, quelle image utiliser pour quelle fiche/question, via le
manifeste écrit ici (wikimedia/manifest.json, lu par
GET /api/illustrations-disponibles/).

Les noms de fichiers réels sont découverts en interrogeant l'API MediaWiki de
Commons au moment de l'exécution (aucune liste figée dans le code) : la
catégorie peut évoluer, et on ne veut pas maintenir une liste de codes à la main.

Nécessite un token Bearer valide d'un compte membre du groupe autorisé de
l'app (obtenu en se connectant à code-route dans le navigateur — cf. page
Paramétrage, bouton « Copier mon token » — et collé ici une seule fois) :
storage n'a pas de compte de service pour cette app (cf. CLAUDE.md, pattern
carto-lab), le token de l'admin est simplement forwardé.

Exemple :
    python manage.py seed_illustrations_wikimedia --token eyJhbGci... --limit 20
"""
import json
import re

import requests
from django.core.management.base import BaseCommand, CommandError

from api import storage_client

COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
MANIFEST_PATH = 'wikimedia/manifest.json'
_TIMEOUT = 30
# Politique Wikimedia : les requêtes API sans User-Agent descriptif sont
# rejetées (403). Voir https://meta.wikimedia.org/wiki/User-Agent_policy
_HEADERS = {'User-Agent': 'code-route-lab-seed/1.0 (usage interne, non commercial)'}


class Command(BaseCommand):
    help = "Télécharge un premier lot de SVG 'France road sign' depuis Wikimedia Commons vers storage."

    def add_arguments(self, parser):
        parser.add_argument('--token', required=True, help='Token Bearer (JWT Keycloak) à forwarder à storage.')
        parser.add_argument('--limit', type=int, default=20, help='Nombre maximum de fichiers à importer.')

    def handle(self, *args, **options):
        auth_header = f"Bearer {options['token']}"
        limit = options['limit']

        self.stdout.write("Recherche des fichiers 'France road sign' sur Wikimedia Commons...")
        titles = self._list_category_files(limit)
        if not titles:
            raise CommandError("Aucun fichier trouvé dans cette catégorie Commons.")
        self.stdout.write(f"{len(titles)} fichier(s) trouvé(s).")

        manifest = self._load_existing_manifest(auth_header)
        imported = []

        for title in titles:
            info = self._get_file_info(title)
            if not info:
                self.stdout.write(self.style.WARNING(f"  ✗ {title} : impossible d'obtenir les métadonnées, ignoré."))
                continue

            filename = title.removeprefix('File:').replace(' ', '_')
            relative_path = f'wikimedia/{filename}'
            if any(e['relative_path'] == relative_path for e in manifest):
                self.stdout.write(f"  → {filename} : déjà importé, ignoré.")
                continue

            try:
                resp = requests.get(info['url'], headers=_HEADERS, timeout=_TIMEOUT)
                resp.raise_for_status()
            except requests.RequestException as exc:
                self.stdout.write(self.style.WARNING(f"  ✗ {filename} : téléchargement échoué ({exc})."))
                continue

            try:
                storage_client.upload(
                    auth_header, relative_path,
                    resp.content, filename, 'image/svg+xml',
                )
            except storage_client.StorageClientError as exc:
                self.stdout.write(self.style.WARNING(f"  ✗ {filename} : upload storage échoué ({exc})."))
                continue

            entry = {
                'relative_path': relative_path,
                'nom': filename,
                'credit': info['credit'],
            }
            manifest.append(entry)
            imported.append(entry)
            self.stdout.write(self.style.SUCCESS(f"  ✔ {filename} — {info['credit']}"))

        if imported:
            storage_client.upload(
                auth_header, MANIFEST_PATH,
                json.dumps(manifest, ensure_ascii=False, indent=2).encode(),
                'manifest.json', 'application/json',
            )
        self.stdout.write(self.style.SUCCESS(
            f"\n{len(imported)} nouvelle(s) illustration(s) importée(s) "
            f"({len(manifest)} au total dans le manifeste)."
        ))
        self.stdout.write(
            "Rien n'est associé automatiquement à une fiche/question — "
            "faites-le depuis l'UI d'admin (sélecteur d'illustration)."
        )

    def _load_existing_manifest(self, auth_header: str) -> list[dict]:
        try:
            tmp = storage_client.download_to_tempfile(auth_header, MANIFEST_PATH)
        except storage_client.StorageClientError:
            return []
        with tmp:
            return json.load(tmp)

    def _list_category_files(self, limit: int) -> list[str]:
        """Les panneaux français ne vivent pas dans une unique catégorie plate sur
        Commons (chaque code de panneau a sa propre sous-catégorie, ex.
        'Category:AB1 (road sign, France)') — on recherche donc directement les
        fichiers dont le titre suit la convention documentée dans le brief
        ('France road sign <code>.svg'), namespace File (ns=6)."""
        titles = []
        sroffset = 0
        while len(titles) < limit:
            params = {
                'action': 'query', 'list': 'search',
                'srsearch': 'intitle:"France road sign" filetype:drawing',
                'srnamespace': 6, 'srlimit': min(50, limit - len(titles)),
                'sroffset': sroffset, 'format': 'json',
            }
            try:
                resp = requests.get(COMMONS_API, params=params, headers=_HEADERS, timeout=_TIMEOUT)
                resp.raise_for_status()
                data = resp.json()
            except (requests.RequestException, ValueError) as exc:
                raise CommandError(f'API Wikimedia Commons injoignable : {exc}')

            results = data.get('query', {}).get('search', [])
            if not results:
                break
            for result in results:
                if result['title'].lower().endswith('.svg'):
                    titles.append(result['title'])

            sroffset = data.get('continue', {}).get('sroffset')
            if not sroffset:
                break
        return titles[:limit]

    def _get_file_info(self, title: str) -> dict | None:
        params = {
            'action': 'query', 'titles': title, 'prop': 'imageinfo',
            'iiprop': 'url|extmetadata', 'format': 'json',
        }
        try:
            resp = requests.get(COMMONS_API, params=params, headers=_HEADERS, timeout=_TIMEOUT)
            resp.raise_for_status()
            pages = resp.json().get('query', {}).get('pages', {})
        except (requests.RequestException, ValueError):
            return None

        page = next(iter(pages.values()), None)
        if not page or 'imageinfo' not in page:
            return None
        imageinfo = page['imageinfo'][0]
        extmeta = imageinfo.get('extmetadata', {})
        artist = extmeta.get('Artist', {}).get('value', '')
        # Le champ Artist contient parfois du HTML (liens) — on le nettoie grossièrement.
        artist = re.sub('<[^<]+?>', '', artist).strip() or 'Auteur non renseigné'
        licence = extmeta.get('LicenseShortName', {}).get('value', 'CC BY-SA')
        return {'url': imageinfo['url'], 'credit': f'{artist}, Wikimedia Commons, {licence}'}
