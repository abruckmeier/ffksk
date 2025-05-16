#!/usr/bin/env python

'''
    Initialise the Groups and Permissions after the models have been initialised in the database.
    Permissions are initialised with the models itself.

    Do the assignment of groups here, not in the Admin-Surface!
'''


import os
import sys
import django

if __name__ == '__main__':
    # Setup the Django environment of the Kiosk
    BASE = os.path.dirname(os.path.dirname(os.path.dirname((os.path.abspath(__file__)))))
    sys.path.append(BASE)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ffeKiosk.settings")
    django.setup()


# Import the Modules for the tasks
from django.conf import settings
from django.contrib.auth.models import Group, Permission


def GetOrCreateGroup(name):
    try:
        grp = Group.objects.get(name=name)
    except:
        grp = Group(name=name)
        grp.save()
    return grp


# User functions here (or from import)
def InitGroupsAndPermissions():

    # -----------
    # Admin
    #    But not superuser
    # -----------
    admin = GetOrCreateGroup(name='Admin')

    p = Permission.objects.none()

    p |= Permission.objects.filter(
        content_type__app_label='kiosk', 
        content_type__model='einkaufsliste', 
        codename__iregex=r'(add|change|delete)_einkaufsliste',
    )
    p |= Permission.objects.filter(
        content_type__app_label='kiosk', 
        content_type__model='einkaufslistegroups', 
        codename__iregex=r'(add|change|delete)_einkaufslistegroups',
    )
    p |= Permission.objects.filter(
        content_type__app_label='kiosk', 
        content_type__model='kioskkapazitaet', 
        codename__iregex=r'(add|change)_kioskkapazitaet',
    )
    p |= Permission.objects.filter(
        content_type__app_label='kiosk', 
        content_type__model='kontakt_nachricht', 
        codename='change_kontakt_nachricht',
    )
    p |= Permission.objects.filter(
        content_type__app_label='kiosk', 
        content_type__model='produktpalette', 
        codename__iregex=r'(add|change)_produktpalette',
    )
    p |= Permission.objects.filter(
        content_type__app_label='kiosk', 
        content_type__model='produktverkaufspreise', 
        codename='add_produktverkaufspreise',
    )
    p |= Permission.objects.filter(
        content_type__app_label='profil', 
        content_type__model='kioskuser', 
        codename__iregex=r'(add|change)_kioskuser',
    )
    p |= Permission.objects.filter(
        content_type__app_label='profil', 
        content_type__model='kioskuser', 
        codename='do_admin_tasks',
    )
    p |= Permission.objects.filter(
        content_type__app_label='paypal',
        content_type__model='mail',
        codename='change_kioskuser',
    )
    for pp in p:
        admin.permissions.add(pp)


    # -----------
    # Verwalter
    # -----------
    verwalter = GetOrCreateGroup(name='Verwalter')

    p = Permission.objects.none()
    p |= Permission.objects.filter(
        content_type__app_label='profil', 
        content_type__model='kioskuser', 
        codename='do_verwaltung',
    )
    for pp in p:
        verwalter.permissions.add(pp)


    # -----------
    # Einkäufer
    # -----------
    einkaufer = GetOrCreateGroup(name='Einkaufer')

    p = Permission.objects.none()
    p |= Permission.objects.filter(
        content_type__app_label='profil', 
        content_type__model='kioskuser', 
        codename='do_einkauf',
    )
    for pp in p:
        einkaufer.permissions.add(pp)


    # -----------
    # Nutzer
    # -----------
    nutzer = GetOrCreateGroup(name='Nutzer')

    p = Permission.objects.none()
    p |= Permission.objects.filter(
        content_type__app_label='profil', 
        content_type__model='kioskuser', 
        codename='perm_kauf',
    )
    for pp in p:
        nutzer.permissions.add(pp)

    print('Groups created and permissions assigned.')
    return


# Run the Script

if __name__ == '__main__':

    # Permissions are initialised with the models itself.

    # Now, Init the groups and concatenate the permissions
    InitGroupsAndPermissions()
    