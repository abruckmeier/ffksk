from django.http import HttpResponse
import sys



def receiveSlackCommands(request):
	print('Test',file=sys.stderr)
	return HttpResponse(status=200)