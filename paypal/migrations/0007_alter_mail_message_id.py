# Generated by Django 5.1.7 on 2025-05-26 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('paypal', '0006_mail_mail_is_processed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mail',
            name='message_id',
            field=models.CharField(help_text='ID from Outlook', max_length=16, unique=True),
        ),
    ]
