from django.shortcuts import redirect, render, render_to_response, HttpResponseRedirect, reverse
from django.db.models import Count
from django.db import connection
from .models import Kontostand, Kiosk, Einkaufsliste, ZumEinkaufVorgemerkt, Gekauft
from .models import GeldTransaktionen, ProduktVerkaufspreise, ZuVielBezahlt, Produktkommentar, Produktpalette
from profil.models import KioskUser
from profil.forms import UserErstellenForm, ConfirmPW
from django.template.loader import render_to_string
from django.http import HttpResponse

from .forms import EinkaufAnnahmeForm, TransaktionenForm, EinzahlungenForm, RueckbuchungForm
from .forms import NeuesProdukt_Palette, NeuesProdukt_Kommentar, NeuesProdukt_Kapazitaet, NeuesProdukt_Preis
from django.contrib.auth.decorators import login_required, permission_required
import math
from django.conf import settings
from django.utils import timezone
import datetime
from django.contrib.auth.models import Group
from .queries import readFromDatabase

from django.db import transaction

from .bot import checkKioskContentAndFillUp, slack_PostNewProductsInKioskToChannel, slack_PostWelcomeMessage, slack_PostTransactionInformation, slack_TestMsgToUser

from .charts import *


# Create your views here.

def start_page(request):
	
	# Einkaeufer des Monats
	data = readFromDatabase('getEinkaeuferDesMonats')
	bestBuyers = []
	for item in data:
		bestBuyers.append(item['first_name'] + ' ' + item['last_name'])
	bestBuyers = ', '.join(bestBuyers)

	# Verwalter des Monats
	data = readFromDatabase('getVerwalterDesMonats')
	bestVerwalter = []
	for item in data:
		bestVerwalter.append(item['first_name'] + ' ' + item['last_name'])
	bestVerwalter = ', '.join(bestVerwalter)

	# Administrator
	data = KioskUser.objects.filter(visible=True, rechte='Admin')
	admins = []
	for item in data:
		admins.append(item.first_name + ' ' + item.last_name)
	admins = ', '.join(admins)

	# Verwalter
	data = KioskUser.objects.filter(visible=True, rechte='Accountant')
	accountants = []
	for item in data:
		accountants.append(item.first_name + ' ' + item.last_name)
	accountants = ', '.join(accountants)
	

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()
 
	return render(request, 'kiosk/start_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		'bestBuyers': bestBuyers, 'bestVerwalter': bestVerwalter, 
		'admins': admins, 'accountants': accountants, 
		'chart_DaylyVkValue': Chart_DaylyVkValue(), })

@login_required
@permission_required('profil.perm_kauf',raise_exception=True)
def home_page(request):
	currentUser = request.user
	kontostand = Kontostand.objects.get(nutzer__username=request.user).stand / 100.0

	# Hole die eigene Liste, welche einzukaufen ist
	persEinkaufsliste = ZumEinkaufVorgemerkt.getMyZumEinkaufVorgemerkt(currentUser.id)

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/home_page.html', 
		{'currentUser': currentUser, 'kontostand': kontostand, 'persEinkaufsliste': persEinkaufsliste,
		'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste})


@login_required
@permission_required('profil.perm_kauf',raise_exception=True)
def kauf_page(request):
	if request.method == "POST":

		wannaBuyItem = request.POST.get("produktName")
		buySuccess = False
		buySuccess = Kiosk.buyItem(wannaBuyItem,request.user)

		# Ueberpruefung vom Bot, ob Einkaeufe erledigt werden muessen. Bei Bedarf werden neue Listen zur Einkaufsliste hinzugefuegt.
		checkKioskContentAndFillUp()

		return HttpResponseRedirect(reverse('gekauft_page'))


	else:
		# Hole den Kioskinhalt
		msg = ''
		allowed = True
		kioskItems = Kiosk.getKioskContent()
		currentUser = request.user
		kontostand = Kontostand.objects.get(nutzer__username=request.user).stand / 100.0

		# Check, ob der Kontostand noch positiv ist.
		# Auser der Dieb, dieser hat kein Guthaben und darf beliebig negativ werden.
		if kontostand <=0 and not currentUser.username=='Dieb':
			msg = 'Dein Kontostand ist zu niedrig. Bitte wieder beim Admin einzahlen.'
			allowed = False
		
		# Einkaufsliste abfragen
		einkaufsliste = Einkaufsliste.getEinkaufsliste()

		return render(request, 'kiosk/kauf_page.html', 
			{'currentUser': currentUser, 'kontostand': kontostand, 'kioskItems': kioskItems
			, 'einkaufsliste': einkaufsliste, 'msg': msg, 'allowed': allowed})


@login_required
@permission_required('profil.perm_kauf',raise_exception=True)
def gekauft_page(request):

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request,'kiosk/gekauft_page.html',{'kioskItems': kioskItems
			, 'einkaufsliste': einkaufsliste})


