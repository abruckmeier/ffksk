from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from kiosk.models import Kiosk, Einkaufsliste
from paypal.paypal_mail import routine_with_messaging
from profil.models import KioskUser


class SyncPayPalTransactions(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'profil.perm_kauf'

    def get(self, request):
        """"""
        is_success, response_msg = routine_with_messaging()
        return JsonResponse(dict(
            is_success=is_success,
            response_msg=response_msg,
        ))


class PayPalEinzahlungInfoPage(View):
    def get(self, request):
        # Administrator
        data = KioskUser.objects.filter(visible=True, rechte='Admin')
        admins = []
        for item in data:
            admins.append(item.first_name + ' ' + item.last_name)
        admins = ', '.join(admins)

        # Verwalter
        data = KioskUser.objects.filter(visible=True, rechte='Accountant')
        accountants = []
        for item in data:
            accountants.append(item.first_name + ' ' + item.last_name)
        accountants = ', '.join(accountants)

        # Hole den Kioskinhalt
        kioskItems = Kiosk.getKioskContent()

        # Einkaufsliste abfragen
        einkaufsliste = Einkaufsliste.getEinkaufsliste()

        return render(request,
                      'paypal/paypal_einzahlung_page.html',
                      dict(admins=admins, accountants=accountants,
                           kioskItems=kioskItems,
                           einkaufsliste=einkaufsliste))
