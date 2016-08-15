# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pheno_db', '0007_variabledescriptor_has_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='variabledescriptor',
            name='domain_rank',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='variabledescriptor',
            name='individuals',
            field=models.IntegerField(null=True),
        ),
    ]
