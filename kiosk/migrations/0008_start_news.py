# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-07-14 14:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('kiosk', '0007_kontakt_nachricht'),
    ]

    operations = [
        migrations.CreateModel(
            name='Start_News',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('heading', models.CharField(max_length=256)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('content', models.TextField(blank=True, max_length=2048)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('starred', models.BooleanField(default=False)),
                ('visible', models.BooleanField(default=True)),
            ],
        ),
    ]
