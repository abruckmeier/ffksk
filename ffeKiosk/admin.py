from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from profil.models import KioskUser

admin.site.register(KioskUser, UserAdmin)
