from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from kiosk.models import Kiosk, Einkaufsliste
from paypal.offline_token import gmail_login_redirect, gmail_auth_response
from paypal.paypal_mail import routine_with_messaging
from profil.models import KioskUser
import logging

logger = logging.getLogger(__name__)


class SyncPayPalTransactions(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'profil.perm_kauf'

    def get(self, request):
        """
        This view is used to synchronize PayPal transactions from the GMail inbox mails.
        One can add the argument `with_login_redirect` as true to redirect the user to the GMail login page
        if the user is not logged in to GMail.
        This is relevant only from the admin area.
        """
        # Check if the argument to redirect to the login page is set or not
        with_login_redirect: bool = request.GET.get(
            'with_login_redirect', 'false'
        ).lower() == 'true'

        is_success, response_msg, response = routine_with_messaging(with_login_redirect=with_login_redirect)

        if response:
            return response
        else:
            return JsonResponse(dict(
                is_success=is_success,
                response_msg=response_msg,
            ))


class PayPalEinzahlungInfoPage(View):
    def get(self, request):
        # Administrator
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_admin_tasks')
        admins = []
        for item in data:
            admins.append(item.first_name + ' ' + item.last_name)
        admins = ', '.join(admins)

        # Verwalter
        data = KioskUser.objects.filter(groups__permissions__codename__icontains='do_verwaltung')
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


class GmailAuthPage(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    This is the page where the user can authenticate with GMail.
    It redirects to the GMail login page.
    """

    permission_required = 'profil.do_verwaltung_financial_operations'

    def get(self, request):
        # Start the GMail authentication process
        return gmail_login_redirect(request)


class GmailAuthResponsePage(View):
    """
    This is the redirect page for the GMail authentication process after the user has logged in to GMail.
    """
    def get(self, request):
        gmail_auth_response(request)

        messages.success(request, 'login done')

        # Write this into the Token db table for further access
        return HttpResponseRedirect(reverse('paypal_sync'))
