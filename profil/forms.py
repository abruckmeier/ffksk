from django import forms
from django.utils.translation import ugettext_lazy as _
from  .models import KioskUser


class ConfirmPW(forms.Form):
	passwordcon = forms.CharField(label='Passwort best'+chr(228)+'tigen',widget=forms.PasswordInput)

class UserErstellenForm(forms.ModelForm):


	class Meta:
		model = KioskUser
		fields = ('username','first_name','last_name','email','aktivBis','positionFfE','password')
		widgets = {
			'password': forms.PasswordInput(), 
			'aktivBis': forms.DateInput(attrs={'class':'datepicker'}),
		}
		labels = {
			'username': _('Slack Name'),
			'aktivBis': _('Angestellt bis'),
			'positionFfE': _('Anstellung'),
		}
		help_texts = {
			'username': _('')
		}

