from django.conf.urls import url
from . import views, slackCommands

urlpatterns = [
	url(r'^$', views.start_page, name='start_page'),
	url(r'^menu/$', views.home_page, name='home_page'),
	url(r'^menu/kauf', views.kauf_page, name='kauf_page'),
	url(r'^menu/gekauft', views.gekauft_page, name='gekauft_page'),
	url(r'^menu/kontobewegungen$', views.kontobewegungen_page, name='kontobewegungen_page'),
	url(r'^menu/kontobewegungen/(?P<s>\d+)/$', views.kontobewegungen_page_next, name='kontobewegungen_page_next'),
	url(r'^menu/einkaufsvormerkungen', views.einkauf_vormerk_page, name = 'einkauf_vormerk_page'),
	url(r'^menu/einkaufvorgemerkt', views.vorgemerkt_page, name = 'vorgemerkt_page'),
	url(r'^menu/einkaufsannahme$', views.einkauf_annahme_page, name = 'einkauf_annahme_page'),
	url(r'^menu/einkaufangenommen$', views.einkauf_angenommen_page, name = 'einkauf_angenommen_page'),
	url(r'^menu/transaktion$', views.transaktion_page, name = 'transaktion_page'),
	url(r'^menu/transaktiondone$', views.transaktion_done_page, name = 'transaktion_done_page'),
	url(r'^menu/neuerNutzer$', views.neuerNutzer_page, name = 'neuerNutzer_page'),
	url(r'^menu/einzahlung$', views.einzahlung_page, name = 'einzahlung_page'),
	url(r'^menu/einzahlungdone$', views.einzahlung_done_page, name = 'einzahlung_done_page'),
	url(r'^menu/meineeinkaufe$', views.meine_einkaufe_page, name = 'meine_einkaufe_page'),
	url(r'^menu/fillKioskUp$', views.fillKioskUp, name = 'fillKioskUp'),
	url(r'^menu/inventory$', views.inventory, name = 'inventory'),
	url(r'^menu/inventorydone$', views.inventory_done, name = 'inventory_done'),
	url(r'^menu/statistics$', views.statistics, name = 'statistics'),
	url(r'^menu/produktKommentare$', views.produktKommentare, name = 'produkt_kommentare_page'),
	url(r'^menu/produktKommentieren/(?P<s>\d+)/$', views.produktKommentieren, name='produkt_kommentieren_page'),
	url(r'^menu/anleitung$', views.anleitung, name = 'anleitung_page'),
	url(r'^menu/rueckbuchung$', views.rueckbuchung, name = 'rueckbuchungen_page'),
	url(r'^menu/rueckbuchungdone$', views.rueckbuchung_done, name = 'rueckbuchung_done'),
	url(r'^menu/slackComTest$', views.slackComTest, name = 'slackComTest_page'),

	url(r'^receiveSlackCommands/$', slackCommands.receiveSlackCommands, name = 'receiveSlackCommands'),
]