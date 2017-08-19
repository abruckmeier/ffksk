from kiosk.queries import readFromDatabase
from kiosk.models import Einkaufsliste, Produktpalette, EinkaufslisteGroups
from django.db import transaction
from django.db.models import Max
import math


@transaction.atomic
def checkKioskContentAndFillUp():
	# Alle Produkte im Umlauf (Kiosk, persoenliche und offene Einkaufsliste) werden zusammengezaehlt und der maximalen Anzahl im Kiosk gegenuebergestellt. Wird die Bestellschwelle unterschritten, werden entsprechend Produkte auf die Einkaufsliste gesetzt.

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
				
				maxGroup = maxGroup + 1
	
	print("Bot has performed a Fill-Up.")

	return