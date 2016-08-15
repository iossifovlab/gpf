# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pheno_db', '0004_auto_20160812_0524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variabledescriptor',
            name='domain',
            field=models.CharField(max_length=b'127', db_index=True),
        ),
        migrations.AlterField(
            model_name='variabledescriptor',
            name='variable_id',
            field=models.CharField(unique=True, max_length=b'255', db_index=True),
        ),
    ]
