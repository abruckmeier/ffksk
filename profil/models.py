from django.apps import apps
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from datetime import date
from django.contrib.auth.hashers import make_password


# Change the user manager for a case-insensitive login
class KioskUserManager(UserManager):
    def get_by_natural_key(self, username):
        case_insensitive_username_field = '{}__iexact'.format(self.model.USERNAME_FIELD)
        return self.get(**{case_insensitive_username_field: username})

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError("The given username must be set")
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(
            self.model._meta.app_label, self.model._meta.object_name
        )
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user


class KioskUser(AbstractUser):

    objects = KioskUserManager()
    REQUIRED_FIELDS = []

    email = None
    is_verified = models.BooleanField(default=False)
    
    slackName = models.CharField(max_length=40, unique=True, help_text='Slack ID oder Name hinter @, falls keine '
                                                                       'Leerzeichen oder Umlaute.')
    paypal_name = models.CharField(max_length=64, null=True, blank=True,
                                   help_text='Name, der bei PayPal nach außen zu sehen ist')
    aktivBis = models.DateField(default=date.today)
    instruierterKaeufer = models.BooleanField(default=False)
    visible = models.BooleanField(default=True, help_text='Bank, Dieb, usw. sollen nicht gesehn und nicht angewaehlt '
                                                          'werden duerfen, z.B. bei Einkauf-Annahme')  
    activity_end_msg = models.IntegerField(
        default=0, 
        help_text="0: Active, nothing sent. 1: Active, message sent that in 7 days, account will be blocked. "
                  "2: Inactive, invisible, Inactivity message sent. 3: Account is now unpersonalised, money is "
                  "donated to Kiosk"
    )

    dsgvo_accepted = models.BooleanField(default=False)
    is_functional_user = models.BooleanField(default=False, help_text='Set to true, if this is no real user, but System user')

    class Meta:
        default_manager_name = 'objects'
        permissions = (
            ("do_admin_tasks", "Kontaktnachrichten, Statistiken, Erweiterte Produktverwaltung, Nutzerverwaltung"),
            ("do_verwaltung_product_operations", "Besorgungen annehmen, Einkäufe rückbuchen, Inventur durchführen"),
            ("do_verwaltung_financial_operations", "Einzahlungen, Auszahlungen und Geldtransaktionen abwickeln"),
            ("do_verwaltung_product_management", "Produktlisten und -preise pflegen"),
            ("do_einkauf", "Produkte vormerken und besorgen"),
            ("perm_kauf", "Einkaufen im Kiosk"),
        )
