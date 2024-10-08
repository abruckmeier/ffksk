# Generated by Django 5.0.7 on 2024-07-17 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kiosk', '0010_auto_20190621_2249'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='einkaufsliste',
            options={'verbose_name': 'Einkaufsliste', 'verbose_name_plural': 'Einkaufslisten'},
        ),
        migrations.AlterModelOptions(
            name='einkaufslistegroups',
            options={'verbose_name': 'Einkaufslistengruppe', 'verbose_name_plural': 'Einkaufslistengruppen'},
        ),
        migrations.AlterModelOptions(
            name='gekauft',
            options={'verbose_name': 'Gekauft', 'verbose_name_plural': 'Gekauft'},
        ),
        migrations.AlterModelOptions(
            name='geldtransaktionen',
            options={'verbose_name': 'Geldtransaktion', 'verbose_name_plural': 'Geldtransaktionen'},
        ),
        migrations.AlterModelOptions(
            name='kiosk',
            options={'verbose_name': 'Kioskelement', 'verbose_name_plural': 'Kioskelemente'},
        ),
        migrations.AlterModelOptions(
            name='kioskkapazitaet',
            options={'verbose_name': 'Kapazität', 'verbose_name_plural': 'Kapazitäten'},
        ),
        migrations.AlterModelOptions(
            name='kontakt_nachricht',
            options={'verbose_name': 'Kontaktnachricht', 'verbose_name_plural': 'Kontaktnachrichten'},
        ),
        migrations.AlterModelOptions(
            name='kontostand',
            options={'verbose_name': 'Kontostand', 'verbose_name_plural': 'Kontostände'},
        ),
        migrations.AlterModelOptions(
            name='produktkommentar',
            options={'verbose_name': 'Produktkommentar', 'verbose_name_plural': 'Produktkommentare'},
        ),
        migrations.AlterModelOptions(
            name='produktpalette',
            options={'verbose_name': 'Produkt', 'verbose_name_plural': 'Produkte'},
        ),
        migrations.AlterModelOptions(
            name='produktverkaufspreise',
            options={'verbose_name': 'Produkt-Verkaufspreis', 'verbose_name_plural': 'Produkt-Verkaufspreise'},
        ),
        migrations.AlterModelOptions(
            name='start_news',
            options={'verbose_name': 'Startneuigkeit', 'verbose_name_plural': 'Startneuigkeiten'},
        ),
        migrations.AlterModelOptions(
            name='zumeinkaufvorgemerkt',
            options={'verbose_name': 'vorgemerktes Produkt', 'verbose_name_plural': 'vorgemerkte Produkte'},
        ),
        migrations.AlterModelOptions(
            name='zuvielbezahlt',
            options={'verbose_name': 'Zu viel bezahlt', 'verbose_name_plural': 'Zu viel bezahlt'},
        ),
        migrations.AlterField(
            model_name='produktpalette',
            name='farbeFuerPlot',
            field=models.CharField(blank=True, max_length=7),
        ),
        migrations.AlterField(
            model_name='produktpalette',
            name='imVerkauf',
            field=models.BooleanField(default=True),
        ),
    ]
