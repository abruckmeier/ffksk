from django.shortcuts import render, HttpResponseRedirect, reverse
from django.views import View
from django.contrib.auth.decorators import login_required
from kiosk.models import Kiosk, Einkaufsliste
from datetime import datetime

from .models import KioskUser
from .forms import AktivBisChangeForm


@login_required
def angestellt_bis_change(request):

	usr = KioskUser.objects.get(id=request.user.id)

	if request.method == "POST":

		aktivBisChangeForm = AktivBisChangeForm(request.POST)

		if aktivBisChangeForm.is_valid():
			date = aktivBisChangeForm.cleaned_data.get('aktivBis')
			usr.aktivBis = date
			usr.save()

			request.session['angestellt_bis_change'] = datetime.strftime(date,'%d.%m.%Y')
			return HttpResponseRedirect(reverse('angestellt_bis_changed'))

		else:
			aktivBisChangeForm = AktivBisChangeForm(request.POST)

	else:
		aktivBisChangeForm = AktivBisChangeForm(initial={'aktivBis':usr.aktivBis,})
	
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'profilVerwaltung/angestellt_bis_change.html', 
		{'aktivBisChangeForm': aktivBisChangeForm, 'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,})


@login_required
def angestellt_bis_changed(request):

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	if 'angestellt_bis_change' in request.session.keys():
		newDate = request.session['angestellt_bis_change']
		del request.session['angestellt_bis_change']
	else:
		return HttpResponseRedirect(reverse('home_page'))

	return render(request, 'profilVerwaltung/angestellt_bis_changed.html', 
		{'newDate': newDate, 'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,})