def kontobewegungen_page(request):
	s = 1
	return kontobewegungen_page_next(request,s)

@login_required
@permission_required('profil.perm_kauf',raise_exception=True)
def kontobewegungen_page_next(request,s):
	# Rufe alle Kontobewegungen ab, sowohl automatisch als auch manuell
	currentUser = request.user
	
	views = getattr(settings,'VIEWS')
	entriesPerPage = views['itemsInKontobewegungen']
	numTransactions = GeldTransaktionen.getLengthOfAllTransactions(request.user)
	try:
		numTransactions = numTransactions[0]["numTransactions"]
	except KeyError:
		numTransactions = numTransactions[0]["numtransactions"]
	
	maxPages = int(math.ceil(numTransactions/entriesPerPage))
	prevpage = int(s) - 1
	nextpage = int(s) + 1

	kontobewegungen = GeldTransaktionen.getTransactions(request.user,s,entriesPerPage,numTransactions)
	kontostand = Kontostand.objects.get(nutzer__username=request.user).stand / 100.0

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request,'kiosk/kontobewegungen_page.html',
		{'currentUser': currentUser, 'kontostand': kontostand, 'kontobewegungen': kontobewegungen,
		'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste, 
		'maxpage': maxPages, 'prevpage': prevpage, 'nextpage':nextpage})


