# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-11-05 16:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kiosk', '0005_remove_produktpalette_kommentar'),
    ]

    operations = [
        migrations.AddField(
            model_name='produktpalette',
            name='imVerkauf',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
