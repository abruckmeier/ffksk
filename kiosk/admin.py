from django.contrib import admin
from .models import Produktpalette, Kioskkapazitaet, ProduktVerkaufspreise
from .models import Einkaufsliste, ZumEinkaufVorgemerkt, Kiosk, Gekauft, Kontostand, EinkaufslisteGroups, GeldTransaktionen

# Register your models here.
admin.site.register(Produktpalette)
admin.site.register(Kioskkapazitaet)
admin.site.register(ProduktVerkaufspreise)
admin.site.register(Einkaufsliste)
admin.site.register(ZumEinkaufVorgemerkt)
admin.site.register(Kiosk)
admin.site.register(Gekauft)
admin.site.register(GeldTransaktionen)
admin.site.register(Kontostand)
admin.site.register(EinkaufslisteGroups)