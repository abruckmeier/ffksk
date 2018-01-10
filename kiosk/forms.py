from django import forms
from django.core.validators import MinValueValidator


class EinkaufAnnahmeForm(forms.Form):
	userID = forms.IntegerField()
	produktName = forms.CharField(max_length=40)
	anzahlElemente = forms.IntegerField()
	anzahlAngeliefert = forms.IntegerField(validators=[MinValueValidator(1)])
	gesPreis = forms.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])


class TransaktionenForm(forms.Form):
	idFrom = forms.IntegerField()
	idTo = forms.IntegerField()
	betrag = forms.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
	kommentar = forms.CharField(max_length=500)

class EinzahlungenForm(forms.Form):
	CHOICES = [('Einzahlung','Einzahlung'),('Auszahlung','Auszahlung')]

	idUser = forms.IntegerField()
	typ = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect())
	betrag = forms.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
	kommentar = forms.CharField(max_length=500,required=False)

class RueckbuchungForm(forms.Form):
	userID = forms.IntegerField()
	productID = forms.IntegerField()
	anzahlElemente = forms.IntegerField()
	anzahlZurueck = forms.IntegerField()