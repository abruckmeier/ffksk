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
    
    
class BeverageBookingForm(forms.Form):
    """This form is used to book beverages into the system on the view 'Einkauf Annahme'."""
    product_id = forms.IntegerField(
        widget=forms.TextInput(attrs={'readonly': 'true', 'hidden': 'true'})
    )
    user_id = forms.IntegerField(
        widget=forms.TextInput(attrs={'readonly': 'true', 'hidden': 'true'})
    )
    product_name = forms.CharField(
        label='Produkt',
        widget=forms.TextInput(attrs={'readonly': 'true'})
    )
    max_number_elements = forms.IntegerField(
        label='Anzahl zu kaufen',
        widget=forms.TextInput(attrs={'readonly': 'true'})
    )
    max_price = forms.DecimalField(
        label='Maximaler Einkaufspreis',
        decimal_places=2,
        widget=forms.TextInput(attrs={'readonly': 'true'}),
        localize=True,
    )
    delivered_elements = forms.IntegerField(
        label='Angelieferte Menge',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'x', 'class': 'form-control', 'style': 'width: 60px;'}),
    )
    price_paid = forms.DecimalField(
        localize=True,
        label='Bezahlter Preis in € (ohne Pfand)',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'x,yz €', 'class': 'form-control', 'style': 'width: 70px;'}),
    )
    pledge = forms.DecimalField(
        label='Pfand bezahlt in €',
        decimal_places=2,
        localize=True,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'x,yz €', 'class': 'form-control', 'style': 'width: 70px;'}),
    )
