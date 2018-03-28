from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _
from  .models import KioskUser


class UserErstellenForm(UserCreationForm):

	def __init__(self, *args, **kwargs):
		super(UserErstellenForm, self).__init__(*args, **kwargs)
		self.fields['password1'].help_text = '<small>Das Passwort darf nich zu den oberen Eingaben '+chr(228)+'hnlich sein, mindestens 8 Zeichen lang sein und nicht nur aus Ziffern bestehen.</small>'
		self.fields['password2'].help_text = '<small>Das Passwort zur Best'+chr(228)+'tigung erneut eingeben.</small>'

	def is_valid(self):
		valid = super(UserErstellenForm,self).is_valid()
		ffeEmailDomain = self['email'].value().find('@ffe.de') != -1

		if valid and ffeEmailDomain: return True
		else: return False

	def clean_email(self):
		email = self.cleaned_data['email']
		if KioskUser.objects.filter(email=email).exists():
			raise ValidationError(_('E-Mail Adresse existiert bereits'), code='invalid')

		if (self['email'].value().find('@ffe.de') == -1):
			raise ValidationError(_('E-Mail Adresse muss die Domain "@ffe.de" besitzen'), code='invalid')

		return email

	class Meta:
		model = KioskUser
		fields = ('username','first_name','last_name','email','aktivBis','positionFfE','password1','password2')
		widgets = {
			'aktivBis': forms.DateInput(attrs={'class':'datepicker'}),
		}
		labels = {
			'aktivBis': _('Angestellt bis'),
			'positionFfE': _('Anstellung als'),
		}
		help_texts = {
			'username': _('<small>Dein Username im FfE-Kiosk muss deinem Slack-Namen entsprechen. (ohne @)</small>'),
			'email': _('<small>Die E-Mail-Adresse muss die @ffe.de-Domain besitzen.</small>'),
			'aktivBis': _('<small>Angabe des Datums deines Austritts an der FfE. Davor wirst du daran erinnert, dein Guthaben vom Konto auzahlen zu lassen, bevor dein Account gesperrt wird.</small>'),
		}


class AktivBisChangeForm(forms.ModelForm):
	
	class Meta:
		model = KioskUser
		fields = ('aktivBis',)
		widgets = {
			'aktivBis': forms.DateInput(attrs={'class':'datepicker'}),
		}
		help_texts = {
			'aktivBis': _('<small>Angabe des Datums deines Austritts an der FfE. Davor wirst du daran erinnert, dein Guthaben vom Konto auzahlen zu lassen, bevor dein Account gesperrt wird.</small>'),
		}