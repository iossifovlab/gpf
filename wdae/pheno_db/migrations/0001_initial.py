# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person_id', models.CharField(max_length=b'32', db_index=True)),
                ('role', models.CharField(max_length=b'16', db_index=True)),
                ('role_order', models.IntegerField()),
                ('role_id', models.CharField(max_length=b'8', db_index=True)),
                ('gender', models.CharField(max_length=b'1', db_index=True)),
                ('race', models.CharField(max_length=b'32', db_index=True)),
                ('family_id', models.CharField(max_length=16, db_index=True)),
                ('collection', models.CharField(max_length=b'64')),
                ('ssc_dataset', models.NullBooleanField()),
                ('v1', models.BooleanField()),
                ('v2', models.BooleanField()),
                ('v3', models.BooleanField()),
                ('v4', models.BooleanField()),
                ('v5', models.BooleanField()),
                ('v6', models.BooleanField()),
                ('v7', models.BooleanField()),
                ('v8', models.BooleanField()),
                ('v9', models.BooleanField()),
                ('v10', models.BooleanField()),
                ('v11', models.BooleanField()),
                ('v12', models.BooleanField()),
                ('v13', models.BooleanField()),
                ('v14', models.BooleanField()),
                ('v15', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='ValueFloat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('family_id', models.CharField(max_length=b'64', db_index=True)),
                ('person_id', models.CharField(max_length=b'64', db_index=True)),
                ('person_role', models.CharField(max_length=b'16', db_index=True)),
                ('variable_id', models.CharField(max_length=b'255', db_index=True)),
                ('value', models.FloatField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='VariableDescriptor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source', models.CharField(max_length=b'32')),
                ('table_name', models.CharField(max_length=b'64')),
                ('variable_name', models.CharField(max_length=b'127')),
                ('variable_category', models.CharField(max_length=b'127', null=True)),
                ('variable_id', models.CharField(unique=True, max_length=b'255', db_index=True)),
                ('domain', models.CharField(max_length=b'127', db_index=True)),
                ('domain_choice_label', models.CharField(max_length=b'255', null=True)),
                ('measurement_scale', models.CharField(max_length=b'32')),
                ('regards_mother', models.NullBooleanField()),
                ('regards_father', models.NullBooleanField()),
                ('regards_proband', models.NullBooleanField()),
                ('regards_sibling', models.NullBooleanField()),
                ('regards_family', models.NullBooleanField()),
                ('regards_other', models.NullBooleanField()),
                ('variable_notes', models.TextField(null=True)),
                ('is_calculated', models.BooleanField()),
                ('calculation_documentation', models.TextField(null=True)),
                ('has_values', models.NullBooleanField()),
                ('domain_rank', models.IntegerField(null=True)),
                ('individuals', models.IntegerField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='valuefloat',
            name='descriptor',
            field=models.ForeignKey(to='pheno_db.VariableDescriptor'),
        ),
        migrations.AlterUniqueTogether(
            name='valuefloat',
            unique_together=set([('descriptor', 'person_id')]),
        ),
    ]
