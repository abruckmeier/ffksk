# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-12-19 18:38
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profil', '0009_auto_20190112_2032'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kioskuser',
            name='aktivBis',
            field=models.DateField(default=datetime.date(1999, 12, 31)),
        ),
    ]
