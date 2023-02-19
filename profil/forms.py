from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.tokens import default_token_generator
from kiosk.bot import slack_SendMsg
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string

from django.db.models import Q

from  .models import KioskUser
from . import models



# Slack Reset Form
# This form is used in the template to enter the slack name to send a message to the user with a reset link to generate a new password. This form finds the user and sends the url.
class SlackResetForm(forms.Form):
    
    slackName = forms.CharField(label="Slack-Name oder E-Mail-Adresse", max_length=40)


    def send_slackMessage(self, subject_template_name, email_template_name, context, from_email, to_user, html_email_template_name=None):
        """
        Send a Slack message
        """
        subject = render_to_string(subject_template_name, context)
        # subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = render_to_string(email_template_name, context)

        msg = '*'+str(subject)+'*\n\n\r' + str(body)
        try:
            slack_SendMsg(msg,to_user)
        except:
            pass


    def get_users(self, slackName):
        """Given an slackName, return matching user(s) who should receive a reset.
        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        active_users = models.KioskUser._default_manager.filter(
            Q(slackName__iexact=slackName, is_active=True)
            |
            Q(email__iexact=slackName, is_active=True)
        )
        return (u for u in active_users if u.has_usable_password())

    def save(self, domain_override=None, subject_template_name='registration/password_reset_subject.html', email_template_name='registration/password_reset_message.html', use_https=False, token_generator=default_token_generator, from_email=None, request=None, html_email_template_name=None, extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        slackName = self.cleaned_data["slackName"]
        for user in self.get_users(slackName):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'slackName': slackName,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }
            print('send')
            self.send_slackMessage(
                subject_template_name, email_template_name, context, from_email,
                user, html_email_template_name=html_email_template_name,
            )



class UserErstellenForm(UserCreationForm):

	def __init__(self, *args, **kwargs):
		super(UserErstellenForm, self).__init__(*args, **kwargs)
		self.fields['password1'].help_text = '<small>Das Passwort darf nich zu den oberen Eingaben '+chr(228)+'hnlich sein, mindestens 8 Zeichen lang sein und nicht nur aus Ziffern bestehen.</small>'
		self.fields['password2'].help_text = '<small>Das Passwort zur Best'+chr(228)+'tigung erneut eingeben.</small>'

	def is_valid(self):
		valid = super(UserErstellenForm,self).is_valid()
		ffeEmailDomain = self['email'].value().find('@ffe.de') != -1

		dsgvo_accepted = self['dsgvo_accepted'].value()

		if valid and ffeEmailDomain and dsgvo_accepted: return True
		else: return False

	def clean_email(self):
		email = self.cleaned_data['email']
		if KioskUser.objects.filter(email=email).exists():
			raise ValidationError(_('E-Mail Adresse existiert bereits'), code='invalid')

		if (self['email'].value().find('@ffe.de') == -1):
			raise ValidationError(_('E-Mail Adresse muss die Domain "@ffe.de" besitzen'), code='invalid')

		return email

	def clean_slackName(self):
		slackName = self.cleaned_data['slackName']
		if KioskUser.objects.filter(slackName=slackName).exists():
			raise ValidationError(_('Slack-Name existiert bereits'), code='invalid')

		return slackName

	def clean_dsgvo_accepted(self):
		dsgvo_accepted = self.cleaned_data['dsgvo_accepted']
		if not dsgvo_accepted is True:
			raise ValidationError(_('Du musst die Regelungen im Kiosk und die Datenverwendung akzeptieren.'), code='invalid')

		return dsgvo_accepted

	class Meta:
		model = KioskUser
		fields = ('username', 'slackName','first_name','last_name','email','aktivBis','password1','password2', 'dsgvo_accepted')
		widgets = {
			'aktivBis': forms.DateInput(attrs={'class':'datepicker'}),
		}
		labels = {
            'slackName': _('Slack-Name'),
			'aktivBis': _('Angestellt bis'),
            'dsgvo_accepted': _('Akzeptieren der Regelungen im Kiosk und der Datenverwendung'),
		}
		help_texts = {
			'username': _('<small>W'+chr(228)+'hle einen Nutzernamen, mit dem du dich einloggen m'+chr(246)+'chtest.</small>'),
            'slackName': _('<small>Gib deinen Namen auf Slack an (ohne @). Falls du, ein Leerzeichen im Slack-Namen hast, dann musst du unter "Profile & Account" deine "Member ID" angeben (U....).</small>'),
			'email': _('<small>Die E-Mail-Adresse muss die @ffe.de-Domain besitzen.</small>'),
			'aktivBis': _('<small>Angabe des Datums deines Austritts an der FfE. Davor wirst du daran erinnert, dein Guthaben vom Konto auzahlen zu lassen, bevor dein Account gesperrt wird.</small>'),
            'dsgvo_accepted': _('Mit dem Setzen des Hakens akzeptierst du die <a class="bold" href="/menu/regelwerk/">g'+chr(252)+'ltigen Regeln im Kiosk</a> und die <a class="bold" href="/datenschutzerklaerung/">Hinweise zur Datenverwendung</a>.')
		}


class AktivBisChangeForm(forms.ModelForm):
	
	class Meta:
		model = KioskUser
		fields = ('aktivBis',)
		widgets = {
			'aktivBis': forms.DateInput(attrs={'class':'datepicker'}),
		}
		help_texts = {
			#'aktivBis': _('<small>Angabe des Datums deines Austritts an der FfE. Davor wirst du daran erinnert, dein Guthaben vom Konto auzahlen zu lassen, bevor dein Account gesperrt wird.</small>'),
		}