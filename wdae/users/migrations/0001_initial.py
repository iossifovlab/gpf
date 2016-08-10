# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WdaeUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('first_name', models.CharField(max_length=b'100')),
                ('last_name', models.CharField(max_length=b'100')),
                ('email', models.EmailField(unique=True, max_length=254)),
                ('researcher_id', models.CharField(max_length=b'100', null=True, blank=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='Researcher',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('first_name', models.CharField(max_length=b'100')),
                ('last_name', models.CharField(max_length=b'100')),
                ('email', models.EmailField(unique=True, max_length=254)),
            ],
            options={
                'db_table': 'researchers',
            },
        ),
        migrations.CreateModel(
            name='ResearcherId',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('researcher_id', models.CharField(unique=True, max_length=b'100')),
                ('researcher', models.ManyToManyField(to='users.Researcher')),
            ],
            options={
                'db_table': 'researcherid',
            },
        ),
        migrations.CreateModel(
            name='VerificationPath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(unique=True, max_length=b'255')),
            ],
            options={
                'db_table': 'verification_paths',
            },
        ),
        migrations.AddField(
            model_name='wdaeuser',
            name='verification_path',
            field=models.OneToOneField(null=True, blank=True, to='users.VerificationPath'),
        ),
    ]
