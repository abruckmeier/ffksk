from django.urls import re_path
from paypal import views

urlpatterns = [
    re_path(r'sync/?$',
            views.SyncPayPalTransactions.as_view(),
            name='paypal_sync'),
]