@login_required
@permission_required('profil.do_einkauf',raise_exception=True)
def einkauf_vormerk_page(request):
	# Vormerken von Einkaeufen

	currentUser = request.user
	user = KioskUser.objects.get(id=currentUser.id)
	msg = ''
	color = '#ff0000'

	if request.method == "POST":

		if "best" in request.POST.keys():
			# Bestaetigung des ersten Einkaufens kommt zurueck
			user.instruierterKaeufer = True
			user.save()
			msg = 'Nun kannst du Eink'+chr(228)+'ufe vormerken.'
			color = '#00ff00'
			
		elif not "ekID" in request.POST.keys():
			# Keine Bestaetigung wurde gemacht
			msg = 'Du hast die Instruktionen noch nicht best'+chr(228)+'tigt.'


		else:

			einkaufGroupID = request.POST.get("ekID")
			Einkaufsliste.einkaufGroupVormerken(einkaufGroupID,currentUser.id)

			return HttpResponseRedirect(reverse('vorgemerkt_page'))
			

	# Es kommt ein Request herein, um naehre Informationen zu Produkten zu bekommen
	elif request.method == "GET":
		if not request.GET.get("getCommentsOnProduct") is None:
			# Besorgen der angewaehlten Gruppen-ID
			gruppen_id = request.GET.get("gruppen_id")

			# Infomationen / Kommentare zu den Produkten besorgen
			information = Einkaufsliste.getCommentsOnProducts(gruppen_id)
			
			html = render_to_string('kiosk/einkauf_vormerk_page_comments.html',
				{'information': information})
			return HttpResponse(html)

	# Checken, ob User ein instruierter Kaeufer ist.
	isInstr = user.instruierterKaeufer

	# Hole die eigene Liste, welche einzukaufen ist
	#persEinkaufsliste = ZumEinkaufVorgemerkt.getMyZumEinkaufVorgemerkt(currentUser.id)
	
	# Einkaufsliste abfragen
	einkaufslisteComp = Einkaufsliste.getEinkaufslisteCompressed()	

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/einkauf_vormerk_page.html', 
		{'currentUser': currentUser, 'einkaufslisteComp': einkaufslisteComp, 'isInstr': isInstr,
		#'persEinkaufsliste':persEinkaufsliste, 
		'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste, 'msg': msg, 'color': color})



@login_required
@permission_required('profil.do_einkauf',raise_exception=True)
def vorgemerkt_page(request):
	
	currentUser = request.user
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()
	# Hole die eigene Liste, welche einzukaufen ist
	persEinkaufsliste = ZumEinkaufVorgemerkt.getMyZumEinkaufVorgemerkt(currentUser.id)

	return render(request,'kiosk/vorgemerkt_page.html',
		{'currentUser': currentUser,'persEinkaufsliste':persEinkaufsliste,'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste})


# Der Verwalter pflegt den Einkauf ins System ein
@login_required
@permission_required('profil.do_verwaltung',raise_exception=True)
def einkauf_annahme_page(request):

	if request.method == "POST":
		# Hier kommt der Post mit dem Einkaeufer, der Ware und dem Preis
		
		form = EinkaufAnnahmeForm(request.POST)
		currentUser = request.user

		returnDict = ZumEinkaufVorgemerkt.einkaufAnnehmen(form,currentUser)

		if getattr(settings,'ACTIVATE_SLACK_INTERACTION') == True:
			try:
				slack_PostNewProductsInKioskToChannel(returnDict['angeliefert'])
			except:
				pass

		request.session['annahme_data'] = returnDict['returnHttp']
		return HttpResponseRedirect(reverse('einkauf_angenommen_page'))

	else:

		if not request.GET.get("getUserData") is None:
			# Einkaeufer wurde ausgewaehlt, jetzt seine vorgemerkten Einkaeufe zurueckgeben
			userID = request.GET.get("userID")

			seineVorgemerktenEinkaeufe = ZumEinkaufVorgemerkt.getMyZumEinkaufVorgemerkt(userID)
			userName = KioskUser.objects.get(id=userID)
			html = render_to_string('kiosk/einkauf_annahme_page_ekListe.html',
				{'seineVorgemerktenEinkaeufe': seineVorgemerktenEinkaeufe, 'userName': userName})
			return HttpResponse(html)
			
		else:

			currentUser = request.user
			# Besorge alle User
			allUsers = readFromDatabase('getUsersToBuy')
			# Hier auch nach Einkaeufer und hoeher filtern, User duerfen nichts einkaufen.
			# Hole den Kioskinhalt
			kioskItems = Kiosk.getKioskContent()

			# Einkaufsliste abfragen
			einkaufsliste = Einkaufsliste.getEinkaufsliste()

			return render(request, 'kiosk/einkauf_annahme_page.html', 
				{'currentUser': currentUser, 'allUsers': allUsers,  
				'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste})


@login_required
@permission_required('profil.do_verwaltung',raise_exception=True)
def einkauf_angenommen_page(request):

	currentUser = request.user
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	if 'annahme_data' in request.session.keys():
		annahme_data = request.session['annahme_data']
		del request.session['annahme_data']
	else:
		return HttpResponseRedirect(reverse('home_page'))

	annahme_data['currentUser'] = currentUser
	annahme_data['kioskItems'] = kioskItems
	annahme_data['einkaufsliste'] = einkaufsliste
	return render(request,'kiosk/einkauf_angenommen_page.html',annahme_data)

@login_required
@permission_required('profil.do_admin_tasks',raise_exception=True)
def transaktion_page(request):

	currentUser = request.user
	errorMsg = ''
	if request.method == "POST":
		# Hier kommen die eingegebenen Daten der Transaktion an.
		form = TransaktionenForm(request.POST)

		schuldner = KioskUser.objects.get(id=form['idFrom'].value())
		schuldnerKto = Kontostand.objects.get(nutzer=schuldner)

		if not form.is_valid():
			errorMsg = 'Fehler in der Eingabe, bitte erneut eingeben.'

		elif form['idTo'].value() == form['idFrom'].value():
			errorMsg = chr(220)+'berweiser und Empf'+chr(228)+'nger sind identisch.'

		elif int(100*float(form['betrag'].value())) > schuldnerKto.stand and schuldner.username!='Bank':
			errorMsg = 'Kontostand des Schuldners ist nicht gedeckt.'

		else:
			returnHttp = GeldTransaktionen.makeManualTransaktion(form,currentUser)

			if getattr(settings,'ACTIVATE_SLACK_INTERACTION') == True:
				try:
					slack_PostTransactionInformation(returnHttp)
				except:
					pass

			request.session['transaktion_data'] = returnHttp['returnDict']
			return HttpResponseRedirect(reverse('transaktion_done_page'))
			
	# Besorge alle User
	#allUsers = KioskUser.objects.filter(visible=True).order_by('username')
	allUsers = readFromDatabase('getUsersForTransaction')

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/transaktion_page.html', 
		{'user': currentUser, 'allUsers': allUsers,  
		'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		'errorMsg': errorMsg})


@login_required
@permission_required('profil.do_admin_tasks',raise_exception=True)
def transaktion_done_page(request):

	currentUser = request.user
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	if 'transaktion_data' in request.session.keys():
		transaktion_data = request.session['transaktion_data']
		del request.session['transaktion_data']
	else:
		return HttpResponseRedirect(reverse('home_page'))

	transaktion_data['currentUser'] = currentUser
	transaktion_data['kioskItems'] = kioskItems
	transaktion_data['einkaufsliste'] = einkaufsliste

	return render(request,'kiosk/transaktion_done_page.html',transaktion_data)


# Anmelden neuer Nutzer, Light-Version: Jeder darf das tun, aber nur Basics, jeder wird Standardnutzer
@transaction.atomic
def neuerNutzer_page(request):
	
	msg = ''
	color = '#ff0000'

	if request.method == "POST":

		res = UserErstellenForm(request.POST)
		pw = ConfirmPW(request.POST)

		if not res.is_valid():
			msg = 'Eingabefehler.'

		elif not pw['passwordcon'].value() == res['password'].value():
			msg = 'Passwort stimmt nicht ueberein.'

		else:			

			res.is_superuser = False
			res.is_staff = False
			res.is_active = True
			res.instruierterKaeufer = False
			res.rechte = 'User'
			res.visible = True

			u = KioskUser.objects.create_user(**res.cleaned_data)
			u.slackName = res['username'].value()
			u.save()
			g = Group.objects.get(name='Nutzer')
			g.user_set.add(u)

			k = Kontostand(nutzer_id = u.id, stand=0)
			k.save()


			msg = 'Nutzer wurde angelegt.'
			color = '#00ff00'

			if getattr(settings,'ACTIVATE_SLACK_INTERACTION') == True:
				try:
					slack_PostWelcomeMessage(u)
					msg += chr(10) + 'Dir wurde eine Nachricht per Slack zugesandt.'
				except:
					pass

			return HttpResponseRedirect(reverse('home_page'))


	form = UserErstellenForm()
	confPW = ConfirmPW()
	currentUser = request.user

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/neuerNutzer_page.html', 
		{'user': currentUser, 'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		'form':form, 'confPW': confPW, 'msg':msg, 'color': color})	


@login_required
@permission_required('profil.do_verwaltung',raise_exception=True)
def einzahlung_page(request):

	currentUser = request.user
	errorMsg = ''

	if request.method == "POST":

		# Hier kommen die eingegebenen Daten der Transaktion an.
		form = EinzahlungenForm(request.POST)

		if not form.is_valid():
			errorMsg = 'Fehler in der Eingabe, bitte erneut eingeben.'

		# Testen bei Auszahlung, ob nicht zu viel ausgezahlt wird
		else:
		
			if form['typ'].value() == 'Auszahlung':
				auszUser = KioskUser.objects.get(id=form['idUser'].value())
				auszKto = Kontostand.objects.get(nutzer=auszUser)
				
			if form['typ'].value() == 'Auszahlung' and int(100*float(form['betrag'].value())) > auszKto.stand:
					errorMsg = 'Das Konto deckt diesen Betrag nicht ab.'

			else:
				returnHttp = GeldTransaktionen.makeEinzahlung(form,currentUser)

				if getattr(settings,'ACTIVATE_SLACK_INTERACTION') == True:
					try:
						slack_PostTransactionInformation(returnHttp)
					except:
						pass
					
				request.session['einzahlung_data'] = {'type':returnHttp['type'],'betrag':returnHttp['betrag']}
				return HttpResponseRedirect(reverse('einzahlung_done_page'))
			
	# Besorge alle User
	allUsers = readFromDatabase('getUsersForEinzahlung')

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/einzahlung_page.html', 
		{'user': currentUser, 'allUsers': allUsers,  
		'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		'errorMsg': errorMsg})


@login_required
@permission_required('profil.do_verwaltung',raise_exception=True)
def einzahlung_done_page(request):
	currentUser = request.user
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	if 'einzahlung_data' in request.session.keys():
		einzahlung_data = request.session['einzahlung_data']
		del request.session['einzahlung_data']
	else:
		return HttpResponseRedirect(reverse('home_page'))

	einzahlung_data['currentUser'] = currentUser
	einzahlung_data['kioskItems'] = kioskItems
	einzahlung_data['einkaufsliste'] = einkaufsliste

	return render(request,'kiosk/einzahlung_done_page.html',einzahlung_data)



@login_required
@permission_required('profil.do_einkauf',raise_exception=True)
def meine_einkaufe_page(request):
	currentUser = request.user

	# Hole die eigene Liste, welche einzukaufen ist
	persEinkaufsliste = ZumEinkaufVorgemerkt.getMyZumEinkaufVorgemerkt(currentUser.id)

	# Bearbeitung eines Loeschvorgangs
	if request.method == "POST":
		# Ueberpruefung des Inputs
		idToDelete = int(request.POST.get("productID"))
		for item in persEinkaufsliste:
			if item["id"] == idToDelete:
				maxNumToDelete = item["anzahlElemente"]
				break
			else:
				maxNumToDelete = 0
		
		numToDelete = int(request.POST.get("noToDelete"))
		
		# Wenn Input passt, dann wird geloescht
		if numToDelete <= maxNumToDelete:
			ZumEinkaufVorgemerkt.objects.filter(pk__in=ZumEinkaufVorgemerkt.objects.filter(produktpalette__id=idToDelete).values_list('pk')[:numToDelete]).delete()

			# Testen, ob wieder Produkte auf die allgemeine Einkaufsliste muessen
			checkKioskContentAndFillUp()

		return HttpResponseRedirect(reverse('meine_einkaufe_page'))

	
	# Ausfuehren der normalen Seitendarstellung

	# Hole die eigene Liste, welche einzukaufen ist
	persEinkaufsliste = ZumEinkaufVorgemerkt.getMyZumEinkaufVorgemerkt(currentUser.id)

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/meine_einkaufe_page.html', 
		{'currentUser': currentUser, 'persEinkaufsliste': persEinkaufsliste,
		'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste})



@login_required
@permission_required('profil.do_admin_tasks',raise_exception=True)
def fillKioskUp(request):

	checkKioskContentAndFillUp()

	return redirect('home_page')


@login_required
@permission_required('profil.do_verwaltung', raise_exception=True)
def inventory(request):
	currentUser = request.user

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	# Get the kiosk-content, prepared for inventory form
	inventoryList = Kiosk.getKioskContentForInventory()

	# Processing the response of the inventory form
	if request.method == "POST":

		report = ZuVielBezahlt.makeInventory(request, currentUser, inventoryList)

		# Calculate the overall loss within this inventory
		loss = 0
		for item in report:
			if item['verlust'] == True:
				loss = loss + item["anzahl"] * item["verkaufspreis_ct"]
		loss = loss / 100

		tooMuch = 0
		for item in report:
			if item['verlust'] == False:
				tooMuch = tooMuch + item["anzahl"] * item["verkaufspreis_ct"]
		tooMuch = tooMuch / 100
		
		# Ueberpruefung vom Bot, ob Einkaeufe erledigt werden muessen. Bei Bedarf werden neue Listen zur Einkaufsliste hinzugefuegt.
		checkKioskContentAndFillUp()

		# Hole den Kioskinhalt
		kioskItems = Kiosk.getKioskContent()

		# Einkaufsliste abfragen
		einkaufsliste = Einkaufsliste.getEinkaufsliste()

		request.session['inventory_data'] = {'loss': loss, 'tooMuch':tooMuch,  
			'report': report,'kioskItems': kioskItems
			, 'einkaufsliste': einkaufsliste}
		return HttpResponseRedirect(reverse('inventory_done'))

	
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/inventory_page.html', 
		{'currentUser': currentUser, 'inventoryList': inventoryList,
		'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste}) 


@login_required
@permission_required('profil.do_verwaltung', raise_exception=True)
def inventory_done(request):
	currentUser = request.user
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	if 'inventory_data' in request.session.keys():
		inventory_data = request.session['inventory_data']
		del request.session['inventory_data']
	else:
		return HttpResponseRedirect(reverse('home_page'))

	inventory_data['currentUser'] = currentUser
	inventory_data['kioskItems'] = kioskItems
	inventory_data['einkaufsliste'] = einkaufsliste

	return render(request,'kiosk/inventory_conducted_page.html',inventory_data)


@login_required
@permission_required('profil.do_admin_tasks',raise_exception=True)
def statistics(request):

	# Geldwerte
	vkValueKiosk = readFromDatabase('getKioskValue')
	vkValueKiosk = vkValueKiosk[0]['value']
	vkValueAll = readFromDatabase('getVkValueAll')
	vkValueAll = vkValueAll[0]['value']

	ekValueKiosk = readFromDatabase('getKioskEkValue')
	ekValueKiosk = ekValueKiosk[0]['value']
	ekValueAll = readFromDatabase('getEkValueAll')
	ekValueAll = ekValueAll[0]['value']

	priceIncrease = round((vkValueAll-ekValueAll)/ekValueAll * 100.0, 1)

	kioskBankValue = Kontostand.objects.get(nutzer__username='Bank')
	kioskBankValue = kioskBankValue.stand / 100.0

	bargeld = Kontostand.objects.get(nutzer__username='Bargeld')
	bargeld = - bargeld.stand / 100.0

	usersMoneyValue = readFromDatabase('getUsersMoneyValue')
	usersMoneyValue = usersMoneyValue[0]['value']


	# Bezahlte und unbezahlte Ware im Kiosk (Tabelle gekauft)
	datum = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
	unBezahlt = readFromDatabase('getUmsatzUnBezahlt',[datum, datum, datum])
	for item in unBezahlt:
		if item['what'] == 'bezahlt': vkValueBezahlt = item['preis']
		if item['what'] == 'Dieb': stolenValue = item['preis']
		if item['what'] == 'alle': vkValueGekauft = item['preis']


	# Gewinn & Verlust
	theoAlloverProfit = vkValueAll - ekValueAll
	theoProfit = vkValueKiosk + kioskBankValue
	buyersProvision = theoAlloverProfit - theoProfit

	adminsProvision = 0
	profitHandback = 0

	expProfit = theoProfit - stolenValue - adminsProvision - profitHandback

	bilanzCheck = usersMoneyValue - bargeld - stolenValue + kioskBankValue
	checkExpProfit = -(usersMoneyValue -bargeld - vkValueKiosk)

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/statistics_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		'chart_Un_Bezahlt': Chart_Un_Bezahlt(), 
		'chart_UmsatzHistorie': Chart_UmsatzHistorie(),
		'chart_DaylyVkValue': Chart_DaylyVkValue(),
		'chart_Profits': Chart_Profits(),
		'chart_ProductsWin': Chart_ProductsWin(),
		'chart_ProductsCount': Chart_ProductsCount(),
		'chart_Stolen_ProductsWin': Chart_Stolen_ProductsWin(),
		'chart_StolenProductsShare': Chart_StolenProductsShare(),
		'vkValueBezahlt': vkValueBezahlt, 'stolenValue': stolenValue, 'vkValueGekauft': vkValueGekauft, 
		'relDieb': stolenValue/vkValueGekauft*100.0, 'relBezahlt': vkValueBezahlt/vkValueGekauft*100.0, 
		'vkValueKiosk': vkValueKiosk, 'kioskBankValue': kioskBankValue, 
		'vkValueAll': vkValueAll, 'ekValueAll': ekValueAll, 'ekValueKiosk': ekValueKiosk,
		'bargeld': bargeld, 'usersMoneyValue': usersMoneyValue, 
		'priceIncrease': priceIncrease, 'theoAlloverProfit': theoAlloverProfit, 
		'theoProfit': theoProfit, 'buyersProvision': buyersProvision, 
		'adminsProvision': adminsProvision, 'profitHandback': profitHandback, 
		'expProfit': expProfit, 'bilanzCheck': bilanzCheck, 'checkExpProfit': checkExpProfit}) 



@login_required
@permission_required('profil.do_einkauf',raise_exception=True)
def produktKommentare(request):

	# Besorge Liste aller Produktkommentare
	allProductComments = readFromDatabase('getAllProductComments')

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/produkt_kommentare_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		'allProductComments': allProductComments, })


@login_required
@permission_required('profil.do_einkauf',raise_exception=True)
def produktKommentieren(request, s):
	
	# Processing a new comment from the site
	if request.method == "POST":
		productID = int(request.POST.get("productID"))
		comment = request.POST.get("kommentar")

		p = Produktpalette.objects.get(id=productID)
		k = Produktkommentar(produktpalette = p, kommentar = comment)
		k.save()

		return HttpResponseRedirect(reverse('produkt_kommentieren_page', kwargs={'s':s}))
	
	productID = s

	# Besorge Liste aller Produktkommentare
	allCommentsOfProduct = readFromDatabase('getAllCommentsOfProduct',[productID])
	productName = allCommentsOfProduct[0]["produkt_name"]
	latestComment = allCommentsOfProduct[0]["kommentar"]

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/produkt_kommentieren_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		'allCommentsOfProduct': allCommentsOfProduct, 
		'productName': productName, 'productID': productID, 'latestComment': latestComment, })


def anleitung(request):

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/anleitung_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste})


@login_required
@permission_required('profil.do_verwaltung',raise_exception=True)
def rueckbuchung(request):

	currentUser = request.user

	if request.method == "POST":

		currentUser = request.user
		form = RueckbuchungForm(request.POST)

		session_data = Gekauft.rueckbuchen(form,currentUser)
		request.session['rueckbuchung_done'] = session_data
		return HttpResponseRedirect(reverse('rueckbuchung_done'))

	else:

		if not request.GET.get("getUserData") is None:
			# Kaeufer wurde ausgewaehlt, jetzt wird die Liste seiner Einkaeufe ausgegeben.
			userID = request.GET.get("userID")
			userName = KioskUser.objects.get(id=userID)
			seineKaeufe = readFromDatabase('getBoughtItemsOfUser', [userID])

			html = render_to_string('kiosk/rueckbuchungen_gekauft_liste.html',{'userID': userID, 'userName': userName, 'seineKaeufe': seineKaeufe})
			return HttpResponse(html)


	# Abfrage aller Nutzer
	allActiveUsers = KioskUser.objects.filter(is_active=True,visible=True)
	dieb = KioskUser.objects.filter(username='Dieb')
	allActiveUsers = allActiveUsers.union(dieb)

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/rueckbuchungen_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		'allActiveUsers': allActiveUsers, })

