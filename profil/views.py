from django.shortcuts import render, HttpResponseRedirect, reverse
from django.views import View
from django.contrib.auth.decorators import login_required
from kiosk.models import Kiosk, Einkaufsliste
from datetime import datetime
from django.contrib.auth.models import Group
from kiosk.models import Kontostand
from django.db import transaction
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import KioskUser
from .forms import AktivBisChangeForm, PersonalInfoChangeForm

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from profil.tokens import account_activation_token
from kiosk.bot import slack_PostWelcomeMessage


@login_required
def angestellt_bis_change(request):

    usr = KioskUser.objects.get(id=request.user.id)

    if request.method == "POST":

        aktivBisChangeForm = AktivBisChangeForm(request.POST)

        if aktivBisChangeForm.is_valid():
            date = aktivBisChangeForm.cleaned_data.get('aktivBis')
            usr.aktivBis = date
            
            # Remove the flag that (maybe) user has been warned about the end of active account
            usr.activity_end_msg = 0
            
            usr.save()

            request.session['angestellt_bis_change'] = datetime.strftime(date,'%d.%m.%Y')
            return HttpResponseRedirect(reverse('angestellt_bis_changed'))

        else:
            aktivBisChangeForm = AktivBisChangeForm(request.POST)

    else:
        aktivBisChangeForm = AktivBisChangeForm(initial={'aktivBis':usr.aktivBis,})
    
    # Hole den Kioskinhalt
    kioskItems = Kiosk.getKioskContent()

    # Einkaufsliste abfragen
    einkaufsliste = Einkaufsliste.getEinkaufsliste()

    return render(request, 'profilVerwaltung/angestellt_bis_change.html', 
        {'aktivBisChangeForm': aktivBisChangeForm, 'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,})


@login_required
def angestellt_bis_changed(request):

    # Hole den Kioskinhalt
    kioskItems = Kiosk.getKioskContent()

    # Einkaufsliste abfragen
    einkaufsliste = Einkaufsliste.getEinkaufsliste()

    if 'angestellt_bis_change' in request.session.keys():
        newDate = request.session['angestellt_bis_change']
        del request.session['angestellt_bis_change']
    else:
        return HttpResponseRedirect(reverse('home_page'))

    return render(request, 'profilVerwaltung/angestellt_bis_changed.html', 
        {'newDate': newDate, 'kioskItems': kioskItems, 'einkaufsliste': einkaufsliste,})


class PersonalInfoChange(View):
    """"""

    def get(self, request):
        usr = KioskUser.objects.get(id=request.user.id)
        personal_info_change_form = PersonalInfoChangeForm(instance=usr)
        return render(request,
                      'profilVerwaltung/personalInfoChange.html',
                      dict(form=personal_info_change_form,))

    def post(self, request):
        usr = KioskUser.objects.get(id=request.user.id)
        personal_info_change_form = PersonalInfoChangeForm(request.POST, instance=usr)
        if personal_info_change_form.is_valid():
            personal_info_change_form.save()
            return render(request,
                          'profilVerwaltung/personalInfoChange.html',
                          dict(form=personal_info_change_form,
                               msg='Änderungen gespeichert',
                               color='success'))
        else:
            return render(request,
                          'profilVerwaltung/personalInfoChange.html',
                          dict(form=personal_info_change_form,
                               msg='Fehler!',
                               color='danger'))


# After Login, check, if the user is accepted to access to the page by the site admin. Redirect, if allowed. If not, messages are provided here.
class registrationStatus(View):

    def get(self, request):

        if request.user.is_authenticated:
            
            if 'just_verified' in request.session.keys():
                just_verified = request.session['just_verified']
                del request.session['just_verified']
            else:
                just_verified = False
            
            if KioskUser.objects.filter(username=request.user.username,is_verified=True).exists() and not just_verified:
                
                return HttpResponseRedirect(reverse('home_page'))

            else:                
                # Get the Administrator
                data = KioskUser.objects.filter(visible=True, rechte='Admin')
                admins = []
                for item in data:
                    admins.append(item.first_name + ' ' + item.last_name)
                admins = ', '.join(admins)
                
                # Hole den Kioskinhalt
                kioskItems = Kiosk.getKioskContent()

                # Einkaufsliste abfragen
                einkaufsliste = Einkaufsliste.getEinkaufsliste()

                return render(request, 'registration/registrationStatus.html',{
                    'just_verified': just_verified,
                    'admins': admins,
                    'kioskItems': kioskItems, 
                    'einkaufsliste': einkaufsliste,
                })

        else:
            return HttpResponseRedirect(reverse('start_page'))


# Verify the slack name on registration. When the token, given in the verification message is correct, the corresponding flag is set to True. A Slack-message will be sent to give further information: Welcome message
class AccountActivate(LoginRequiredMixin, View):

    @transaction.atomic
    def get(self, request, uidb64, token):

        # Check, if the address is valid
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = KioskUser.objects.get(pk=uid)

        except(TypeError, ValueError, OverflowError, KioskUser.DoesNotExist):
            print('error')
            user = None

        # Set the flag to be email verified and save
        if user is not None and account_activation_token.check_token(user, token):
            user.is_verified = True
            user.save()

            g = Group.objects.get(name='Nutzer')
            g.user_set.add(user)
            h = Group.objects.get(name='Einkaufer')
            h.user_set.add(user)

            k = Kontostand(nutzer_id = user.id, stand=0)
            k.save()

            login(request, user)

            # Send an slack message with further information: Welcome
            slack_PostWelcomeMessage(user)            

            # Add the information: Just email verified -> For text display on the following website
            request.session['just_verified'] = True

            return HttpResponseRedirect(reverse('registrationStatus'))

        else:
            # Get the Administrator
            data = KioskUser.objects.filter(visible=True, rechte='Admin')
            admins = []
            for item in data:
                admins.append(item.first_name + ' ' + item.last_name)
            admins = ', '.join(admins)

            # Hole den Kioskinhalt
            kioskItems = Kiosk.getKioskContent()

            # Einkaufsliste abfragen
            einkaufsliste = Einkaufsliste.getEinkaufsliste()

            return render(request, 'registration/verification_failed.html',{
                    'admins': admins,
                    'kioskItems': kioskItems, 
                    'einkaufsliste': einkaufsliste,
                })