# Generated by Django 3.2.8 on 2021-11-19 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='stats',
            name='tiers',
            field=models.JSONField(default={'bronze': 0, 'diamond': 0, 'ghost': 0, 'gold': 0, 'silver': 0}),
        ),
    ]
