# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pheno_db', '0003_auto_20160812_0520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variabledescriptor',
            name='regards_family',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='variabledescriptor',
            name='regards_father',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='variabledescriptor',
            name='regards_mother',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='variabledescriptor',
            name='regards_other',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='variabledescriptor',
            name='regards_proband',
            field=models.NullBooleanField(),
        ),
        migrations.AlterField(
            model_name='variabledescriptor',
            name='regards_sibling',
            field=models.NullBooleanField(),
        ),
    ]
