from django.contrib import admin
from .models import Produktpalette, Kioskkapazitaet, ProduktVerkaufspreise, Produktkommentar, Kontakt_Nachricht, Start_News
from .models import Einkaufsliste, ZumEinkaufVorgemerkt, Kiosk, Gekauft, Kontostand, EinkaufslisteGroups, GeldTransaktionen


class ProduktVerkaufspreiseAdmin(admin.ModelAdmin):

    def get_produktpalette_name(self, obj):
        return obj.produktpalette.produktName
    get_produktpalette_name.short_description = 'Produkt'
    get_produktpalette_name.admin_order_field = 'produktpalette__produktName'

    def get_verkaufspreis(self, obj):
        return f'{(obj.verkaufspreis/100):.2f} €'
    get_verkaufspreis.short_description = 'Verkaufspreis'
    get_verkaufspreis.admin_order_field = 'verkaufspreis'

    def get_preis_aufstockung(self, obj):
        return f'{(obj.preisAufstockung/100):.2f} €'
    get_preis_aufstockung.short_description = 'Preis Aufstockung'
    get_preis_aufstockung.admin_order_field = 'preisAufstockung'

    list_display = ('pk', 'get_produktpalette_name', 'get_verkaufspreis', 'get_preis_aufstockung', 'gueltigAb')
    list_filter = (
        get_produktpalette_name.admin_order_field,
        'gueltigAb',
    )


# Register your models here.
admin.site.register(Produktpalette)
admin.site.register(Kioskkapazitaet)
admin.site.register(ProduktVerkaufspreise, ProduktVerkaufspreiseAdmin)
admin.site.register(Einkaufsliste)
admin.site.register(ZumEinkaufVorgemerkt)
admin.site.register(Kiosk)
admin.site.register(Gekauft)
admin.site.register(GeldTransaktionen)
admin.site.register(Kontostand)
admin.site.register(EinkaufslisteGroups)
admin.site.register(Produktkommentar)
admin.site.register(Kontakt_Nachricht)
admin.site.register(Start_News)