from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from paypal.paypal_mail import routine_with_messaging


class SyncPayPalTransactions(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'profil.do_verwaltung'

    def get(self, request):
        """"""
        is_success, response_msg = routine_with_messaging()
        return JsonResponse(dict(
            is_success=is_success,
            response_msg=response_msg,
        ))
