"""Convert identifier columns from TEXT to VARCHAR(255).

Background (iossifovlab/gpf#836):

- The previous shape of migration 0009 set ``Dataset.dataset_id`` to
  ``TextField(unique=True)``. On MySQL/MariaDB that produces
  ``TEXT UNIQUE`` and fails at apply time with::

      MySQLdb.OperationalError: (1170, "BLOB/TEXT column 'dataset_id'
      used in key specification without a key length")

  0009 has therefore been amended in place to ``CharField(max_length=255,
  unique=True)`` so fresh MySQL deploys (and fresh deploys on every
  backend) get the right schema.

- ``Dataset.dataset_name`` and ``DatasetHierarchy.instance_id`` were
  also ``TextField`` for no good reason — they are short identifiers.
  This migration switches them to ``CharField(max_length=255)``.

- For existing Postgres deploys (e.g. SFARI / gain-web's ``gpfwa``)
  that already applied the old 0009 against ``TEXT``, the column is
  still ``TEXT UNIQUE``. The ``AlterField`` for ``dataset_id`` here
  is a no-op against the *Django model state* (0009 already declares
  ``CharField(max_length=255, unique=True)``), but ``schema_editor``
  emits the actual ``ALTER COLUMN ... TYPE VARCHAR(255)`` SQL against
  the DB, converting the column in place. On fresh deploys the
  column is already ``VARCHAR(255) UNIQUE`` and the alter is a cheap
  no-op.

The same logic applies to ``dataset_name`` and ``instance_id``: the
model state in 0005 / 0008 still says ``TextField``, so this
migration is the one that records the switch to ``CharField`` for
those two.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("datasets_api", "0009_dataset_dataset_id_unique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dataset",
            name="dataset_id",
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name="dataset",
            name="dataset_name",
            field=models.CharField(max_length=255, default=""),
        ),
        migrations.AlterField(
            model_name="datasethierarchy",
            name="instance_id",
            field=models.CharField(max_length=255),
        ),
    ]
