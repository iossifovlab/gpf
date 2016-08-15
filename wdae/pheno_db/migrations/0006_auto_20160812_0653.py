# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pheno_db', '0005_auto_20160812_0600'),
    ]

    operations = [
        migrations.CreateModel(
            name='ValueFloat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('family_id', models.CharField(max_length=b'64', db_index=True)),
                ('person_id', models.CharField(max_length=b'64', db_index=True)),
                ('person_role', models.CharField(max_length=b'16', db_index=True)),
                ('variable_id', models.CharField(max_length=b'255', db_index=True)),
                ('value', models.FloatField()),
                ('descriptor', models.ForeignKey(to='pheno_db.VariableDescriptor')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterUniqueTogether(
            name='valuefloat',
            unique_together=set([('descriptor', 'person_id')]),
        ),
    ]