@login_required
@permission_required('profil.do_verwaltung',raise_exception=True)
def rueckbuchung_done(request):
	currentUser = request.user
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()
	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	if 'rueckbuchung_done' in request.session.keys():
		rueckbuchung_done = request.session['rueckbuchung_done']
		del request.session['rueckbuchung_done']
	else:
		return HttpResponseRedirect(reverse('home_page'))

	rueckbuchung_done['currentUser'] = currentUser
	rueckbuchung_done['kioskItems'] = kioskItems
	rueckbuchung_done['einkaufsliste'] = einkaufsliste

	return render(request,'kiosk/rueckbuchungen_done_page.html',rueckbuchung_done)


@login_required
@permission_required('profil.do_verwaltung',raise_exception=True)
def neuesProdukt(request):

	currentUser = request.user

	if request.method == "POST":
		pass

	
	formPalette = NeuesProdukt_Palette()
	formKommentar =  NeuesProdukt_Kommentar()
	formKapazitaet = NeuesProdukt_Kapazitaet()
	formPreis = NeuesProdukt_Preis()

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/neuesProdukt_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,
		 'formPalette':formPalette, 'formKommentar':formKommentar, 
		 'formKapazitaet':formKapazitaet, 'formPreis':formPreis,
		 'msg': '', 'color':'black', })


@login_required
@permission_required('profil.perm_kauf',raise_exception=True)
def slackComTest(request):

	currentUser = request.user
	slack_TestMsgToUser(currentUser)

	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/slackComTest_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste})
