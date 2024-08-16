from django.contrib import admin
from .models import Produktpalette, Kioskkapazitaet, ProduktVerkaufspreise, Produktkommentar, Kontakt_Nachricht, Start_News
from .models import Einkaufsliste, ZumEinkaufVorgemerkt, Kiosk, Gekauft, Kontostand, EinkaufslisteGroups, GeldTransaktionen


class KioskkapazitaetInline(admin.TabularInline):
    model = Kioskkapazitaet
    extra = 0
    show_change_link = True


class KioskkapazitaetAdmin(admin.ModelAdmin):

    def get_produktpalette_name(self, obj):
        return f'[{obj.produktpalette.id}] {obj.produktpalette.produktName}'
    get_produktpalette_name.short_description = 'Produkt'
    get_produktpalette_name.admin_order_field = 'produktpalette__produktName'

    list_display = ('pk', 'get_produktpalette_name', 'maxKapazitaet', 'schwelleMeldung', 'paketgroesseInListe',)
    search_fields = ('get_produktpalette_name',)
    list_editable = ('maxKapazitaet', 'schwelleMeldung', 'paketgroesseInListe',)


class ProduktkommentarInline(admin.TabularInline):
    model = Produktkommentar
    extra = 0
    show_change_link = True


class ProduktkommentarAdmin(admin.ModelAdmin):

    def get_produktpalette_name(self, obj):
        return f'[{obj.produktpalette.id}] {obj.produktpalette.produktName}'
    get_produktpalette_name.short_description = 'Produkt'
    get_produktpalette_name.admin_order_field = 'produktpalette__produktName'

    list_display = ('pk', 'get_produktpalette_name', 'erstellt', 'kommentar',)
    list_filter = (get_produktpalette_name.admin_order_field, )
    search_fields = ('get_produktpalette_name', 'kommentar',)


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


class ProduktVerkaufspreiseInline(admin.TabularInline):
    model = ProduktVerkaufspreise
    extra = 0
    show_change_link = True


class ProduktpaletteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'produktName', 'imVerkauf', 'inAufstockung',)
    list_filter = ('imVerkauf', 'inAufstockung',)
    search_fields = ('produktName', 'pk',)
    list_editable = ('produktName', 'imVerkauf', 'inAufstockung',)
    inlines = [
        KioskkapazitaetInline,
        ProduktVerkaufspreiseInline,
        ProduktkommentarInline,
    ]


class KontostandAdmin(admin.ModelAdmin):

    def get_username(self, obj):
        return f'[{obj.nutzer.id}] {obj.nutzer.username}'
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'nutzer__username'

    def get_stand(self, obj):
        return f'{(obj.stand/100):.2f} €'
    get_stand.short_description = 'Kontostand'
    get_stand.admin_order_field = 'stand'

    list_display = ('pk', 'get_username', 'get_stand',)
    search_fields = ('get_username',)


class GeldTransaktionenAdmin(admin.ModelAdmin):

    def get_username_from(self, obj):
        return f'[{obj.vonnutzer.id}] {obj.vonnutzer.username}'
    get_username_from.short_description = 'Username von'
    get_username_from.admin_order_field = 'vonnutzer__username'

    def get_username_to(self, obj):
        return f'[{obj.zunutzer.id}] {obj.zunutzer.username}'
    get_username_to.short_description = 'Username zu'
    get_username_to.admin_order_field = 'zunutzer__username'

    def get_betrag(self, obj):
        return f'{(obj.betrag/100):.2f} €'
    get_betrag.short_description = 'Betrag'
    get_betrag.admin_order_field = 'betrag'

    list_display = ('pk', 'get_username_from', 'get_username_to', 'datum', 'get_betrag', 'kommentar',)
    list_filter = (get_username_from.admin_order_field, get_username_to.admin_order_field,)
    search_fields = ('get_username_from', 'get_username_to', 'kommentar',)


# Register your models here.
admin.site.register(Produktpalette, ProduktpaletteAdmin)
admin.site.register(Kioskkapazitaet, KioskkapazitaetAdmin)
admin.site.register(ProduktVerkaufspreise, ProduktVerkaufspreiseAdmin)
admin.site.register(Einkaufsliste)
admin.site.register(ZumEinkaufVorgemerkt)
admin.site.register(Kiosk)
admin.site.register(Gekauft)
admin.site.register(GeldTransaktionen, GeldTransaktionenAdmin)
admin.site.register(Kontostand, KontostandAdmin)
admin.site.register(EinkaufslisteGroups)
admin.site.register(Produktkommentar, ProduktkommentarAdmin)
admin.site.register(Kontakt_Nachricht)
admin.site.register(Start_News)
