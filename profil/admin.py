from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import KioskUser


# Register
admin.site.register(KioskUser, UserAdmin)