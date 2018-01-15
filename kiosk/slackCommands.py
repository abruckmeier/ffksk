from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

from slackclient import SlackClient

from .models import Produktpalette
from profil.models import KioskUser

from .queries import readFromDatabase

import requests


@csrf_exempt
def receiveSlackCommands(request):
	
	# Check if it is a POST-request
	if not request.method == "POST":
		return HttpResponse(status=406)
	message = request.POST

	# Verify the correct sender: Slack-FfE
	slack_verification_token = getattr(settings,'SLACK_VERIFICATION_TOKEN')
	if not message.get('token') == slack_verification_token:
		return HttpResponse(status=403)

	# Route the command to the correct function
	if message.get('command') == '/kiosk':
		# Start a function with threading
		#Thread(target=process_kiosk, args=[message]).start()
		process_kiosk(message)

	# No mapping for this command has been established, yet.
	else:
		try:
			slack_NotKnownCommandMsg(message.get('response_url'), message.get('command'))
		except:
			pass

	return HttpResponse(status=200)


# Process the command '/kiosk'
def process_kiosk(message):

	# Check if the user has an account in the kiosk
	if not KioskUser.objects.filter(slackName=message.get('user_name'), visible=True):
		attach = getCancelAttachementForResponse()
		slack_sendMessageToResponseUrl(message.get('response_url'), 'Ich kann deinen Slack-Account nicht mit deinem  FfE-Konto verbinden.'+chr(10)+'Wende dich bitte an einen Administrator.', attach)

		# Weiter gehts bei slackMessages.receiveSlackCommands, wo die Antwort weiterverarbeitet wird.
		return

	# Filter the the command from spaces
	commandText = message.get('text')
	commandText = commandText.split(' ')
	commandText = list(filter(lambda a: a not in ['',' '], commandText))

	# Find the command 'buy'
	command = [x for x in commandText if x in ['Kaufen','Kauf','kauf','kaufen','Buy','buy','Buying','buying']]
	if not command==[]:
		process_kiosk_buy(message, commandText, command[0])

	# No known kiosk-command found. Tell the user
	else:
		msg = 'Ich konnte Deinen `/kiosk`-Befehl leider nicht verstehen.'+chr(10)+'Ich ben'+chr(246)+'tige ein Stichwort wie beispielsweise `Kaufen`. '
		slack_sendMessageToResponseUrl(message.get('response_url'), msg, getCancelAttachementForResponse())	

	return


