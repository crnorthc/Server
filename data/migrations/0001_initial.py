# Generated by Django 3.2.8 on 2021-11-10 21:17

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Data',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hour', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(default=dict), default=list, size=None)),
                ('day', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(default=dict), default=list, size=None)),
                ('week', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(default=dict), default=list, size=None)),
                ('month', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(default=dict), default=list, size=None)),
                ('year', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(default=dict), default=list, size=None)),
                ('all', django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(default=dict), default=list, size=None)),
            ],
        ),
        migrations.CreateModel(
            name='Symbol',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=8)),
                ('crypto', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=80)),
                ('image', models.CharField(max_length=1000)),
                ('data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='data.data')),
            ],
        ),
    ]
