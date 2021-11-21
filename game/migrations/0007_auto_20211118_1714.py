# Generated by Django 3.2.8 on 2021-11-18 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_auto_20211116_1439'),
    ]

    operations = [
        migrations.RenameField(
            model_name='lineup',
            old_name='price',
            new_name='close',
        ),
        migrations.AddField(
            model_name='game',
            name='ended',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='lineup',
            name='open',
            field=models.DecimalField(decimal_places=10, max_digits=25, null=True),
        ),
    ]