# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pheno_db', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='variabledescriptor',
            old_name='unique_variable_name',
            new_name='variable_name',
        ),
    ]
