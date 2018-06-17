from django.conf.urls import url, include
from django.views.generic import RedirectView
from django.contrib import admin


urlpatterns = [
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico')),
    url(r'^admin/', admin.site.urls),
    url(r'', include('kiosk.urls')),
    url(r'', include('profil.urls')),
]
