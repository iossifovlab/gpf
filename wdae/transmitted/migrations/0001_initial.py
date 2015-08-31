# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GeneEffectVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('symbol', models.CharField(max_length=32, null=True, db_index=True)),
                ('effect_type', models.CharField(max_length=32, db_index=True)),
                ('variant_type', models.CharField(max_length=4)),
                ('n_par_called', models.IntegerField()),
                ('n_alt_alls', models.IntegerField()),
                ('alt_freq', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='SummaryVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ln', models.IntegerField(db_index=True)),
                ('chrome', models.CharField(max_length=3, db_index=True)),
                ('position', models.IntegerField()),
                ('variant', models.CharField(max_length=45)),
                ('variant_type', models.CharField(max_length=4)),
                ('effect_type', models.CharField(max_length=32, null=True, db_index=True)),
                ('effect_gene', models.CharField(max_length=32, null=True, db_index=True)),
                ('effect_count', models.IntegerField(default=0)),
                ('n_par_called', models.IntegerField()),
                ('n_alt_alls', models.IntegerField()),
                ('alt_freq', models.FloatField()),
                ('prcnt_par_called', models.FloatField()),
                ('seg_dups', models.IntegerField()),
                ('hw', models.FloatField()),
                ('ssc_freq', models.FloatField(null=True)),
                ('evs_freq', models.FloatField(null=True)),
                ('e65_freq', models.FloatField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name='geneeffectvariant',
            name='summary_variant',
            field=models.ForeignKey(related_name='effects', to='transmitted.SummaryVariant'),
        ),
    ]
