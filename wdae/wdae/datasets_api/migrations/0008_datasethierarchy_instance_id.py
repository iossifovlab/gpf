# Generated by Django 4.2.7 on 2024-01-10 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets_api', '0007_datasethierarchy_direct'),
    ]

    operations = [
        migrations.AddField(
            model_name='datasethierarchy',
            name='instance_id',
            field=models.TextField(default='DEFAULT_INSTANCE_ID_FROM_MIGRATION'),
            preserve_default=False,
        ),
    ]