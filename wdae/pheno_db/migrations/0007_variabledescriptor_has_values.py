# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pheno_db', '0006_auto_20160812_0653'),
    ]

    operations = [
        migrations.AddField(
            model_name='variabledescriptor',
            name='has_values',
            field=models.NullBooleanField(),
        ),
    ]
