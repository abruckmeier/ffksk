from django.urls import re_path, include
from django.views.generic import RedirectView
from django.contrib import admin
from django.contrib.auth import views
from ffeKiosk import views as ffeKioskViews

urlpatterns = [
    re_path(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico')),
    re_path(r'^admin/', admin.site.urls),
    re_path(r'^accounts/login/$', views.LoginView.as_view(), name='login'),
    re_path(r'^accounts/logout/$', views.LogoutView.as_view(next_page='/'), name='logout'),
    re_path(r'', include('kiosk.urls')),
    re_path(r'', include('profil.urls')),
    re_path(r'paypal/', include('paypal.urls')),
    re_path(r'cron/daily_routine/?$', ffeKioskViews.DailyRoutine.as_view()),
    re_path(r'cron/paypal_sync/?$', ffeKioskViews.SyncPayPalTransactions.as_view()),
]
