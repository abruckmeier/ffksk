from django import forms
from django.core.validators import MinValueValidator
from . import models


class Kontakt_Nachricht_Form(forms.ModelForm):

    class Meta:
        model = models.Kontakt_Nachricht
        exclude = ('beantwortet',)
        widgets= {
            'betreff': forms.Textarea(attrs={'rows':1,})
        }



class TransaktionenForm(forms.Form):
    idFrom = forms.IntegerField(
        widget=forms.TextInput(attrs={'readonly':'true'})
    )
    idTo = forms.IntegerField(
        widget=forms.TextInput(attrs={'readonly':'true'})
    )
    betrag = forms.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
    kommentar = forms.CharField(widget=forms.Textarea, max_length=500)
    

class EinzahlungenForm(forms.Form):
    CHOICES = [('Einzahlung','Einzahlung'),('Auszahlung','Auszahlung')]

    idUser = forms.IntegerField(
        widget=forms.TextInput(attrs={'readonly':'true'})
    )
    typ = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect())
    betrag = forms.DecimalField(decimal_places=2, max_digits=10, validators=[MinValueValidator(0)])
    kommentar = forms.CharField(widget=forms.Textarea, max_length=500,required=False)


class RueckbuchungForm(forms.Form):
    kaeufer_id = forms.IntegerField(
        widget=forms.TextInput(attrs={'readonly':'true'})
    )
    produkt_id = forms.IntegerField(
        widget=forms.TextInput(attrs={'readonly':'true'})
    )
    produkt_name = forms.CharField(
        widget=forms.TextInput(attrs={'readonly':'true'})
    )
    anzahl_gekauft = forms.IntegerField(
        widget=forms.TextInput(attrs={'readonly':'true'})
    )
    anzahl_zurueck = forms.IntegerField(required=False, validators=[MinValueValidator(0)])

    # Clean "anzahl_zurueck" so that no values have to be filled in and they are set to default with zero
    def clean_anzahl_zurueck(self):
        data = self.cleaned_data['anzahl_zurueck']
        anzahl_gekauft = self.cleaned_data['anzahl_gekauft']
        if not data:
            data = 0

        if data > anzahl_gekauft:
            raise forms.ValidationError('Der Wert muss kleiner gleich '+str(anzahl_gekauft)+' sein.')

        return data
    
    

