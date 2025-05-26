from django.db import models
from profil.models import KioskUser
from kiosk.models import GeldTransaktionen


class Mail(models.Model):
    """Downloaded and extracted mail from the Outlook server that was sent from PayPal"""

    message_id = models.CharField(unique=True, max_length=16, help_text='ID from Outlook')
    envelope_str = models.TextField(unique=True, help_text='Envelope string from Outlook')
    mail_ts = models.DateTimeField(help_text='Mail received (envelope)')
    data = models.TextField(help_text='Mail data')
    extraction_was_successful = models.BooleanField(
        default=False,
        help_text='Mail extraction was successful, if all values could be extracted'
    )
    assignment_was_successful = models.BooleanField(
        default=False,
        help_text='Mail assignment to a user was successful'
    )
    mail_is_processed = models.BooleanField(
        default=False,
        help_text='Mail has been read and necessary action was taken.'
    )
    user_str = models.CharField(max_length=64, blank=True, null=True, help_text='Extracted user')
    transaction_code = models.CharField(max_length=64, blank=True, null=True, help_text='Extracted transaction code')
    amount = models.IntegerField(help_text='Extracted amount sent', blank=True, null=True)
    notice = models.TextField(help_text='Extracted notice text', blank=True, null=True)

    user = models.ForeignKey(KioskUser, on_delete=models.SET_NULL, blank=True, null=True, related_name='assigned_user',
                             help_text='Assignment based on user_str and paypal_name')
    geld_transaktion = models.OneToOneField(GeldTransaktionen, on_delete=models.SET_NULL, blank=True, null=True,
                                            related_name='assigned_geld_transaktion',
                                            help_text='transaction of "Einzahlung" that has been created from this mail.')

    def __str__(self):
        return f'[{self.id}] {self.mail_ts}'

    class Meta:
        verbose_name = 'Mail'
        verbose_name_plural = 'Mails'