# Process the command '/kiosk buy'
def process_kiosk_buy(message, commandText, command):
	# Remove command item from commandText
	commandText.remove(command)

	# Check, how many command items are left
	if len(commandText)==0:
		msg = 'Dein `/kiosk buy`-Befehl besitzt keine ein oder zwei zus'+chr(228)+'tzliche W'+chr(246)+'rter, welche mir mitteilen, *welches Produkt* du kaufen m'+chr(246)+'chtest und *wie viele* davon.'
		slack_sendMessageToResponseUrl(message.get('response_url'), msg, getCancelAttachementForResponse())
		return

	elif len(commandText)> 2:
		msg = 'Dein `/kiosk buy`-Befehl besitzt zu viele Argumente. Ich ben'+chr(246)+'tige ein oder zwei zus'+chr(228)+'tzliche W'+chr(246)+'rter, welche mir mitteilen, *welches Produkt* du kaufen m'+chr(246)+'chtest und *wie viele* davon.'
		slack_sendMessageToResponseUrl(message.get('response_url'), msg, getCancelAttachementForResponse())
		return

	# In case of one more command item, it is seen as the kiosk item
	if len(commandText)==1:
		rawItemToBuy = commandText[0]
		numBuy = 1
	else:
		# In case of two more command items, check for the one that is a number. The other is the kios item
		numBuy = None
		
		try: numBuy = int(commandText[0])
		except: pass
		if not numBuy is None:
			rawItemToBuy = commandText[1]

		else:
			try: numBuy = int(commandText[1])
			except: pass
			if not numBuy is None:
				rawItemToBuy = commandText[0]
			else:
				msg = 'Dein `/kiosk buy`-Befehl ben'+chr(246)+'tigt als Argument entweder ein Produkt, das du kaufen m'+chr(246)+'chtest oder zwei Argumente, wobei eines das Produkt ist, das du kaufen m'+chr(246)+'chtest und das zweite Argument die Anzahl dieser Produkte als numerisches Zeichen.'
				slack_sendMessageToResponseUrl(message.get('response_url'), msg)
				return	

	# Search for the item with a 100 percent accordance
	itemAccordance = None
	itemToBuy = Produktpalette.objects.filter(produktName=rawItemToBuy, imVerkauf=True)
	if len(itemToBuy)==1: itemAccordance = 1

	# Search for the item with a likeness-query
	if itemAccordance is None:
		itemToBuy = Produktpalette.objects.filter(produktName__icontains=rawItemToBuy, imVerkauf=True)
		if len(itemToBuy)>=1: itemAccordance = 0.5

	# Search for the item with only parts of the string
	if itemAccordance is None:
		for i in range(len(rawItemToBuy)-1,2,-1):
			itemToBuy = Produktpalette.objects.filter(produktName__icontains=rawItemToBuy[0:i], imVerkauf=True)
			if len(itemToBuy)>=1: 
				itemAccordance = 0.25
				break

	# If no match was made, give back the complete list
	if itemAccordance is None:
		itemToBuy = Produktpalette.objects.filter(imVerkauf=True).order_by('produktName')

	# Create list of products plus price for selection
	txts = []
	for v in itemToBuy:
		prices = readFromDatabase('getProductNameAndPriceById',[v.id])
		txt = str(numBuy) + 'x ' + str(v.produktName) + ' | ' + '%.2f' % (prices[0]['verkaufspreis']/100.0*numBuy) + ' ' + chr(8364)
		txts.append({'text': txt, 'value': str(v.id)+'#'+str(numBuy)})

	# Prepare the selection and the button
	actionSelection = {'name': 'product_list','text': 'Auswahl ...', 'type': 'select', 'options': txts}
	actionButton = {'name': 'ConfirmOneItem', 'text': txts[0]['text'],'type': 'button','value': txts[0]['value']}

	# Send messages to respond
	if itemAccordance is None:
		# There is no accordance -> Give the complete products to select
		text = 'Was m'+chr(246)+'chtest Du kaufen? Ich konnte dich nicht verstehen und gebe dir die komplette Produktpalette zur Auswahl.'
		action = actionSelection

	elif itemAccordance==1 or len(itemToBuy)==1:
		# One item has been found. Just ask to confirm
		text = 'Du m'+chr(246)+'chtest folgendes kaufen?'
		action = actionButton

	elif itemAccordance<1:
		# There is a selection of possible products. Ask to select from them
		text = 'Was genau m'+chr(246)+'chtest Du kaufen? Deine Eingabe hat folgende Ergebnisse geliefert:'
		action = actionSelection

	else:
		# Fehler darf nicht passieren -> Error-Message
		text = 'Uuups. Da ist etwas schief gelaufen. Wende dich bitte an den Administrator.'
		action = None


	# Send the message
	attach = {
		'attachments': [
			{
				'text': text,
				'callback_id': 'kiosk_buy',
				'attachment_type': 'default',
				'actions': [
					action,
					{'name': 'Cancel', 'text': 'Abbrechen','type': 'button','value':'cancel','style':'danger'},
				]
			}
		]
	}
	slack_sendMessageToResponseUrl(message.get('response_url'),'*Einkaufen im Kiosk*',attach)

	# Weiter gehts bei slackMessages.receiveSlackCommands, wo die Antwort weiterverarbeitet wird.
	return

def getCancelAttachementForResponse():
	attach = {
		'attachments': [
			{
				'text': '',
				'callback_id': 'cancel_action',
				'attachment_type': 'default',
				'actions': [
					{'name': 'Cancel', 'text': 'Abbrechen','type': 'button','value':'cancel','style':'danger'},
				]
			}
		]
	}
	return attach

def getOkAttachementForResponse():
	attach = {
		'attachments': [
			{
				'text': '',
				'callback_id': 'OK_action',
				'attachment_type': 'default',
				'actions': [
					{'name': 'OK', 'text': 'OK','type': 'button','value':'OK','style':'good'},
				]
			}
		]
	}
	return attach

# Send back a ephemeral message to the response url
def slack_sendMessageToResponseUrl(url, text, furtherDict={}):
	data = {'text':text}
	data.update(furtherDict)
	r = requests.post(url,json=data)
	return


# Send back a message to the sender and tell, that the command does not exist.
def slack_NotKnownCommandMsg(response_url, command):
	msg = "Ich konnte leider mit folgendem Befehl nichts anfangen: '" + command + "'."
	slack_sendMessageToResponseUrl(response_url, msg, getCancelAttachementForResponse())
	return

def old_slack_NotKnownCommandMsg(channelToRespond, userToRespond, command):
	
	slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
	msg = "Ich konnte leider mit folgendem Befehl nichts anfangen: '" + command + "'."

	slack_SendEphemeralMsgWithFallback(channelToRespond, userToRespond, msg)

	return


# Try to send a Ephemeral message to the place of the sending if possible. If not, then send it to the person itself.
def old_slack_SendEphemeralMsgWithFallback(channelToSend, userToSend, msg):
	
	slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
	sc = SlackClient(slack_token)

	success = sc.api_call(
		"chat.postEphemeral",
		channel=channelToSend,
		text = msg,
		user = userToSend
	)

	if not success['ok']:
		sc.api_call(
			"chat.postMessage",
			channel=userToSend,
			text = msg
		)

	return