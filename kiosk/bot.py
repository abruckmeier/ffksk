from kiosk.queries import readFromDatabase
from kiosk.models import Produktpalette, Einkaufsliste, EinkaufslisteGroups
from profil.models import KioskUser
from django.db import transaction
from django.db.models import Max
import math

from django.conf import settings
from slackclient import SlackClient


def slack_SendMsg(msg, user=None, channel=False):
	
	if channel==True:
		slackSettings = getattr(settings,'SLACK_SETTINGS')
		userAdress = '#'+slackSettings['channelToPost']
	else:
		userAdress = '@' + user.slackName	
		# Functional Users (bank, thief) do not need messages
		if user.visible == False:
			return

	slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
	
	sc = SlackClient(slack_token)
	sc.api_call(
		"chat.postMessage",
		link_names=1,
		channel=userAdress,
		text = msg,
	)	
	return

# Eine Slack-Nachricht wird testweise an den persoenlichen Slackbot-Channel eines Nutzers gesendet
def slack_TestMsgToUser(user):

	# Functional Users (bank, thief) do not need messages
	if user.visible == False:
		return

	slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')

	textToChannel = 'Hallo ' + str(user.first_name) + '!\n' + ':mailbox_with_mail: Das ist eine Testnachricht, die ich von deinem pers'+chr(246)+'nlichen Bereich im FfE-Kiosk gesendet habe. Da du das lesen kannst scheint die pers'+chr(246)+'nliche Benachrichtigung zu funktionieren!\n' + 'An dieser Stelle wirst du dann '+chr(252)+'ber deinen niedrigen (hohen) Kontostand und '+chr(252)+'ber besondere Kontobewegungen wie '+chr(220)+'berweisungen, Einzahlungen und Auszahlungen informiert.'

	userAdress = '@' + user.slackName

	sc = SlackClient(slack_token)

	sc.api_call(
		"chat.postMessage",
		channel=userAdress,
		text = textToChannel,
	)
	#print(sc.api_call("users.list",include_locale=True))
	#print(sc.api_call("channels.list"))
	#print(sc.api_call("conversations.info",channel="D7E1357DE"))
	

	return


# Der Nutzer wird persoenlich ueber nicht selbst durchgefuehrte Kontobewegungen informiert: Einzahlung / Auszahlung / Ueberweisung
def slack_PostTransactionInformation(info):

	if info['type'] == 'manTransaction':
		textToChannel = ':grey_exclamation::dollar: Es wurde eine '+chr(220)+'berweisung von ' + info['userFrom'].slackName + ' an ' + info['userTo'].slackName + ' in H'+chr(246)+'he von ' + str('%.2f' % info['betrag']) + ' '+chr(8364)+' get'+chr(228)+'tigt.'
	elif info['type'] == 'eingezahlt':
		textToChannel = ':grey_exclamation::dollar: Es wurden ' + str('%.2f' % info['betrag']) + ' '+chr(8364)+' auf dein Konto eingezahlt.'
	elif info['type'] == 'ausgezahlt':
		textToChannel = ':grey_exclamation::dollar: Es wurden ' + str('%.2f' % info['betrag']) + ' '+chr(8364)+' von deinem Konto ausgezahlt.'

	slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
	sc = SlackClient(slack_token)

	for user in [info['userFrom'], info['userTo']]:
		if user.visible == True:
			userAdress = '@' + user.slackName
			sc.api_call(
				"chat.postMessage",
				channel=userAdress,
				text = textToChannel,
			)

	return


def slack_PostWelcomeMessage(user):
	# Verwalter
	data = KioskUser.objects.filter(visible=True, rechte='Accountant')
	accountants = []
	for item in data:
		accountants.append(item.first_name + ' ' + item.last_name)
	accountants = ', '.join(accountants)

	textToChannel = ':tada: Willkommen im FfE-Kiosk! :tada:\n\n' + 'Du bist jetzt Teil einer Community, die als Gemeinschaft ein Kiosk betreibt und zu Supermarktpreisen Produkte verkauft. Als Nutzer des Kiosks musst du zun'+chr(228)+'chst etwas Guthaben auf dein Konto bei einem Verwalter ('+ accountants + ') einzahlen um Produkte einkaufen zu k'+chr(246)+'nnen.\n' + 'Im #kiosk-Channel hier auf Slack bekommst du alle wichtigen Informationen zum FfE-Kiosk. Vor allem sende ich dort Benachrichtigungen, wenn neue Produkte angeliefert wurden und wenn Produkte auf der Einkaufsliste stehen.\n' + 'Apropos Einkaufsliste: Wenn du dich aktiv am Betrieb des Kiosks beteiligen m'+chr(246)+'chtest, kannst du dich als `Eink'+chr(228)+'ufer` freischalten lassen. Dann kannst du nach Belieben Produkte von der Einkaufsliste f'+chr(252)+'r eine kleine Aufwandsentsch'+chr(228)+'digung f'+chr(252)+'r das Kiosk besorgen.'

	userAdress = '@' + user.slackName

	slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
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

	slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
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

		slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
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

	slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
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

