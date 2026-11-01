"""Réécrit chaque secret du coffre sous `VAULT_ENCRYPTION_KEY` (contrat failles, I3).

Lit les valeurs BRUTES (SQL, sans passer par le champ) : une valeur sous
l'ancienne clé (dérivée de SECRET_KEY) est rechiffrée, une valeur historique en
clair est chiffrée, une valeur indéchiffrable est LAISSÉE telle quelle — elle
est déjà traitée comme absente à la lecture, et l'écraser détruirait la seule
chance de la relire avec une ancienne SECRET_KEY retrouvée.
"""
import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def rechiffrer(apps, schema_editor):
    from api.fields import EncryptedTextField, Undecryptable, decrypt_raw, encrypt

    qn = schema_editor.quote_name
    with schema_editor.connection.cursor() as cur:
        for model in apps.get_app_config('api').get_models():
            for field in model._meta.concrete_fields:
                if not isinstance(field, EncryptedTextField):
                    continue
                table, col, pk = model._meta.db_table, field.column, model._meta.pk.column
                cur.execute(f'SELECT {qn(pk)}, {qn(col)} FROM {qn(table)} '
                            f"WHERE {qn(col)} IS NOT NULL AND {qn(col)} <> ''")
                for row_pk, raw in cur.fetchall():
                    try:
                        clair = decrypt_raw(raw)
                    except Undecryptable:
                        logger.warning('Coffre : %s.%s pk=%s indéchiffrable, laissé tel quel',
                                       table, col, row_pk)
                        continue
                    cur.execute(f'UPDATE {qn(table)} SET {qn(col)} = %s WHERE {qn(pk)} = %s',
                                [encrypt(clair), row_pk])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_generationia_deepsearch'),
    ]

    operations = [
        migrations.RunPython(rechiffrer, migrations.RunPython.noop),
    ]
