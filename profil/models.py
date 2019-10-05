from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import AbstractUser, UserManager
from datetime import date

from datetime import date

# Change the user manager for a case-insensitive login
class KioskUserManager(UserManager):
	def get_by_natural_key(self, username):
		case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
		return self.get(**{case_insensitive_username_field: username})



class KioskUser(AbstractUser):

	objects = KioskUserManager()

	email = models.EmailField(_('E-Mail-Adresse'), unique=True)
	is_verified = models.BooleanField(default=False)

	permissions = (('User','Standardnutzer'),
		('Buyer','Eink'+chr(228)+'ufer'),('Accountant','Verwalter'),('Admin','Admin'))
	
	slackName = models.CharField(max_length=40, unique=True)
	aktivBis = models.DateField(default=date(1999,12,31))
	instruierterKaeufer = models.BooleanField(default=False)
	rechte = models.CharField(max_length=15,default='User',choices=permissions)
	visible = models.BooleanField(default=True) # Bank, Dieb, usw. sollen nicht gesehn und nicht angewaehlt werden duerfen, z.B. bei Einkauf-Annahme
	activity_end_msg = models.IntegerField(default=0) # 0: Active, nothing sent. 1: Active, message sent that in 7 days, account will be blocked. 2: Inactive, invisible, Inactivity message sent. 3: Account is now unpersonalised, money is donated to Kiosk

	dsgvo_accepted = models.BooleanField(default=False)

	class Meta:
		permissions = (
			("do_admin_tasks","Einpflegen von Usern, Geldtransaktionen, ..."),
			("do_verwaltung","Einarbeiten von Waren ins Kiosk"),
			("do_einkauf","Eink"+chr(228)+"ufe vormerken und einkaufen"),
			("perm_kauf","Kaufen im Kiosk")
		)