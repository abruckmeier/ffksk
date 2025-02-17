from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

from profil.models import KioskUser
from .slackCommands import slack_sendMessageToResponseUrl, getCancelAttachementForResponse, getOkAttachementForResponse
from .models import Produktpalette, Kiosk, Kontostand

from .queries import readFromDatabase

import json

@csrf_exempt
def receiveSlackMessages(request):

	# Check if it is a POST-request
	if not request.method == "POST":
		return HttpResponse(status=406)
	message = request.POST

	message = message.get('payload')
	message = json.loads(message)

	# Verify the correct sender: Slack-FfE
	slack_verification_token = getattr(settings,'SLACK_VERIFICATION_TOKEN')
	if not message['token'] == slack_verification_token:
		return HttpResponse(status=403)

	## Process the message and distribute it to the targeted message
	# First, check if the message is the correct type.
	if message['type']=='interactive_message' and 'actions' in message.keys() and len(message['actions'])==1:
		# This is a response from the kiosk buy interaction
		if message['callback_id']=='kiosk_buy':
			# Start a function with threading
			process_kiosk_buy(message)

		# This is a response from the kiosk buy interaction with multiple choice of products
		elif message['callback_id']=='kiosk_buy_preselection':
			process_kiosk_buy_preselection(message)

		# This is a general Cancel request
		elif message['callback_id']=='cancel_action':
			process_cancel_action(message)

		# This is a general OK request
		elif message['callback_id']=='OK_action':
			process_ok_action(message)
			#Thread(target = process_ok_action, args=[message]).start()

		# The format is correct, but the response can not be handeled
		else:
			slack_sendMessageToResponseUrl(message.get('response_url'), '*Sorry!*'+chr(10)+'Ich kann diesen Dialog nicht weiterverarbeiten. Bitte kontaktiere den FfE-Kiosk-Administrator.', getCancelAttachementForResponse())	

	# The format is wrong. Send a Message to cancel the action
	else:
		slack_sendMessageToResponseUrl(message.get('response_url'), '*Sorry!*'+chr(10)+'Deine Antwort kann ich nicht verstehen. Bitte kontaktiere den FfE-Kiosk-Administrator.', getCancelAttachementForResponse())	

	return HttpResponse(status=200)


# Buy what has been selected or abort if cancel message sent.
def process_kiosk_buy(message):
	# Check for a cancel message
	if message['actions'][0]['name']=='Cancel':
		slack_sendMessageToResponseUrl(message.get('response_url'), 'Kauf gestoppt.')
		return


	# Check if the user has an account in the kiosk
	user = KioskUser.objects.filter(
		slackName__in=[ message['user']['id'], message['user']['name'], ],
		visible=True
	).first()
	if not user:
		slack_sendMessageToResponseUrl(message.get('response_url'), 'Ich kann deinen Slack-Account nicht mit deinem  FfE-Konto verbinden.'+chr(10)+'Wende dich bitte an einen Administrator.', getCancelAttachementForResponse())
		return

	# Check whether donate or not
	values = message['actions'][0]['value']
	if message['actions'][0]['name']=='ConfirmOneItemAndDonate':
		buyAndDonate = True
	elif message['actions'][0]['name']=='ConfirmOneItem':
		buyAndDonate = False
	else:
		slack_sendMessageToResponseUrl(message.get('response_url'), '*Uuups*'+chr(10)+'Da gab es einen Fehler bei der '+chr(220)+'bertragung deiner Bestellung.'+chr(10)+'Wende dich bitte an einen Administrator.', getCancelAttachementForResponse())
		return

	values = values.split('#')
	try:
		idItem = int(values[0])
		numBuy = int(values[1])
	except:
		slack_sendMessageToResponseUrl(message.get('response_url'), '*Uuups*'+chr(10)+'Da gab es einen Fehler bei der '+chr(220)+'bertragung deiner Bestellung.'+chr(10)+'Wende dich bitte an einen Administrator.', getCancelAttachementForResponse())
		return

	## Now buy the products
	# Get product name
	item = Produktpalette.objects.get(id=idItem)
	wannaBuyItem = item.produktName
	# Buy the item(s)
	for i in range(0,numBuy,1):
		retVal = Kiosk.buyItem(wannaBuyItem,user,gekauft_per='slack', buyAndDonate=buyAndDonate)
		if not retVal['success']:
			msg = '*Ooh!*'+chr(10)+'Es wurden '+str(i)+' von '+str(numBuy)+' Produkten verbucht.'+chr(10)+'Es sind vielleicht keine Produkte im Kiosk zum Verbuchen mehr vorhanden. Oder hast du nicht genug Guthaben auf deinem Konto? Oder ist dein Account ist abgelaufen.'
			slack_sendMessageToResponseUrl(message.get('response_url'), msg, getCancelAttachementForResponse())
			break

	# Send message with success
	if retVal['success']:
		konto = Kontostand.objects.get(nutzer = user)
		msg = 'Es wurde '+str(numBuy)+'x '+str(wannaBuyItem)+' erfolgreich verbucht.'+chr(10)+'Dein Kontostand ist nun '+ '%.2f' % (konto.stand/100) +' '+chr(8364)+'.'
		slack_sendMessageToResponseUrl(message.get('response_url'), msg, getOkAttachementForResponse())


	return


