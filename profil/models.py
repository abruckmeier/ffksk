from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date

# Create your models here.

class KioskUser(AbstractUser):
	positionsFfE = (('WiHi','Student'),
		('MA','Festangestellter'))
	permissions = (('User','Standardnutzer'),
		('Buyer','Eink'+chr(228)+'ufer'),('Accountant','Verwalter'),('Admin','Admin'))
	
	slackName = models.CharField(max_length=40)
	aktivBis = models.DateField(default=date.today)
	positionFfE = models.CharField(max_length=15,choices=positionsFfE,blank=True)
	instruierterKaeufer = models.BooleanField(default=False)
	rechte = models.CharField(max_length=15,default='User',choices=permissions)
	visible = models.BooleanField(default=True) # Bank, Dieb, usw. sollen nicht gesehn und nicht angewaehlt werden duerfen, z.B. bei Einkauf-Annahme

	class Meta:
		permissions = (
			("do_admin_tasks","Einpflegen von Usern, Geldtransaktionen, ..."),
			("do_verwaltung","Einarbeiten von Waren ins Kiosk"),
			("do_einkauf","Einkaeufe vormerken und einkaufen"),
			("perm_kauf","Kaufen im Kiosk")
		)