# Generated by Django 4.2.11 on 2024-07-09 10:09
# flake8: noqa
# type: ignore
# pylint: skip-file

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users_api', '0004_resetpasswordcode_setpasswordcode_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='GpUserState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.TextField()),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