# There was a preselection with multiple choice, now, return the buy menu again with the chosen item.
def process_kiosk_buy_preselection(message):

	# Check for a cancel message
	if message['actions'][0]['name']=='Cancel':
		slack_sendMessageToResponseUrl(message.get('response_url'), 'Kauf gestoppt.')
		return

	if message['actions'][0]['name']=='product_list': 
		values = message['actions'][0]['selected_options'][0]['value'] 
	else:
		slack_sendMessageToResponseUrl(message.get('response_url'), '*Uuups*'+chr(10)+'Da gab es einen Fehler bei der '+chr(220)+'bertragung deiner Bestellung.'+chr(10)+'Wende dich bitte an einen Administrator.', getCancelAttachementForResponse())
		return

	values = values.split('#')
	try:
		idItem = int(values[0])
		numBuy = int(values[1])
	except:
		slack_sendMessageToResponseUrl(message.get('response_url'), '*Uuups*'+chr(10)+'Da gab es einen Fehler bei der '+chr(220)+'bertragung deiner Bestellung.'+chr(10)+'Wende dich bitte an einen Administrator.', getCancelAttachementForResponse())
		return

	itemToBuy = Produktpalette.objects.filter(id=idItem, imVerkauf=True)

	prices = readFromDatabase('getProductNameAndPriceById',[itemToBuy[0].id])
	txt = str(numBuy) + 'x ' + str(itemToBuy[0].produktName) + ' | ' + '%.2f' % (prices[0]['verkaufspreis']/100.0*numBuy) + ' ' + chr(8364) + ' ( +' + '%.2f' % (prices[0]['preisAufstockung']/100.0*numBuy) + ' ' + chr(8364) + ' Spende)'
	value = str(itemToBuy[0].id)+'#'+str(numBuy)

	callback_id = 'kiosk_buy'
	text = 'Deine Auswahl: _' + txt + '_'
	action = {'name': 'ConfirmOneItem', 'text': 'Nur Kaufen', 'type': 'button', 'style': 'default', 'value': value}
	action2 = {'name': 'ConfirmOneItemAndDonate', 'text': 'Kaufen & Spenden', 'type': 'button', 'style': 'primary', 'value': value}

	# Send the message
	attach = {
		'attachments': [
			{
				'text': text,
				'callback_id': callback_id,
				'attachment_type': 'default',
				'actions': [
					action,
					action2,
					{'name': 'Cancel', 'text': 'Abbrechen','type': 'button','value':'cancel','style':'danger'},
				]
			}
		]
	}
	slack_sendMessageToResponseUrl(message.get('response_url'),'*Einkaufen im Kiosk*',attach)

	# Weiter gehts bei slackMessages.receiveSlackCommands, wo die Antwort weiterverarbeitet wird.
	return

# x
def process_cancel_action(message):
	slack_sendMessageToResponseUrl(message.get('response_url'), 'Cancelled.')
	return

# x
def process_ok_action(message):
	slack_sendMessageToResponseUrl(message.get('response_url'), 'OK.')
	return
