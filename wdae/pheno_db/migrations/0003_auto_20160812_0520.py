# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pheno_db', '0002_auto_20160812_0513'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variabledescriptor',
            name='variable_category',
            field=models.CharField(max_length=b'127', null=True),
        ),
    ]
