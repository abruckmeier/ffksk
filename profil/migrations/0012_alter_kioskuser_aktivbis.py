# Generated by Django 5.0.7 on 2024-07-17 07:28

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profil', '0011_kioskuser_paypal_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kioskuser',
            name='aktivBis',
            field=models.DateField(default=datetime.date(2024, 7, 17)),
        ),
    ]