from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

from slackclient import SlackClient
from threading import Thread

from .models import Produktpalette

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
		Thread(target=process_kiosk, args=[message]).start()

	# No mapping for this command has been established, yet.
	else:
		try:
			slack_NotKnownCommandMsg(message.get('response_url'), message.get('command'))
		except:
			pass

	return HttpResponse(status=200)


# Process the command '/kiosk'
def process_kiosk(message):

	commandText = message.get('text')
	commandText = commandText.split(' ')

	# Find the command 'buy'
	command = [x for x in commandText if x in ['Kaufen','Kauf','kauf','kaufen','Buy','buy','Buying','buying']]
	if not command==[]:
		process_kiosk_buy(message, commandText, command[0])

	# No known kiosk-command found. Tell the user
	else:
		msg = 'Ich konnte Deinen `/kiosk`-Befehl leider nicht verstehen.'+chr(10)+'Ich ben'+chr(246)+'tige ein Stichwort wie beispielsweise `Kaufen`. '
		slack_sendMessageToResponseUrl(message.get('response_url'), msg)	

	return


# Process the command '/kiosk buy'
def process_kiosk_buy(message, commandText, command):
	# Remove command item from commandText
	commandText.remove(command)

	# Check, how many command items are left
	if len(commandText)==0:
		msg = 'Dein `/kiosk buy`-Befehl besitzt keine ein oder zwei zus'+chr(228)+'tzliche W'+chr(246)+'rter, welche mir mitteilen, *welches Produkt* du kaufen m'+chr(246)+'chtest und *wie viele* davon.'
		slack_sendMessageToResponseUrl(message.get('response_url'), msg)
	elif len(commandText)> 2:
		msg = 'Dein `/kiosk buy`-Befehl besitzt zu viele Argumente. Ich ben'+chr(246)+'tige ein oder zwei zus'+chr(228)+'tzliche W'+chr(246)+'rter, welche mir mitteilen, *welches Produkt* du kaufen m'+chr(246)+'chtest und *wie viele* davon.'
		slack_sendMessageToResponseUrl(message.get('response_url'), msg)

	# In case of one more command item, it is seen as the kiosk item
	if len(commandText)==1:
		rawItemToBuy = commandText[0]
	else:
		print('to Do + Anzahl')

	# Search for the item with a 100 percent accordance
	itemAccordance = None
	itemToBuy = Produktpalette.objects.filter(produktName=rawItemToBuy)
	if len(itemToBuy)==1: itemAccordance = 1

	# Search for the item with a likeness-query
	if itemAccordance is None:
		itemToBuy = Produktpalette.objects.filter(produktName__contains=rawItemToBuy)
		if len(itemToBuy)>=1: itemAccordance = 0.5

	# Search for the item with only parts of the string
	if itemAccordance is None:
		for i in range(len(rawItemToBuy)-1,2,-1):
			itemToBuy = Produktpalette.objects.filter(produktName__contains=rawItemToBuy[0:i])
			if len(itemToBuy)>=1: 
				itemAccordance = 0.25
				break

	# Send messages to respond
	if itemAccordance is None:
		# There is no accordance -> Give the complete products to select
		pass
	elif itemAccordance==1 or len(itemToBuy)==1:
		# One item has been found. Just ask to confirm
		pass
	elif itemAccordance<1:
		# There is a selection of possible products. Ask to select from them
		pass
	else:
		# Fehler darf nicht passieren -> Error-Message
		pass

	# Send the message
	adde = {
		'attachments': [
			{
				'text': 'Was moechtest du kaufen?',
				'callback_id': 'kiosk_buy',
				'attachment_type': 'default',
				'actions': [
					{'name': 'product_list','text': 'Auswahl ...', 'type': 'select',
						'options':[{'text':'Pizza | 2.80','value':1},{'text':'Eis | 1.40','value':2},]
					},
					{'name': 'Cancel', 'text': 'Abbrechen','type': 'button','value':'cancel','style':'danger'},
				]
			}
		]
	}
	slack_sendMessageToResponseUrl(message.get('response_url'),'*Einkaufen im Kiosk*',adde)

	# Weiter gehts bei slackMessages.receiveSlackCommands, wo die Antwort weiterverarbeitet wird.
	return


# Send back a ephemeral message to the response url
def slack_sendMessageToResponseUrl(url, text, furtherDict={}):
	data = {'text':text}
	data.update(furtherDict)
	r = requests.post(url,json=data)
	return


# Send back a message to the sender and tell, that the command does not exist.
def slack_NotKnownCommandMsg(response_url, command):
	msg = "Ich konnte leider mit folgendem Befehl nichts anfangen: '" + command + "'."
	slack_sendMessageToResponseUrl(response_url, msg)
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