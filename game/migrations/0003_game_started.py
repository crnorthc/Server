# Generated by Django 3.2.8 on 2021-11-12 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0002_lineup_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='started',
            field=models.BooleanField(default=False),
        ),
    ]
