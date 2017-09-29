from django.shortcuts import redirect, render, render_to_response
from django.db.models import Count
from django.db import connection
from .models import Kontostand, Kiosk, Einkaufsliste, ZumEinkaufVorgemerkt
from .models import GeldTransaktionen, ProduktVerkaufspreise, ZuVielBezahlt
from profil.models import KioskUser
from profil.forms import UserErstellenForm, ConfirmPW
from django.template.loader import render_to_string
from django.http import HttpResponse

from .forms import EinkaufAnnahmeForm, TransaktionenForm, EinzahlungenForm
from django.contrib.auth.decorators import login_required, permission_required
import math
from django.conf import settings
from django.utils import timezone
import datetime
from django.contrib.auth.models import Group
from .queries import readFromDatabase

from django.db import transaction

from .bot import checkKioskContentAndFillUp

from jchart import Chart
from jchart.config import Axes, DataSet, rgba



# Create your views here.

def start_page(request):
	
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()
 
	return render(request, 'kiosk/start_page.html', 
		{'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste})

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

		# Hole den Kioskinhalt
		kioskItems = Kiosk.getKioskContent()
		# Einkaufsliste abfragen
		einkaufsliste = Einkaufsliste.getEinkaufsliste()

		return render(request,'kiosk/gekauft_page.html',
			{'buySuccess': buySuccess,'kioskItems': kioskItems
			, 'einkaufsliste': einkaufsliste})

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
			vormerkSuccess = False
			vormerkSuccess = Einkaufsliste.einkaufGroupVormerken(einkaufGroupID,currentUser.id)

			# Hole die eigene Liste, welche einzukaufen ist
			persEinkaufsliste = ZumEinkaufVorgemerkt.getMyZumEinkaufVorgemerkt(currentUser.id)

			# Hole den Kioskinhalt
			kioskItems = Kiosk.getKioskContent()
			# Einkaufsliste abfragen
			einkaufsliste = Einkaufsliste.getEinkaufsliste()

			return render(request,'kiosk/vorgemerkt_page.html',
				{'vormerkSuccess': vormerkSuccess,'currentUser': currentUser,'persEinkaufsliste':persEinkaufsliste,'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste})

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


# Der Verwalter pflegt den Einkauf ins System ein
@login_required
@permission_required('profil.do_verwaltung',raise_exception=True)
def einkauf_annahme_page(request):

	if request.method == "POST":
		# Hier kommt der Post mit dem Einkaeufer, der Ware und dem Preis
		
		form = EinkaufAnnahmeForm(request.POST)
		currentUser = request.user

		returnHttp = ZumEinkaufVorgemerkt.einkaufAnnehmen(form,currentUser)
		return HttpResponse(returnHttp)

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
			return HttpResponse(returnHttp)
			
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
				return HttpResponse(returnHttp)
			
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

		return render(request,'kiosk/inventory_conducted_page.html',
			{'loss': loss, 'tooMuch':tooMuch,  'report': report,'kioskItems': kioskItems
			, 'einkaufsliste': einkaufsliste})

	
	# Hole den Kioskinhalt
	kioskItems = Kiosk.getKioskContent()

	# Einkaufsliste abfragen
	einkaufsliste = Einkaufsliste.getEinkaufsliste()

	return render(request, 'kiosk/inventory_page.html', 
		{'currentUser': currentUser, 'inventoryList': inventoryList,
		'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste}) 




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
	unBezahlt = readFromDatabase('getUmsatzUnBezahlt',[timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
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
		'vkValueBezahlt': vkValueBezahlt, 'stolenValue': stolenValue, 'vkValueGekauft': vkValueGekauft, 
		'relDieb': stolenValue/vkValueGekauft*100.0, 'relBezahlt': vkValueBezahlt/vkValueGekauft*100.0, 
		'vkValueKiosk': vkValueKiosk, 'kioskBankValue': kioskBankValue, 
		'vkValueAll': vkValueAll, 'ekValueAll': ekValueAll, 'ekValueKiosk': ekValueKiosk,
		'bargeld': bargeld, 'usersMoneyValue': usersMoneyValue, 
		'priceIncrease': priceIncrease, 'theoAlloverProfit': theoAlloverProfit, 
		'theoProfit': theoProfit, 'buyersProvision': buyersProvision, 
		'adminsProvision': adminsProvision, 'profitHandback': profitHandback, 
		'expProfit': expProfit, 'bilanzCheck': bilanzCheck, 'checkExpProfit': checkExpProfit}) 



class Chart_Un_Bezahlt(Chart):
	chart_type = 'doughnut'
	responsive = True

	def get_datasets(self, **kwargs):
		data = readFromDatabase('getUmsatzUnBezahlt',[str(timezone.now)])
		for item in data:
			if item['what'] == 'bezahlt': bezahlt = item['preis']
			if item['what'] == 'Dieb': dieb = item['preis']
		data = [bezahlt, dieb]

		return [DataSet(
			data = data,
			backgroundColor = [rgba(0,255,0,0.2), rgba(255,0,0,0.2)]
		)]

	def get_labels(self, **kwargs):
		return( ['bezahlter Warenwert in &#8364;', 'unbezahlter Warenwert in &#8364;'] )


class Chart_UmsatzHistorie(Chart):
	chart_type = 'line'
	responsive = True
	scales = {
		'xAxes': [Axes(type='time', position='bottom')],
		'yAxes': [{'ticks':{'beginAtZero': True}, 'scaleLabel':{'display': True, 'labelString': 'Anteiliger Geldwert in %'}}]
	}

	def get_datasets(self, **kwargs):
		umsatzHistorie = readFromDatabase('getUmsatzHistorie')
		data = []
		for item in umsatzHistorie:
			data.append(round(item['dieb'] / item['allesUmsatz']*100.0,1))
		
		return [DataSet(
			data = data,
			label = 'unbezahlter Geldwert (Entwicklung)',
			backgroundColor = [rgba(0,0,255,0.2)]
		)]

	def get_labels(self, **kwargs):
		umsatzHistorie = readFromDatabase('getUmsatzHistorie')
		data = []
		for item in umsatzHistorie:
			data.append(item['datum'])

		return( data )


class Chart_DaylyVkValue(Chart):
	chart_type = 'line'
	responsive = True
	scales = {
		'xAxes': [Axes(type='time', position='bottom')],
		'yAxes': [{'ticks':{'beginAtZero': True}, 'scaleLabel':{'display': True, 'labelString': 'Geldwert in &#8364;'}}]
	}

	def get_datasets(self, **kwargs):
		daylyVKValue = readFromDatabase('getDaylyVKValue')
		data = []
		for item in daylyVKValue:
			data.append(item['dayly_value'])
		
		return [DataSet(
			data = data,
			label = 't&#228;licher Umsatz',
			backgroundColor = [rgba(0,0,255,0.2)]
		)]

	def get_labels(self, **kwargs):
		daylyVKValue = readFromDatabase('getDaylyVKValue')
		data = []
		for item in daylyVKValue:
			data.append(item['datum'])

		return( data )


class Chart_Profits(Chart):
	chart_type = 'doughnut'
	responsive = True

	def get_datasets(self, **kwargs):

		vkValueKiosk = readFromDatabase('getKioskValue')
		vkValueKiosk = vkValueKiosk[0]['value']
		vkValueAll = readFromDatabase('getVkValueAll')
		vkValueAll = vkValueAll[0]['value']
		ekValueAll = readFromDatabase('getEkValueAll')
		ekValueAll = ekValueAll[0]['value']
		kioskBankValue = Kontostand.objects.get(nutzer__username='Bank')
		kioskBankValue = kioskBankValue.stand / 100.0
		theoAlloverProfit = vkValueAll - ekValueAll
		theoProfit = vkValueKiosk + kioskBankValue
		buyersProvision = round(theoAlloverProfit - theoProfit,2)
		adminsProvision = 0
		profitHandback = 0
		unBezahlt = readFromDatabase('getUmsatzUnBezahlt',[timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
		for item in unBezahlt:
			if item['what'] == 'Dieb': stolenValue = item['preis']
		expProfit = round(theoProfit - stolenValue - adminsProvision - profitHandback,2)

		data = [buyersProvision, adminsProvision, profitHandback, stolenValue, expProfit]

		return [DataSet(
			data = data,
			backgroundColor = [rgba(0,0,255,0.2), rgba(0,0,255,0.4), rgba(0,0,255,0.6), rgba(0,0,255,0.8), rgba(0,255,0,0.6)]
		)]

	def get_labels(self, **kwargs):
		return( ['Provision der Eink&#228;fer in &#8364;', 'Provision f&#252;r Admin und Verwalter', 
			'Gewinnaussch&#252;ttung', 'gestohlener Geldwert','erwarteter Gewinn'] )
