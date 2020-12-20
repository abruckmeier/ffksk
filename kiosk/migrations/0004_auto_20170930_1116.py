# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-30 09:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('kiosk', '0003_zuvielbezahlt'),
    ]

    operations = [
        migrations.CreateModel(
            name='Produktkommentar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('erstellt', models.DateTimeField(auto_now_add=True)),
                ('kommentar', models.TextField(blank=True, max_length=512)),
            ],
        ),
        migrations.AddField(
            model_name='produktpalette',
            name='farbeFuerPlot',
            field=models.TextField(blank=True, max_length=7),
        ),
        migrations.AddField(
            model_name='produktkommentar',
            name='produktpalette',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='kiosk.Produktpalette'),
        ),
    ]
