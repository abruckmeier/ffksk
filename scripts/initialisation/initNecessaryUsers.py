#!/usr/bin/env python

'''
	Create default users, necessary for running the kiosk
'''


import os
import sys
import django

if __name__ == '__main__':
	# Setup the Django environment of the Kiosk
	BASE = os.path.dirname(os.path.dirname(os.path.dirname((os.path.abspath(__file__)))))
	sys.path.append(BASE)
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ffeKiosk.settings")
	django.setup()


# Import the Modules for the tasks
from django.conf import settings

from profil import models as profil_models
from kiosk import models as kiosk_models


def initNecessaryUsers():

	users = [
		('Bank',),
		('Bargeld',),
		('Bargeld_Dieb',),
		('Bargeld_im_Tresor',),
		('Dieb',),
		('Gespendet',),
		('Spendenkonto',),
	]

	for u in users:

		_u = profil_models.KioskUser(
			username= u[0],
			first_name= u[0],
			last_name= u[0],
			email= u[0]+'@ffe.de',
			is_active= True,
			is_staff= False,
			is_superuser= False,
			slackName= u[0],
			is_verified = True,
			visible= False,
			aktivBis= '2999-12-31',
			rechte= 'User',
		)
		_u.save()

		k = kiosk_models.Kontostand(
			nutzer= _u,
			stand= 0,
		)
		k.save()

	print('Necessary Users created.')

	return


# Run the Script

if __name__ == '__main__':

    initNecessaryUsers()