# -*- coding: utf-8 -*-
# flake8: noqa
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="QueryState",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("data", models.TextField()),
                (
                    "page",
                    models.CharField(
                        max_length=10,
                        choices=[
                            (b"genotype", b"Genotype browser"),
                            (b"phenotype", b"Phenotype browser"),
                            (b"enrichment", b"Enrichment tool"),
                            (b"phenotool", b"Phenotype tool"),
                        ],
                    ),
                ),
                ("uuid", models.UUIDField(default=uuid.uuid4)),
            ],
        ),
    ]
