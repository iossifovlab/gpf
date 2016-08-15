# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pheno_db', '0008_auto_20160815_0442'),
    ]

    operations = [
        migrations.CreateModel(
            name='Individual',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person_id', models.CharField(max_length=b'32', db_index=True)),
                ('role', models.CharField(max_length=b'16', db_index=True)),
                ('gender', models.CharField(max_length=b'1', db_index=True)),
                ('race', models.CharField(max_length=b'32', db_index=True)),
                ('family_id', models.CharField(max_length=16, db_index=True)),
                ('collection', models.CharField(max_length=b'64')),
            ],
        ),
    ]
