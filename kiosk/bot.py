from kiosk.queries import readFromDatabase
from kiosk.models import Produktpalette, Einkaufsliste, EinkaufslisteGroups
from profil.models import KioskUser
from django.db import transaction
from django.db.models import Max
import math

from django.conf import settings
from slackclient import SlackClient


def slack_PostWelcomeMessage(user):
	# Verwalter
	data = KioskUser.objects.filter(visible=True, rechte='Accountant')
	accountants = []
	for item in data:
		accountants.append(item.first_name + ' ' + item.last_name)
	accountants = ', '.join(accountants)

	textToChannel = ':tada: Willkommen im FfE-Kiosk! :tada:\n' + 'Als erstes, lade Guthaben auf dein Konto bei einem Verwalter (' + accountants + '). Dort bekommst du auch weitere Informationen zum Kiosk.\n' + 'In diesem Thread bekommst du weitere persoenliche Nachrichten zu Veraenderungen bei deinem Kontostand. Außerdem bekommst du allen wichtigen Informationen zu Neuanlieferungen, zu neuen Produkten in der Einkaufsliste und zu allen weiteren wichtigen Themen im #kiosk-Channel.\n\n' + 'Möchtest du mehr zum Kiosk beitragen? Gerne kannst du dich als Einkaeufer freischalten lassen und machst dann Besorgungen fuer das Kiosk.'
	userAdress = '@' + user.slackName

	slack_token = getattr(settings,'SLACK_TOKEN')
	sc = SlackClient(slack_token)
	sc.api_call(
		"chat.postMessage",
		channel=userAdress,
		text = textToChannel,
	)

	return

# Neue Produkte sind im Kiosk: Im Channel informieren
def slack_PostNewProductsInKioskToChannel(angeliefert):

	ang = set()
	for item in angeliefert:
		ang.add(item.produktpalette.produktName)

	textToChannel = ':tada: Frisch angeliefert: ' + ', '.join(ang) + ':grey_exclamation:'

	slack_token = getattr(settings,'SLACK_TOKEN')
	slackSettings = getattr(settings,'SLACK_SETTINGS')

	sc = SlackClient(slack_token)
	sc.api_call(
		"chat.postMessage",
		channel=slackSettings['channelToPost'],
		text = textToChannel,
	)

	return


# Neue Elemente in der Einkaufsliste in den Channel posten
def slack_PostNewItemsInShoppingListToChannel(newItems):

	if not newItems==set():
		textToChannel = ':mailbox_with_mail: Neue Produkte in der Einkaufsliste: ' + ', '.join(newItems) + ':grey_exclamation:'

		slack_token = getattr(settings,'SLACK_TOKEN')
		slackSettings = getattr(settings,'SLACK_SETTINGS')

		sc = SlackClient(slack_token)

		sc.api_call(
			"chat.postMessage",
			channel=slackSettings['channelToPost'],
			text = textToChannel,
		)

	return


# Information an Nutzer mit >30 Euro oder <1 Euro um Geld ausbezahlen zu lassen oder Geld einzuzahlen.
def slack_MsgToUserAboutNonNormalBankBalance(userID, bankBalance):
	
	user = KioskUser.objects.get(id = userID)

	# Functional Users (bank, thief) do not need messages
	if user.visible == False:
		return

	slack_token = getattr(settings,'SLACK_TOKEN')
	slackSettings = getattr(settings,'SLACK_SETTINGS')

	if bankBalance > slackSettings['MaxBankBalance']:
		number = '%.2f' % (slackSettings['MaxBankBalance']/100.0)
		textToChannel = ':money_with_wings: Dein Kontostand ist sehr hoch ( > ' + str(number) + ' Euro ). Bitte lass dir von einem Verwalter etwas Geld auszahlen :grey_exclamation:'

	elif bankBalance < slackSettings['MinBankBalance']:
		number = '%.2f' % (slackSettings['MinBankBalance']/100.0)
		textToChannel = ':dollar: Dein Kontostand ist niedrig ( < ' + str(number) + ' Euro ). Denke daran, rechtzeitig bei einem Verwalter wieder Geld einzubezahlen. :grey_exclamation:'

	else:
		return

	userAdress = '@' + user.slackName

	sc = SlackClient(slack_token)

	sc.api_call(
		"chat.postMessage",
		channel=userAdress,
		text = textToChannel,
	)

	return



# Nutzer inaktiv setzen, wenn letzter Tag zu Ende.
# Automatische DB-Sicherung
# Warnung an Admin und Verwalter, wenn Nutzer seinen letzten Tag haben wird (1 Woche vorher)
# Wenn Einkaufslisten-Elemente zu lange in persoenlicher Einkaufsliste verweilen, soll zuerst Meldung gegeben werden (5 Tage) und nach weiteren zwei Tagen wird das Element aus der persoenlichen Liste genommen.


@transaction.atomic
def checkKioskContentAndFillUp():
	# Alle Produkte im Umlauf (Kiosk, persoenliche und offene Einkaufsliste) werden zusammengezaehlt und der maximalen Anzahl im Kiosk gegenuebergestellt. Wird die Bestellschwelle unterschritten, werden entsprechend Produkte auf die Einkaufsliste gesetzt.

	newItems = set()
	kioskBilanz = readFromDatabase('getItemsInWholeKiosk')

	for item in kioskBilanz:
		if item["summe"] <= item["schwelleMeldung"]:
			
			itemsPerRound = item["paketgroesseInListe"]
			roundsFillUp = int(math.ceil((item["maxKapazitaet"] - item["summe"]) / itemsPerRound))

			p = Produktpalette.objects.get(id=item["id"])
			maxGroup = EinkaufslisteGroups.objects.all().aggregate(Max('gruppenID'))
			maxGroup = maxGroup["gruppenID__max"] + 1			

			for i in range(0,roundsFillUp):
				for j in range(0,itemsPerRound):
					e = Einkaufsliste(produktpalette = p)
					e.save()
					eg = EinkaufslisteGroups(einkaufslistenItem=e,gruppenID=maxGroup)
					eg.save()

					newItems.add(e.produktpalette.produktName)
				
				maxGroup = maxGroup + 1
	
	# Send message to the channel to inform about new Items in the shopping list
	if getattr(settings,'ACTIVATE_SLACK_INTERACTION') == True:
		try:
			slack_PostNewItemsInShoppingListToChannel(newItems)
		except:
			pass


	return

