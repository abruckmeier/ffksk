from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

from threading import Thread

import requests
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

	print(message['user'])

	return HttpResponse(status=200)