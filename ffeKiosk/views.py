"""Views for cron tasks. They are only to be accessed as superuser or with the Vercel CRON_SECRET"""
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from paypal.paypal_mail import routine_with_messaging
from scripts.routines.dailyTasks import routine
from django.core.exceptions import PermissionDenied


class CronSecretRequiredMixin:
    """Verify that the current request has the correct CRON_SECRET within the header"""

    def dispatch(self, request, *args, **kwargs):
        if (not 'authorization' in request.headers
                or not request.headers['authorization'] == f'Bearer {settings.CRON_SECRET}'):
            return HttpResponse('Unauthorized', status=401)
        return super().dispatch(request, *args, **kwargs)


class SyncPayPalTransactions(CronSecretRequiredMixin, View):

    def get(self, request):
        """"""
        is_success, response_msg = routine_with_messaging()
        return JsonResponse(dict(
            is_success=is_success,
            response_msg=response_msg,
        ), status=200)


class DailyRoutine(CronSecretRequiredMixin, View):
    def get(self, request):
        """"""
        routine()
        return HttpResponse("Daily Routine Completed", status=200)
