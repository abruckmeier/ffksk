from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.start_page, name='start_page'),
	url(r'^menu/$', views.home_page, name='home_page'),
	url(r'^menu/kauf', views.kauf_page, name='kauf_page'),
	url(r'^menu/kontobewegungen$', views.kontobewegungen_page, name='kontobewegungen_page'),
	url(r'^menu/kontobewegungen/(?P<s>\d+)/$', views.kontobewegungen_page_next, name='kontobewegungen_page_next'),
	url(r'^menu/einkaufsvormerkungen', views.einkauf_vormerk_page, name = 'einkauf_vormerk_page'),
	url(r'^menu/einkaufsannahme$', views.einkauf_annahme_page, name = 'einkauf_annahme_page'),
	url(r'^menu/transaktion$', views.transaktion_page, name = 'transaktion_page'),
	url(r'^menu/neuerNutzer$', views.neuerNutzer_page, name = 'neuerNutzer_page'),
	url(r'^menu/einzahlung$', views.einzahlung_page, name = 'einzahlung_page'),
	url(r'^menu/meineeinkaufe$', views.meine_einkaufe_page, name = 'meine_einkaufe_page'),
	url(r'^menu/fillKioskUp$', views.fillKioskUp, name = 'fillKioskUp'),
]