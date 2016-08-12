# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VariableDescriptor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source', models.CharField(max_length=b'32')),
                ('table_name', models.CharField(max_length=b'64')),
                ('unique_variable_name', models.CharField(max_length=b'127')),
                ('variable_category', models.CharField(max_length=b'127')),
                ('variable_id', models.CharField(unique=True, max_length=b'255')),
                ('domain', models.CharField(max_length=b'127')),
                ('domain_choice_label', models.CharField(max_length=b'255', null=True)),
                ('measurement_scale', models.CharField(max_length=b'32')),
                ('regards_mother', models.BooleanField()),
                ('regards_father', models.BooleanField()),
                ('regards_proband', models.BooleanField()),
                ('regards_sibling', models.BooleanField()),
                ('regards_family', models.BooleanField()),
                ('regards_other', models.BooleanField()),
                ('variable_notes', models.TextField(null=True)),
                ('is_calculated', models.BooleanField()),
                ('calculation_documentation', models.TextField(null=True)),
            ],
        ),
    ]
