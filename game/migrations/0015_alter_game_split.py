# Generated by Django 3.2.8 on 2021-11-27 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0014_playerhistory_ranking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='split',
            field=models.CharField(max_length=20),
        ),
    ]
